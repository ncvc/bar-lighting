# Class representing the LED Strip and a test class
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time, math
from Tkinter import Canvas, Tk, mainloop, Toplevel

DEV_PATH = '/dev/spidev0.0'
MAX_BRIGHTNESS = 127
DEFAULT_LED_SIZE = 40
SHOW_SLEEP_TIME = 0.0000001

# Base strip class that implements nearly all necessary functionality.
# Implementing classes must override the show() method
class BaseStrip(object):
    def __init__(self, num_pixels, row_length):
        self.num_pixels = num_pixels
        self.row_length = row_length
        self.rows = num_pixels / row_length
        self.columns = row_length
        self.xmasMode   = False
        self.buffer     = [[0,0,0]] * num_pixels

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

        self.buffer[pixel] = [int(i) for i in color]

    def setGridPixelColor(self, x, y, color):
        if y % 2 == 0 :
            x_offset = x
        else:
            x_offset = self.columns - x - 1
        self.setPixelColor(x_offset + y * self.row_length, color)

    def getGridPixelColor(self, x, y):
        if y % 2 == 0 :
            x_offset = x
        else:
            x_offset = self.columns - x - 1
        return self.buffer[x_offset + y * self.row_length]

    def setColor(self, color):
        for i in range(self.num_pixels):
            self.setPixelColor(i, color)

    def setColumnColor(self, column, color):
        for row in range(self.rows):
            self.setPixelColor(column, row, color)

    def setRowColor(self, row, color):
        for column in range(self.columns):
            self.setPixelColor(column, row, color)

    def blackout(self):
        self.setColor([0,0,0])
        self.show()

    def show(self):
        raise NotImplementedError("Do not use BaseStrip directly - try Strip or TestingStrip")

    def enableXmasMode(self, enable=True):
        self.xmasMode = enable

    def getPixelColor(self, i):
        return self.buffer[i]

    def __len__(self):
        return self.num_pixels

    def __getitem__(self, i):
        return self.buffer[i]

# Class for a real light strip
class Strip(BaseStrip):
    def __init__(self, num_pixels, row_length, device_name=DEV_PATH):
        super(Strip, self).__init__(num_pixels, row_length)
        self.device = file(device_name, "wb")
        self.show()

    def show(self):
        for i in range(self.num_pixels):
            r, g, b = self[i]
            self.device.write(chr(g | 0x80))
            self.device.write(chr(r | 0x80))
            self.device.write(chr(b | 0x80))
            self.device.flush()
        self.device.write(bytearray(b'\x00\x00\x00'))  # zero fill the last to prevent stray colors at the end
        self.device.write(bytearray(b'\x00'))
        self.device.flush()
        time.sleep(SHOW_SLEEP_TIME)


# Class for an on-screen testing strip
class TestingStrip(BaseStrip):
    def __init__(self, num_pixels, row_length, led_size=DEFAULT_LED_SIZE):
        super(TestingStrip, self).__init__(num_pixels, row_length)
        led_window = Tk()
        led_window.title('LED Simulator')
        MARGIN = 5
        led_size = min((led_window.winfo_screenwidth() - 2 * MARGIN) / row_length, led_size)
        num_rows = math.ceil(num_pixels / row_length)
        height = num_rows * led_size + (1 + num_rows) * MARGIN
        width = led_size * row_length + 2 * MARGIN
        self.canvas = Canvas(led_window, width=width, height=height)
        self.canvas.pack()
        self.leds = [] * num_pixels
        self.leds = [self.create_rectangle(i, num_pixels, row_length, led_size, MARGIN) for i in xrange(num_pixels)]
        self.canvas.update()

    def show(self):
        for i in xrange(self.num_pixels):
            color = '#%02x%02x%02x' % tuple([(255 * c) / MAX_BRIGHTNESS for c in self[i]])
            self.canvas.itemconfigure(self.leds[i], fill=color)
        self.canvas.update()
        time.sleep(SHOW_SLEEP_TIME)

    def create_rectangle(self, index, num_pixels, row_length, led_size, margin):
        #x0
        if (index / row_length) % 2 == 0:
            x0 = margin + (index % row_length) * led_size
        else:
            x0 = margin + (row_length - (index % row_length) - 1) * led_size

        #y0
        y0 = margin + (led_size + margin) * (index / row_length)

        #x1
        if (index / row_length) % 2 == 0:
            x1 = margin + ((index % row_length) + 1) * led_size
        else:
            x1 = margin + (row_length - (index % row_length)) * led_size

        #y1
        y1 = margin + (led_size + margin) * (index / row_length) + led_size

        return self.canvas.create_rectangle(x0, y0, x1, y1)


if __name__ == '__main__':
    strip = TestingStrip(32)
    strip.setColor([127,0,0])
    strip.show()
    mainloop()
