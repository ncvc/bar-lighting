import time
import random
from Colors import *

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
TOGGLEXMASMODE = 'togglexmasmode'
BLINKONCE      = 'blinkonce'
BLINKTWICE     = 'blinktwice'

class Animation(object):
    def __init__(self, strip, wait):
        self.strip = strip 
        self.wait = wait
        self.returns_control = False
        self.name = "Default"

    def setup(self):
        self.strip.blackout()

    def step(self):
        #Override this method in subclasses
        return True

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

class StaticColor(Animation):
    def __init__(self, color, strip, wait=.5):
        super(StaticColor, self).__init__(strip, wait=.5)
        self.color = color

    def step(self):
        self.strip.setColor(self.color.rgb())
        self.strip.show()
        time.sleep(self.wait)
        return True

    def __repr__(self):
        return str(self.color)
       
class Rainbow(Animation):
    def __init__(self, strip, wait=0.0001):
        super(Rainbow, self).__init__(strip, wait)
        self.j = 0
        self.name = "Rainbow"
        
    def step(self):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, self.wheel((i + self.j) % 384))
            self.strip.show()
        self.j = (self.j + 5)% 384
        time.sleep(self.wait)
        return True

class RainbowCycle(Animation):
    def __init__(self, strip, wait=0.0001):
        super(RainbowCycle, self).__init__(strip, wait)
        self.j = 0
        self.name = "Rainbow Cycle"

    def step(self):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, self.wheel(((i * 384 / self.strip.num_pixels) + self.j) % 384))
            self.strip.show()
        self.j = (self.j + 5)  % (384 * 5)
        time.sleep(self.wait)
        return True
 
class ColorWipe(Animation):
    def __init__(self, strip, wait=.01):
        super(ColorWipe, self).__init__(strip, wait)
        self.i = 0
        self.color = BLACKOUT
        self.name = "Color Wipe"

    def setup(self):
        super(ColorWipe, self).setup()
        self.i = 0

    def step(self):
        if self.i == 0:
            rand = self.color
            while rand == self.color:
                rand = random.choice(COLORS) 
            self.color = rand
        self.strip.setPixelColor(self.i, self.color.rgb())
        self.strip.show()
        self.i = (self.i + 1) % self.strip.num_pixels
        time.sleep(self.wait)
        return self.i == 0

class Blink(Animation):
    def __init__(self, num_blinks, strip, wait=.25):
        super(Blink, self).__init__(strip, wait)
        self.i = 0
        self.num_blinks = num_blinks
        self.returns_control = True
        self.name = "Blink"

    def setup(self):
        super(Blink, self).setup()
        self.i = 0

    def step(self):
        if self.i <= self.num_blinks * 2:
            if self.i % 2 == 0:
                self.strip.setColor([0,0,0])
            else:
                self.strip.setColor(WHITE.rgb())

        self.strip.show()
        self.i += 1
        time.sleep(self.wait)
        return self.i > self.num_blinks * 2

class RandomChoice(Animation):
    def __init__(self, strip, wait=.02):
        super(RandomChoice, self).__init__(strip, wait)
        self.i = 0
        self.returns_control = True
        self.winner = None
        self.color = [0,0,0]
        self.num_blinks = 7
        self.toggle = True
        self.blink_counter = 0
        self.name = "Random Choice"

    def setup(self):
        super(RandomChoice, self).setup()
        self.i = 0
        self.blink_counter = 0
        self.winner = random.randint(6 * self.strip.num_pixels, 9 * self.strip.num_pixels)
        self.wait = .02
        self.color = random.choice(COLORS).rgb()

    def step(self):
        if self.winner - self.i < 20 and self.wait < self.winner:
            self.wait = self.wait * 1.2
        if self.i < self.winner:
            self.strip.setPixelColor(self.i - 1, [0,0,0])
            self.strip.setPixelColor(self.i, self.color)
            self.i += 1
        else:
            self.wait = 0.3
            self.strip.setPixelColor(self.i - 1, [0,0,0])
            if self.toggle:
                self.toggle = False
                self.strip.setPixelColor(self.i , [0,0,0])
            else:
                self.toggle = True
                self.strip.setPixelColor(self.i, [127, 127, 127])
            self.blink_counter += 1

        self.strip.show()
        time.sleep(self.wait)
        return self.blink_counter > 2 * self.num_blinks

