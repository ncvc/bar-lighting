import pyaudio
import scipy
import struct
import scipy.fftpack

from Tkinter import *
import threading
import wave
import sys

import numpy

from matplotlib.pylab import * 

#ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
bufferSize = 2 ** 11
#bufferSize=2**8

# ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
sampleRate = 48100
#sampleRate=64000

p = pyaudio.PyAudio()
chunks = []
ffts = []

CHUNK = bufferSize

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

wf = wave.open(sys.argv[1], 'rb')


def stream():
	global chunks, inStream, bufferSize
	while True:
		data = wf.readframes(CHUNK)
		chunks.append(data)
		inStream.write(data)
		# chunks.append(inStream.read(bufferSize))

	inStream.stop_stream()
	inStream.close()

	p.terminate()


def record():
	global w, inStream, p, bufferSize
	# inStream = p.open(format=pyaudio.paInt16, channels=1,
	# 		  rate=sampleRate, input=True, frames_per_buffer=bufferSize)

	inStream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
	                channels=wf.getnchannels(),
	                rate=wf.getframerate(),
	                output=True,
	                frames_per_buffer=CHUNK)
	threading.Thread(target=stream).start()


def downSample(fftx, ffty, degree=10):
	x, y = [], []
	for i in range(len(ffty) / degree - 1):
		x.append(fftx[i * degree + degree / 2])
		y.append(sum(ffty[i * degree:(i + 1) * degree]) / degree)
	return [x, y]


def smoothWindow(fftx, ffty, degree=10):
	lx, ly = fftx[degree:-degree], []
	for i in range(degree, len(ffty) - degree):
		ly.append(sum(ffty[i - degree:i + degree]))
	return [lx, ly]


def smoothMemory(ffty, degree=3):
	global ffts
	ffts = ffts + [ffty]
	if len(ffts) <= degree:
		return ffty
	ffts = ffts[1:]
	return scipy.average(scipy.array(ffts), 0)


def detrend(fftx, ffty, degree=10):
	lx, ly = fftx[degree:-degree], []
	for i in range(degree, len(ffty) - degree):
		ly.append(ffty[i] - sum(ffty[i -
			  degree:i + degree]) / (degree * 2))
		#ly.append(fft[i]-(ffty[i-degree]+ffty[i+degree])/2)
	return [lx, ly]


def graph():
	global chunks, bufferSize, fftx, ffty, w
	if len(chunks) > 0:
		data = chunks.pop(0)
		data = scipy.array(struct.unpack("%dB" % (bufferSize * 2), data[:len(data)/2]))
		#print "RECORDED",len(data)/float(sampleRate),"SEC"
		ffty = scipy.fftpack.fft(data)
		fftx = scipy.fftpack.rfftfreq(bufferSize * 2, 1.0 / sampleRate)
		fftx = fftx[0:len(fftx) / 4]
		ffty = abs(ffty[0:len(ffty) / 2]) / 1000
		ffty1 = ffty[:len(ffty) / 2]
		ffty2 = ffty[len(ffty) / 2::] + 2
		ffty2 = ffty2[::-1]
		ffty = ffty1 + ffty2
		ffty = scipy.log(ffty) - 2
		#fftx,ffty=downSample(fftx,ffty,5)
		#fftx,ffty=detrend(fftx,ffty,30)
		#fftx,ffty=smoothWindow(fftx,ffty,10)
		ffty = smoothMemory(ffty, 3)
		#fftx,ffty=detrend(fftx,ffty,10)
		#w.add(wckgraph.Axes(extent=(0, -1, fftx[-1], 3)))
		# w.add(wckgraph.Axes(extent=(0, -1, 6000, 3)))
		# ffty = numpy.fft.fft(data[:len(data)/2], 32)
		# print len(ffty), len(data[:len(data)/2])
		# print ffty[:5]
		# print ffty[-5:]
		w = np.fft.fft(data)
		freqs = np.fft.fftfreq(len(w))
		idx=np.argmax(np.abs(w)**2)
		freq=freqs[idx]
		freq_in_hertz=abs(freq*sampleRate)
		print(freq_in_hertz)
		# line.set_ydata(ffty)           # update the plot data
		# draw()                      # redraw the canvas
		# w.add(wckgraph.LineGraph([fftx, ffty]))
	if len(chunks) > 20:
		print "falling behind...", len(chunks)


def go(x=None):
	global w, fftx, ffty
	print "STARTING!"
	threading.Thread(target=record).start()
	while True:
		graph()


# ion()                           # interaction mode needs to be turned off

# x = range(0,32)         # we'll create an x-axis from 0 to 2 pi
# y = range(0,3)         # we'll create an x-axis from 0 to 2 pi
# line, = plot(x,x)               # this is our initial plot, and does nothing
# line.axes.set_xlim(0,32)        # set the range for our plot
# line.axes.set_ylim(-1,3)        # set the range for our plot

go()
