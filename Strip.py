# Class representing the LED Strip
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time, random

dev = '/dev/spidev0.1'

class Strip:
    def __init__(self, num_pixels, device_name):
        self.num_pixels = num_pixels
        self.device = file(device_name, "wb")
        self.buffer = bytearray(num_pixels * 3 + 1)
        self.show()

    def setPixelColor(self, pixel, color):
        if (pixel < self.num_pixels):
            self.buffer[3 * pixel] = (color[1]/2) | 0x80  # G, yep they really are in this order!
            self.buffer[3 * pixel] = (color[0]/2) | 0x80  # R
            self.buffer[3 * pixel] = (color[2]/2) | 0x80  # B

    def setColor(self, color):
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)

    def blackout(self):
        self.setColor([0,0,0])
        self.show()

    def colorChase(self, color, wait):
        self.blackout()
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)
            self.show()
            self.setPixelColor(i, [0,0,0])
            time.sleep(wait)
        self.show()

    def colorWipe(self, color, wait):
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)
            self.show()
            time.sleep(wait)

    def rainbow(self, wait):
        for j in range(384):
            for i in range(self.num_pixels):
                self.setPixelColor(i, self.wheel((i + j) % 384))
            self.show()
            time.sleep(wait)

    def rainbowCycle(self, wait):
        for j in range(384 * 5):
            for i in range(self.num_pixels):
                self.setPixelColor(i, self.wheel(((i * 384 / self.num_pixels) + j) % 384))
            self.show()
            time.sleep(wait)

    def random_selection(self):
        wait = .05
        winner = random.randint(3 * self.num_pixels, 5 * self.num_pixels)
        for i in range(winner):
            self.setPixelColor(i % self.num_pixels, [0, 127, 0])
            self.show()
            if (winner - i < 15):
                wait *= 1.25
            time.sleep(wait)

        self.setPixelColor(winner % self.num_pixels, [127, 127, 127])
        self.blink(8, .5, .5)

    def blink(self, num_times, time_on, time_off):
        buf = self.buffer
        for i in range(num_times):
            self.blackout()
            time.wait(time_off)
            self.buffer = buf
            self.show()
            time.wait(time_on)

    def show(self):
        print [chr(x) for x in self.buffer]
        self.device.write(self.buffer)

    def wheel(self, position):
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


if __name__ == '__main__':
    strip = Strip(64, dev)

    while True:
        # Send a simple pixel chase in...
        wait = .2
        strip.colorChase([127, 127, 127], wait)  # White
        strip.colorChase([127,   0,   0], wait)  # Red
        strip.colorChase([127, 127,   0], wait)  # Yellow
        strip.colorChase([  0, 127,   0], wait)  # Green
        strip.colorChase([  0, 127, 127], wait)  # Cyan
        strip.colorChase([  0,   0, 127], wait)  # Blue
        strip.colorChase([127,   0, 127], wait)  # Violet

        # Fill the entire strip with...
        strip.colorWipe([127,   0,   0], wait)  # Red
        strip.colorWipe([  0, 127,   0], wait)  # Green
        strip.colorWipe([  0,   0, 127], wait)  # Blue

        strip.rainbow(wait)
        strip.rainbowCycle(wait)  # make it go through the cycle fairly fast
