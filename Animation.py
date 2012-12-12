
import time

class Animation(object):
    def __init__(self, strip, wait):
        self.strip = strip 
        self.wait = wait

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

class Rainbow(Animation):
    def __init__(self, strip, wait=0.01):
        super(Rainbow, self).__init__(strip, wait)
        self.j = 0

    def step(self):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, self.wheel((i + self.j) % 384))
            self.strip.show()
        self.j = (self.j + 5) % 384
        time.sleep(self.wait)
        return True

class RainbowCycle(Animation):
    def __init__(self, strip, wait=0.01):
        super(RainbowCycle, self).__init__(strip, wait)
        self.j = 0;

    def step(self):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, self.wheel(((i * 384 / self.strip.num_pixels) + self.j) % 384))
            self.strip.show()
        self.j = (self.j + 5) % (384 * 5)
        time.sleep(self.wait)
        return True

class ColorChase(Animation):
    def __init__(self, strip, wait=0.01):
        super(ColorChase, self).__init__(strip, wait)
        self.i = 0

    def step(self):
        self.strip.setPixelColor(self.i - 1, [0,0,0])
        self.strip.setPixelColor(self.i, [127, 0, 0])
        self.strip.show()
        self.i = (self.i + 1 ) % self.strip.num_pixels
        time.sleep(self.wait)
        return self.i % self.strip.num_pixels == 0

class Blackout(Animation):
    def __init__(self, strip, wait=1):
        super(Blackout, self).__init__(strip, wait)
        
    def step(self):
        self.strip.setColor([0,0,0])
        self.strip.show()
        time.sleep(self.wait)
        return True

class ColorWipe(Animation):
    def __init__(self, strip, wait=.01):
        super(ColorWipe, self).__init__(strip, wait)
        self.i = 0
        self.r = 127
        self.g = 0
        self.b = 0

    def step(self):
        if self.i == self.strip.num_pixels - 1:
            self.strip.setColor([0,0,0])
        else:
            tmp = self.r
            self.r = self.g
            self.g = self.b
            self.b = tmp
            self.strip.setPixelColor(self.i, [self.r, self.g, self.b])
        self.strip.show()
        self.i = (self.i + 1) % self.strip.num_pixels
        time.sleep(self.wait)
        return True