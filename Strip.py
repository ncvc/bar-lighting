# Class representing the LED Strip
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time, random

DEV_PATH = '/dev/spidev0.0'
MAX_BRIGHTNESS = 127

class Strip:
    def __init__(self, num_pixels, device_name=DEV_PATH):
        self.num_pixels = num_pixels
        self.xmasMode = False
        self.device = file(device_name, "wb")
        self.buffer = bytearray(num_pixels * 3)
        self.show()

    def setPixelColor(self, pixel, color):
        if (pixel >= self.num_pixels):
            return

        color = [max(0, min(i, MAX_BRIGHTNESS)) for i in color]

        if self.xmasMode:
            i=0
            minBrightness = 50
            if i == 0:
                color[2] = 0
            elif i==1:
                distR = (color[0] - MAX_BRIGHTNESS)**2 + color[1]**2 + color[2]**2
                distG = color[0]**2 + (color[1] - MAX_BRIGHTNESS)**2 + color[2]**2
                if distR < distG:
                    color = [MAX_BRIGHTNESS, 0, 0]
                else:
                    color = [0, MAX_BRIGHTNESS, 0]
            elif i==2:
                distR = (color[0] - MAX_BRIGHTNESS)**2 + color[1]**2 + color[2]**2
                distG = color[0]**2 + (color[1] - MAX_BRIGHTNESS)**2 + color[2]**2
                if distR < distG:
                    color[1] = color[2] = 0
                else:
                    color[0] = color[2] = 0
                color = [max(minBrightness, min(i, MAX_BRIGHTNESS)) for i in color]

        self.buffer[3 * pixel] = (color[1]/2) | 0x80  # G, yep they really are in this order!
        self.buffer[3 * pixel + 1] = (color[0]/2) | 0x80  # R
        self.buffer[3 * pixel + 2] = (color[2]/2) | 0x80  # B

    def setColor(self, color):
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)

    def blackout(self):
        self.setColor([0,0,0])
        self.show()

    def show(self):
        for x in range(self.num_pixels):
            self.device.write(self.buffer[x*3:x*3+3])
            self.device.flush()
        self.device.write(bytearray(b'\x00\x00\x00'))  # zero fill the last to prevent stray colors at the end
        self.device.write(bytearray(b'\x00'))
        self.device.flush()
        time.sleep(0.001)

    def enableXmasMode(self, enable=True):
        self.xmasMode = enable


class Animations:
    def __init__(self, strip):
        self.strip = strip

    def doABigGoddamnLoop(self):
        while True:
            # Send a simple pixel chase in...
            wait = 0
            # self.colorChase([127, 127, 127], wait)  # White
            # self.colorChase([127,   0,   0], wait)  # Red
            # self.colorChase([127, 127,   0], wait)  # Yellow
            # self.colorChase([  0, 127,   0], wait)  # Green
            # self.colorChase([  0, 127, 127], wait)  # Cyan
            # self.colorChase([  0,   0, 127], wait)  # Blue
            # self.colorChase([127,   0, 127], wait)  # Violet

            # # Fill the entire strip with...
            # self.colorWipe([127,   0,   0], wait)  # Red
            # self.colorWipe([  0, 127,   0], wait)  # Green
            # self.colorWipe([  0,   0, 127], wait)  # Blue

            # self.rainbow(wait)
            self.rainbowCycle(wait)  # make it go through the cycle fairly fast

    def colorChase(self, color, wait=0.01):
        self.strip.blackout()
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            self.strip.setPixelColor(i, [0,0,0])
            time.sleep(wait)
        self.strip.show()

    def colorWipe(self, color, wait=0.01):
        for i in range(self.strip.num_pixels):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait)

    def rainbow(self, wait=0.01):
        for j in range(384):
            for i in range(self.strip.num_pixels):
                self.strip.setPixelColor(i, self.wheel((i + j) % 384))
            self.strip.show()
            time.sleep(wait)

    def rainbowCycle(self, wait=0.01):
        for j in range(384 * 5):
            for i in range(self.strip.num_pixels):
                self.strip.setPixelColor(i, self.wheel(((i * 384 / self.strip.num_pixels) + j) % 384))
            self.strip.show()
            time.sleep(wait)

    def random_selection(self):
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

    def blink(self, num_times, time_on, time_off):
        buf = self.buffer
        for i in range(num_times):
            self.strip.blackout()
            time.wait(time_off)
            self.buffer = buf
            self.strip.show()
            time.wait(time_on)

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
    strip = Strip(32)
    strip.blackout()
    anim = Animations(strip)
    anim.doABigGoddamnLoop()
