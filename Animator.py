import SocketServer
import Animation
import Strip
import Queue
import threading
import os.path
import socket
import re
import time
import sys
import argparse
from ModCounter import ModCounter
from Tkinter import mainloop, Toplevel, PhotoImage, Button

DEFAULT_STRIP_LENGTH = 64
DEFAULT_ROW_LENGTH = 32

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="show the debug statements", action="store_true")
parser.add_argument("-s", "--simulate", help="run in simulation", action="store_true")
parser.add_argument("-l", "--length", help="set the strip length", default=DEFAULT_STRIP_LENGTH, type=int)
parser.add_argument("-r", "--rowlength", help="set the row length", default=DEFAULT_ROW_LENGTH, type=int)
parser.add_argument("-b", "--button", help="run with the button control", action="store_true")

if __name__ == "__main__":
    args = parser.parse_args()
else:
    args = parser.parse_args([])

DEBUG = args.verbose
SIMULATE = args.simulate
STRIP_LENGTH = args.length
ROW_LENGTH = min(args.rowlength, STRIP_LENGTH)
USE_BUTTON = args.button

def debugprint(msg):
    if DEBUG:
        print msg

GPIO_AVAILABLE = True
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO_AVAILABLE = False
    debugprint("Failed to import RPi.GPIO, continuing in hopes that we don't need it")

SOCKET_NAME = "/tmp/thechillsocket"
INPUT_PIN   = 24

NO_STRIP_ATTACHED = SIMULATE

try:
    StreamServer = SocketServer.UnixStreamServer
except AttributeError:
    # Probably on a Windows machine, we must be testing with no LED strip attached
    NO_STRIP_ATTACHED = True
    StreamServer = SocketServer.BaseServer

class ButtonEvent:
    SINGLEPRESS = 'singlepress'
    DOUBLEPRESS = 'doublepress'
    LONGPRESS   = 'longpress'

class Animator(StreamServer, object):
    def __init__(self, handler, noStrip=NO_STRIP_ATTACHED):
        super(Animator, self).__init__(SOCKET_NAME, handler)
        self.queue         = Queue.Queue(1)
        if noStrip:
            strip          = Strip.SimulationStrip(STRIP_LENGTH, ROW_LENGTH)
        else: 
            strip          = Strip.HardwareStrip(STRIP_LENGTH)
        self.strip         = strip

        self.counter     = ModCounter(len(Animation.DYNAMIC_ANIMATIONS))

        self.stepper = Stepper(self.queue, Animation.ANIMATIONS[Animation.BLACKOUT], strip)
        self.stepper.start()

        if GPIO_AVAILABLE and USE_BUTTON:
            self.buttonmonitor = ButtonMonitor()
            self.buttonmonitor.start()

        self.processCommand(ButtonEvent.SINGLEPRESS)

    def processCommand(self, command):
        debugprint('Processing command: {0}'.format(command))
        animation = None

        if re.search(r"^r:\d{1,3},g:\d{1,3},b:\d{1,3}$", command):
            r, g, b = [int(i.split(":")[-1]) for i in command.split(",")]
            animation = Animation.ANIMATIONS[Animation.COLOR]
            animation.color.setrgb(r, g, b)

        elif command == ButtonEvent.SINGLEPRESS:
            animation = Animation.ANIMATIONS.get(Animation.DYNAMIC_ANIMATIONS[self.counter.i])
            self.counter += 1

        elif command == ButtonEvent.DOUBLEPRESS:
            animation = Animation.ANIMATIONS[Animation.RANDOM]

        elif command == ButtonEvent.LONGPRESS:
            animation = Animation.ANIMATIONS[Animation.BLACKOUT]

        else:
            animation = Animation.ANIMATIONS.get(command)

        if animation:
            try:        
                self.queue.put(animation, False)
            except Queue.Full:
                pass

    def shutdown(self):
        self.stepper.join()
        if USE_BUTTON:
            self.buttonmonitor.join()

        super(Animator, self).shutdown()

class AnimationRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        debugprint("Animator Received:     {}".format(self.data))
        self.server.processCommand(self.data)

class Stepper(threading.Thread, object):
    def __init__(self, queue, anim, strip):
        super(Stepper, self).__init__()
        self.stop_request = threading.Event()
        self.queue        = queue
        self.animation    = anim
        self.strip        = strip
        self.previous_animation = anim

        anim.setup(strip)

    def run(self):
        debugprint('Stepper thread started')
        while not self.stop_request.isSet():
            done = self.animation.step(self.strip)
            self.strip.show()
            time.sleep(self.animation.get_wait())
            if done:
                try:
                    next_animation = self.queue.get(False)
                    if next_animation.returns_control:
                        self.queue.put(self.animation, False)
                    self.animation = next_animation
                    self.animation.setup(self.strip)
                    debugprint('Stepper retrieved {0} from queue'.format(self.animation))
                except Queue.Empty:
                    pass

    def join(self, timeout=None):
        debugprint('Stepper thread exiting')
        self.stop_request.set()
        super(Stepper, self).join(timeout)

class States:
	WAITING             = 0
	LONGPRESSVALIDATE   = 1
        LONGPRESS           = 2
	SINGLEPRESSVALIDATE = 3
	DOUBLEPRESS         = 4

class ButtonMonitor(threading.Thread, object):
    def __init__(self, wait=.01):
        super(ButtonMonitor, self).__init__()
        self.stop_request = threading.Event()
        self.wait = wait
        self.state = States.WAITING
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN)
	
    def run(self):
        debugprint("Button Monitor thread started")
        long_press_validate_count   = 0
        single_press_validate_count = 0
        
        long_press_validate_threshold   = 150
        single_press_validate_threshold = 15
        
        while not self.stop_request.isSet():
            input_value  = not GPIO.input(INPUT_PIN)
            if self.state == States.WAITING:
                if input_value:
                    self.state = States.LONGPRESSVALIDATE
                    
            elif self.state == States.LONGPRESSVALIDATE:
                if input_value:
                    if long_press_validate_count > long_press_validate_threshold:
                        Self.state = States.LONGPRESS
                        long_press_validate_count = 0
                        sendMessage(ButtonEvent.LONGPRESS)
                    else:
                        long_press_validate_count += 1
                else:
                    self.state = States.SINGLEPRESSVALIDATE
                    long_press_validate_count = 0

            elif self.state == States.LONGPRESS:
                if not input_value:
                    self.state = States.WAITING

            elif self.state == States.SINGLEPRESSVALIDATE:
                if input_value:
                    self.state = States.DOUBLEPRESS
                    single_press_validate_count = 0
                else:
                    if single_press_validate_count > single_press_validate_threshold:
                        self.state = States.WAITING
                        single_press_validate_count = 0
                        sendMessage(ButtonEvent.SINGLEPRESS)
                    else:
                        single_press_validate_count += 1
     
            elif self.state == States.DOUBLEPRESS:
                if not input_value:
                    sendMessage(ButtonEvent.DOUBLEPRESS)
                    self.state = States.WAITING
            
            time.sleep(self.wait)

    def join(self, timeout=None):
        debugprint("Button Monitor thread exiting")
        self.stop_request.set()
        super(ButtonMonitor, self).join(timeout)


def sendMessage(message):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_NAME)
        sock.send(message)
        debugprint("Sent:     {}".format(message))
    except IOError as e:
        if e.errno == 13:
            print "{0}\nTry again using sudo".format(e)
        elif e.errno == 111:
            print "{0}\nError connecting to socket {1}\nMake sure the server is running and is on this socket".format(e, SOCKET_NAME)
        else:
            print "An IOError occurred: ", e
    except Exception as e:
        print "An error occurred: ", e
    finally:
        sock.close()

class RunServer(threading.Thread, object):
    def __init__(self, simulate):
        super(RunServer, self).__init__()
        self.simulate = simulate
        self.server = None

    def run(self):
        print "Creating animation server..."
        if os.path.exists(SOCKET_NAME):
            os.remove(SOCKET_NAME)
        
        self.server = Animator(AnimationRequestHandler, self.simulate)
        if not self.simulate:
            print "Starting animation server..."
            print "Animation server is running on socket {0}".format(SOCKET_NAME)
            #print "Quit the server with CONTROL-C."        
            self.server.serve_forever()
        else:
            print "Starting simulation..."
            button_window = Toplevel()
            button_window.title('Button Input')
            img = PhotoImage(file="easy_button.gif")
            single_easy_button = Button(button_window, image=img)
            single_easy_button.pack()
            single_easy_button.bind("<Button-1>", lambda e: server.processCommand(ButtonEvent.SINGLEPRESS))
            double_easy_button = Button(button_window, text="double tap")
            double_easy_button.pack()
            double_easy_button.bind("<Button-1>", lambda e: server.processCommand(ButtonEvent.DOUBLEPRESS))        
            mainloop()
            
    def join(self, timeout=None):
        self.server.shutdown()
        super(RunServer, self).join(timeout)

if __name__ == "__main__":
    run_server = RunServer(SIMULATE)
    run_server.start()
    time.sleep(1)
    commands = Animation.ANIMATIONS.keys()
    commands.sort()
    print "Type 'q' to quit or 'h' for help."
 
    while True:
        cmd = raw_input(">")
        if cmd == "q" or cmd == "quit":
            break
        elif cmd == "help" or cmd == "h" or cmd not in commands:
            print "The available commands are:"
            for command in commands:
                print "\t{0}".format(command)
        else:
            sendMessage(cmd)

    sendMessage(Animation.BLACKOUT)
    run_server.join()

    
