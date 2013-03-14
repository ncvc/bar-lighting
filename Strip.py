# Class representing the LED Strip and a test class
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time, math, copy
from Tkinter import Canvas, Tk, mainloop, Toplevel

DEV_PATH = '/dev/spidev0.0'
MAX_BRIGHTNESS = 127
DEFAULT_LED_SIZE = 40
SHOW_SLEEP_TIME = 0.0000001

# Base strip class that defines the strip interface
# Implementing classes must override all methods
class BaseStrip(object):
    def __init__(self, length):
        self.length = length
        
    def setPixelColor(self, color):
        raise NotImplementedError("Do not use BaseStrip directly - try HardwareStrip or SimulationStrip")
    
    def getPixelColor(self, color):
        raise NotImplementedError("Do not use BaseStrip directly - try HardwareStrip or SimulationStrip")
    
    def setColor(self, color):
        raise NotImplementedError("Do not use BaseStrip directly - try HardwareStrip or SimulationStrip")
        
    def blackout(self):
        raise NotImplementedError("Do not use BaseStrip directly - try HardwareStrip or SimulationStrip")
        
    def show(self):
        raise NotImplementedError("Do not use BaseStrip directly - try HardwareStrip or SimulationStrip")
        
    def __len__(self):
        return self.length

    def __getitem__(self, pixel):
        return self.getPixelColor(pixel)

# Class that contains a buffer to hold pixel values
# and almost all functionality.
# Overriding classes must implement show() method
class Strip(BaseStrip):
    def __init__(self, length):
        super(Strip, self).__init__(length)
        self.buffer = [[0,0,0]] * length

    def setPixelColor(self, pixel, color):
        self.buffer[pixel] = [int(max(0, min(i, MAX_BRIGHTNESS))) for i in color]

    def getPixelColor(self, pixel):
        # forces assignment of pixel colors using setPixelColor
        return copy.deepcopy(self.buffer[pixel])

    def setColor(self, color):
        for pixel in range(self.length):
            self.setPixelColor(pixel, color)

    def blackout(self):
        self.setColor([0,0,0])

    def show(self):
        raise NotImplementedError("Do not use Strip directly - try HardwareStrip or SimulationStrip")

class Substrip(BaseStrip):
    def __init__(self, start_fcn, end_fcn):
        super(Substrip, self).__init__(0)
        self.start_fcn = start_fcn
        self.end_fcn = end_fcn
        self.strip = None
        self.start = 0
        self.end   = 0

    def setPixelColor(self, pixel, color):
        self.strip.setPixelColor(self.start + pixel, color)

    def getPixelColor(self, pixel):
        return self.strip.getPixelColor(self.start + pixel)

    def setColor(self, color):
        for pixel in range(len(self)):
            self.strip.setPixelColor(self.start + pixel, color)

    def blackout(self):
        for pixel in range(len(self)):
            self.strip.setPixelColor(self.start + pixel, [0, 0, 0])

    def show(self):
        self.strip.show()

    def setStrip(self, strip):
        self.strip = strip
        self.start = self.start_fcn(len(strip))
        self.end = self.end_fcn(len(strip))
        self.length = self.end - self.start + 1
        
class HardwareStrip(Strip):
    def __init__(self, length, device_name=DEV_PATH):
        super(HardwareStrip, self).__init__(length)
        self.device = file(device_name, "wb");

    def show(self):
        for i in range(self.length):
            r, g, b = self[i]
            self.device.write(chr(r | 0x80))
            self.device.write(chr(g | 0x80))
            self.device.write(chr(b | 0x80))
            self.device.flush()
        self.device.write(bytearray(b'\x00\x00\x00'))  # zero fill the last to prevent stray colors at the end
        self.device.write(bytearray(b'\x00'))
        self.device.flush()
        time.sleep(SHOW_SLEEP_TIME)

# Class for an on-screen testing strip
class SimulationStrip(Strip):
    def __init__(self, length, row_length, led_size=DEFAULT_LED_SIZE):
        super(SimulationStrip, self).__init__(length)
        led_window = Tk()
        led_window.title('LED Simulator')
        MARGIN = 5
        led_size = min((led_window.winfo_screenwidth() - 2 * MARGIN) / row_length, led_size)
        num_rows = math.ceil(length / row_length)
        height = num_rows * led_size + (1 + num_rows) * MARGIN
        width = led_size * row_length + 2 * MARGIN
        self.canvas = Canvas(led_window, width=width, height=height)
        self.canvas.pack()
        self.leds = [] * length
        self.leds = [self.create_rectangle(i, row_length, led_size, MARGIN) for i in xrange(length)]
        self.canvas.update()

    def show(self):
        for i in xrange(self.length):
            color = '#%02x%02x%02x' % tuple([(255 * c) / MAX_BRIGHTNESS for c in self[i]])
            self.canvas.itemconfigure(self.leds[i], fill=color)
        self.canvas.update()
        time.sleep(SHOW_SLEEP_TIME)

    def create_rectangle(self, index, row_length, led_size, margin):
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
