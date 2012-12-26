import RPi.GPIO as GPIO
import time

INPUT_PIN = 24

GPIO.setmode(GPIO.BOARD)
GPIO.setup(INPUT_PIN, GPIO.IN)

trigger = True

while True:
    #Wired active low!
    if not GPIO.input(INPUT_PIN):
        if trigger:
            trigger = False
            print "Triggering Function"
    else:
        trigger = True
    time.sleep(.25)
