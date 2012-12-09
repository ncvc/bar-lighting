import time

class Animation(object):
    def __init__(self, strip):
        self.strip = strip 
        
    def step(self):
        #Override this method in subclasses
        pass

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
        super(Rainbow, self).__init__(strip)
        self.j = 0;
        self.wait = wait;

    def step(self):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, self.wheel((i + self.j) % 384))
            self.strip.show()
        self.j = (self.j + 1) % 384
        time.sleep(self.wait)

class ColorChase(Animation):
    def __init__(self, strip, wait=0.01):
        super(ColorChase, self).__init__(strip)
        self.wait = wait;
        self.i = 0

    def step(self):
        self.strip.setPixelColor(self.i - 1, [0,0,0])
        self.strip.setPixelColor(self.i, [127, 0, 0])
        self.strip.show()
        self.i = (self.i + 1 ) % self.strip.num_pixels
        time.sleep(self.wait)

class Blackout(Animation):
    def __init__(self, strip, wait=1):
        super(Blackout, self).__init__(strip)
        self.wait = wait
        
    def step(self):
        self.strip.setColor([0,0,0])
        self.strip.show()
        time.sleep(self.wait)

class ColorWipe(Animation):
    def __init__(self, strip, wait=.01):
        super(ColorWipe, self).__init__(strip)
        self.wait = wait
        self.i = 0
        self.r = 127
        self.g = 0
        self.b = 0

    def step(self):
        if self.i == self.strip.num_pixels - 1:
            self.strip.setColor([0,0,0])
            tmp = self.r
            self.g = self.r
            self.r = tmp
        else:
            self.strip.setPixelColor(self.i, [self.r, self.g, self.b])
        self.strip.show()
        self.i = (self.i + 1) % self.strip.num_pixels
        time.sleep(self.wait)

"""
    def colorChase(self, color, wait=0.01):
        self.strip.blackout()
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            self.strip.setPixelColor(i, [0,0,0])
            time.sleep(wait)
        self.strip.show()

    def colorWipe(self, color, wait=0.01, random=False):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait)

    def rainbow(self, wait=0.01):
        self.animation = self.animations["rainbow"]

    def rainbowCycle(self, wait=0.01, random=False):
        for j in range(384 * 5):
            for i in range(self.strip.num_pixels):
                self.strip.setPixelColor(i, self.wheel(((i * 384 / self.strip.num_pixels) + j) % 384))
            self.strip.show()
            time.sleep(wait)

    def random_selection(self, random=False):
        wait = .05
        winner = random.randint(3 * self.strip.num_pixels, 5 * self.strip.num_pixels)
        for i in range(winner):
            self.strip.setPixelColor(i % self.strip.num_pixels, [0, 127, 0])
            self.strip.show()
            if (winner - i < 15):
                wait *= 1.25
            time.sleep(wait)

        self.strip.setPixelColor(winner % self.strip.num_pixels, [127, 127, 127])
        self.blink(8, .5, .5)

    def blink(self, num_times, time_on, time_off, random=False):
        buf = self.buffer
        for i in range(num_times):
            self.strip.blackout()
            time.wait(time_off)
            self.buffer = buf
            self.strip.show()
            time.wait(time_on)
"""
