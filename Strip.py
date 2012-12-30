# Class representing the LED Strip and a test class
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time
from Tkinter import Canvas, Tk, mainloop


DEV_PATH = '/dev/spidev0.0'
MAX_BRIGHTNESS = 127
DEFAULT_LED_SIZE = 40


# Base strip class that implements nearly all necessary functionality.
# Implementing classes must override the show() method
class BaseStrip(object):
    def __init__(self, num_pixels):
        self.num_pixels = num_pixels
        self.xmasMode   = False
        self.buffer     = [[0,0,0] for i in xrange(num_pixels)]

    def setPixelColor(self, pixel, color):
        if pixel >= self.num_pixels:
            raise Exception("Invalid pixel index {0}".format(pixel))

        color = [max(0, min(i, MAX_BRIGHTNESS)) for i in color]

        if self.xmasMode:
            i=1
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

        self.buffer[pixel] = color

    def setColor(self, color):
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)

    def blackout(self):
        self.setColor([0,0,0])
        self.show()

    def show(self):
        raise NotImplementedError("Do not use BaseStrip directly - try Strip or TestingStrip")

    def enableXmasMode(self, enable=True):
        self.xmasMode = enable


# Class for a real light strip
class Strip(BaseStrip):
    def __init__(self, num_pixels, device_name=DEV_PATH):
        super(Strip, self).__init__(num_pixels)
        self.device = file(device_name, "wb")
        self.show()

    def show(self):
        for x in range(self.num_pixels):
            self.device.write(self.buffer[x][1] | 0x80)
            self.device.write(self.buffer[x][0] | 0x80)
            self.device.write(self.buffer[x][2] | 0x80)
            self.device.flush()
        self.device.write(bytearray(b'\x00\x00\x00'))  # zero fill the last to prevent stray colors at the end
        self.device.write(bytearray(b'\x00'))
        self.device.flush()
        time.sleep(0.0000000001)


# Class for an on-screen testing strip
class TestingStrip(BaseStrip):
    def __init__(self, num_pixels, led_size=DEFAULT_LED_SIZE):
        super(TestingStrip, self).__init__(num_pixels)
        height = led_size + 20
        width = led_size * num_pixels + 20
        self.canvas = Canvas(Tk(), width=width, height=height)
        self.canvas.pack()
        self.leds = [self.canvas.create_rectangle(10+i*led_size, 10, 10+(i+1)*led_size, led_size+10) for i in xrange(num_pixels)]
        self.canvas.update()

    def show(self):
        for i in xrange(self.num_pixels):
            color = '#%02x%02x%02x' % tuple([(255 * c) / MAX_BRIGHTNESS for c in self.buffer[i]])
            self.canvas.itemconfigure(self.leds[i], fill=color)
        self.canvas.update()


if __name__ == '__main__':
    strip = TestingStrip(32)
    strip.setColor([127,0,0])
    strip.show()
    mainloop()
