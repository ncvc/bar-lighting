import random
import Colors
from ModCounter import ModCounter
import Queue
import numpy as np
import pyaudio


# Base Animation class that implements nearly all necessary functionality.
# Implementing classes must override the step() method
class BaseAnimation(object):
    def __init__(self, wait):
        self.wait = wait
        self.name = "Default"
        self.returns_control = False

    def setup(self, strip):
        strip.blackout()

    def step(self, strip):
        raise NotImplementedError("Do not use BaseAnimation directly, use a subclass with step() implemented")

    def wheel(self, position, random=False):
        r = 0
        g = 0
        b = 0

        if position / 128 == 0:
            r = 127 - position % 128
            g = position % 128
            b = 0
        elif position / 128 == 1:
            g = 127 - position % 128
            b = position % 128
            r = 0
        elif position / 128 == 2:
            b = 127 - position % 128
            r = position % 128
            g = 0

        return [r, g, b]

    def __repr__(self):
        return self.name


class StaticColor(BaseAnimation):
    def __init__(self, color, wait=.5):
        super(StaticColor, self).__init__(wait=wait)
        self.color = color

    def step(self, strip):
        strip.setColor(self.color.rgb())
        return True

    def __repr__(self):
        return str(self.color)


class Rainbow(BaseAnimation):
    def __init__(self, wait=0.01):
        super(Rainbow, self).__init__(wait)
        self.counter = ModCounter(384)
        self.name = "Rainbow"

    def step(self, strip):
        for i in range(len(strip)):
            strip.setPixelColor(i, self.wheel((i + self.counter.i) % 384))
        self.counter += 5
        return True

class Droplets(BaseAnimation):
    def __init__(self, wait=0.05):
        super(Droplets, self).__init__(wait)
        self.buffer = None
        self.add_rate = .3
        self.fade_rate = 5
        self.name = 'Droplets'

    def step(self, strip):
        if self.buffer == None:
            self.buffer = [[0,0,0]] * len(strip)

        self.buffer = [[max(0, r - self.fade_rate), max(0, g - self.fade_rate), max(0, b - self.fade_rate)] for r, g, b in self.buffer]

        if random.random() < self.add_rate:
            self.buffer[random.randint(0, len(strip) - 1)] = random.choice(Colors.COLORS).rgb()

        for i in range(len(strip)):
            strip.setPixelColor(i, self.buffer[i])
        return True

class RainbowCycle(BaseAnimation):
    def __init__(self, wait=0.01):
        super(RainbowCycle, self).__init__(wait)
        self.counter = ModCounter(384 * 5)
        self.name = "Rainbow Cycle"

    def step(self, strip):
        for i in range(len(strip)):
            strip.setPixelColor(i, self.wheel(((i * 384 / len(strip)) + self.counter.i) % 384))
        self.counter += 1
        return True


class ColorWipe(BaseAnimation):
    def __init__(self, wait=.01):
        super(ColorWipe, self).__init__(wait)
        self.color = Colors.BLACKOUT
        self.name = "Color Wipe"

    def setup(self, strip):
        super(ColorWipe, self).setup(strip)
        self.counter = ModCounter(len(strip))
        self.counter.reset()

    def step(self, strip):
        if self.counter == 0:
            rand = self.color
            while rand == self.color:
                rand = random.choice(Colors.COLORS) 
            self.color = rand
        strip.setPixelColor(self.counter.i, self.color.rgb())
        self.counter += 1
        return True


class Blink(BaseAnimation):
    def __init__(self, num_blinks, wait=.25):
        super(Blink, self).__init__(wait)
        self.i = 0
        self.num_blinks = num_blinks
        self.returns_control = True
        self.name = "Blink"

    def setup(self, strip):
        super(Blink, self).setup(strip)
        self.i = 0

    def step(self, strip):
        if self.i <= self.num_blinks * 2:
            if self.i % 2 == 0:
                strip.setColor([0,0,0])
            else:
                strip.setColor(Colors.WHITE.rgb())

        self.i += 1
        return self.i > self.num_blinks * 2

class Additive(BaseAnimation):
    def __init__(self, fade=True, wait=0.01):
        super(Additive, self).__init__(wait)
        self.color = None
        self.buffer = None
        self.step_size = .2
        self.fade = fade
        self.name = 'Additive Fade' if fade else 'Additive Cycle'
        self.tolerance = .85

    def setup(self, strip):
        super(Additive, self).setup(strip)
        temp = self.color
        while temp == self.color:
            temp = random.choice(Colors.COLORS)
        self.color = temp
        self.buffer = [[0,0,0]] * len(strip)
        self.color_changed_flag_buffer = [False] * len(strip)

    def step(self, strip):
        i = random.randint(0, len(strip) - 1)
        r, g, b = self.buffer[i]
        cr, cg, cb = self.color.rgb()

        if not self.fade and self.color_changed_flag_buffer[i]:
            self.color_changed_flag_buffer[i] = False
            r = 0
            g = 0
            b = 0

        if cr != 0:
            r = min(127, r + self.step_size * cr)
        else:
            r = max(0, r - self.step_size * 127)

        if cg != 0:
            g = min(127, g + self.step_size * cg)
        else:
            g = max(0, g - self.step_size * 127)

        if cb != 0:
            b = min(127, b + self.step_size * cb)
        else:
            b = max(0, b - self.step_size * 127)

        self.buffer[i] = [r, g, b]

        count = 0
        
        for i in range(len(strip)):
            strip.setPixelColor(i, self.buffer[i])
            if self.buffer[i] == self.color.rgb():
                count += 1

        if float(count) / len(strip) > self.tolerance:
            temp = self.color
            while temp == self.color:
                temp = random.choice(Colors.COLORS)
            self.color = temp
            self.color_changed_flag_buffer = [True for i in range(len(self.color_changed_flag_buffer))]

        return True

class RandomChoice(BaseAnimation):
    def __init__(self, wait=.02):
        super(RandomChoice, self).__init__(wait)
        self.i = 0
        self.counter = None
        self.returns_control = True
        self.winner = None
        self.color = [0,0,0]
        self.num_blinks = 7
        self.toggle = True
        self.blink_counter = 0
        self.name = "Random Choice"

    def setup(self, strip):
        super(RandomChoice, self).setup(strip)
        self.i = 0
        self.counter = ModCounter(len(strip))
        self.blink_counter = 0
        self.winner = random.randint(1 * len(strip), 2 * len(strip))
        self.wait = .02
        self.color = random.choice(Colors.COLORS).rgb()

    def step(self, strip):
        if self.winner - self.i < 20 and self.wait < self.winner:
            self.wait = self.wait * 1.2
        if self.i < self.winner:
            strip.setPixelColor(self.counter.i - 1, [0,0,0])
            strip.setPixelColor(self.counter.i, self.color)
            self.i += 1
            self.counter += 1
        else:
            self.wait = 0.3
            strip.setPixelColor(self.counter.i - 1, [0,0,0])
            if self.toggle:
                self.toggle = False
                strip.setPixelColor(self.counter.i , [0,0,0])
            else:
                self.toggle = True
                strip.setPixelColor(self.counter.i, [127, 127, 127])
            self.blink_counter += 1

        return self.blink_counter > 2 * self.num_blinks


# Abstract class to react to mic input
class MusicReactive(BaseAnimation):
    def __init__(self):
        super(MusicReactive, self).__init__(0.1)
        self.CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        self.RATE = 44100
        QUEUE_SECONDS = 1

        self.returns_control = True
        self.name = "MusicReactive"
        self.queue = [0] * self.RATE * QUEUE_SECONDS

        #self.p = pyaudio.PyAudio()

        #self.stream = self.p.open(format=FORMAT,
        #                     channels=CHANNELS,
        #                     rate=self.RATE,
        #                     input=True,
        #                     frames_per_buffer=self.CHUNK)

    def getFreqs(self):
        while self.stream.get_read_available() >= self.CHUNK:
            for frame in self.stream.read(self.CHUNK):
                self.queue.pop()
                self.queue.append(frame)

        w = np.fft.fft(self.queue)
        freqs = np.fft.fftfreq(len(w))
        # print freqs
        print(freqs.min(),freqs.max())
        # (-0.5, 0.499975)

        # Find the peak in the coefficients
        idx=np.argmax(np.abs(w)**2)
        freq=freqs[idx] 
        freq_in_hertz=abs(freq * self.RATE)
        print(freq_in_hertz)
        for e in xrange(len(w)):
            freq=freqs[e]
            freq_in_hertz=abs(freq * self.RATE)
            print e, np.abs(w[e])**2, freq_in_hertz

        return False

    # Returns the level of wub, normalized to the range [0,1]
    def getWubLevel(self):
        self.getFreqs()

    # Not sure if necessary
    def end(self):
        self.stream.stop_stream()
        self.stream.close()

        self.p.terminate()


class MusicSlider(MusicReactive):
    def __init__(self):
        super(MusicSlider, self).__init__()
        self.name = 'MusicSlider'
        self.color = Colors.RED

    def setup(self, strip):
        super(MusicSlider, self).setup(strip)
        strip.blackout()
        self.slider = 0.0

    def step(self, strip):
        scaledWubLevel = self.getWubLevel() * strip.num_pixels
        if self.slider >= scaledWubLevel:
            self.slider = scaledWubLevel
        else:
            self.slider -= 0.1

        self.setColor([0,0,0])
        for i in xrange(self.slider):
            self.strip.setPixelColor(int(i), self.color)

        self.strip.setPixelColor(int(self.slider), self.color * (self.slider - int(self.slider)))

        return True


class MusicCenterSlider(MusicReactive):
    def __init__(self):
        super(MusicCenterSlider, self).__init__()
        self.name = 'MusicCenterSlider'
        self.color = Colors.RED


    def setup(self, strip):
        super(MusicCenterSlider, self).setup(strip)
        strip.blackout()
        self.slider = 0.0

    def step(self, strip):
        scaledWubLevel = self.getWubLevel() * strip.num_pixels
        if self.slider >= scaledWubLevel:
            self.slider = scaledWubLevel
        else:
            self.slider -= 0.1

        self.setColor([0,0,0])
        brightness = self.slider - int(self.slider)
        for i in xrange(self.slider):
            self.strip.setPixelColor(int(i), self.color * brightness)

        self.strip.setPixelColor(int(self.slider), self.color * (self.slider - int(self.slider)))

        return True


# String constants
COLORWIPE      = 'colorwipe'
BLACKOUT       = 'blackout'
COLOR          = 'color'
STATICRED      = 'staticred'
STATICBLUE     = 'staticblue'
STATICGREEN    = 'staticgreen'
STATICMAGENTA  = 'staticmagenta'
STATICCYAN     = 'staticcyan'
STATICWHITE    = 'staticwhite'
BLACKOUT       = 'blackout'
RANDOM         = 'randomchoice'
RAINBOW        = 'rainbow'
RAINBOWCYCLE   = 'rainbowcycle'
BLINKONCE      = 'blinkonce'
BLINKTWICE     = 'blinktwice'
MUSIC          = 'music'
DROPLETS       = 'droplets'
ADDITIVEFADE   = 'additivefade'
ADDITIVECYCLE  = 'additivecycle'

DYNAMIC_ANIMATIONS = [COLORWIPE,
                      RAINBOW,
                      RAINBOWCYCLE,
                      ADDITIVEFADE,
                      ADDITIVECYCLE,
                      DROPLETS,
                      STATICRED,
                      STATICGREEN,
                      STATICBLUE,
                      STATICMAGENTA,
                      STATICCYAN,
                      STATICWHITE]

ANIMATIONS    = {COLORWIPE    : ColorWipe(),
                 RAINBOW      : Rainbow(),
                 RAINBOWCYCLE : RainbowCycle(),
                 STATICRED    : StaticColor(Colors.RED),
                 STATICGREEN  : StaticColor(Colors.GREEN),
                 STATICBLUE   : StaticColor(Colors.BLUE),
                 STATICMAGENTA: StaticColor(Colors.MAGENTA),
                 STATICCYAN   : StaticColor(Colors.CYAN),
                 STATICWHITE  : StaticColor(Colors.WHITE),
                 BLACKOUT     : StaticColor(Colors.BLACKOUT),
                 RANDOM       : RandomChoice(),
                 BLINKONCE    : Blink(1),
                 BLINKTWICE   : Blink(2),
                 COLOR        : StaticColor(Colors.CUSTOM),
                 MUSIC        : MusicReactive(),
                 DROPLETS     : Droplets(),
                 ADDITIVEFADE : Additive(True),
                 ADDITIVECYCLE: Additive(False)}
