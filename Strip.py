# Class representing the LED Strip
# Python port of arduino c project on adafruit.com
# Colors are represented as a three element list [R, G, B]
# where 0 <= R, G, B <= 127

import time

dev = '/dev/spidev0.0'

class Strip:
    def __init__(self, num_pixels, device_name=dev):
        self.num_pixels = num_pixels
        self.device = file(device_name, "wb")
        self.buffer = bytearray(num_pixels * 3)
        self.show()

    def setPixelColor(self, pixel, color):
        pixel = pixel % self.num_pixels
        if (pixel < self.num_pixels):
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
