import numpy as np
import math

r = np.sin([(2*x * np.pi / 180.) * (x * np.pi / 180.) for x in xrange(360)])
# a = np.fft.fft(r)
# b = np.fft.fftfreq(32, d=1.0/360)
# print r
# print a
# print b

w = np.fft.fft(r)
freqs = np.fft.fftfreq(len(w))
# print freqs
print(freqs.min(),freqs.max())
# (-0.5, 0.499975)

# Find the peak in the coefficients
idx=np.argmax(np.abs(w)**2)
freq=freqs[idx] 
freq_in_hertz=abs(freq*360)
print(freq_in_hertz)
for e in xrange(len(w)):
	freq=freqs[e]
	freq_in_hertz=abs(freq*360)
	print e, np.abs(w[e])**2, freq_in_hertz
