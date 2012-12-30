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
from ModCounter import ModCounter
from Tkinter import mainloop

GPIO_AVAILABLE = True
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO_AVAILABLE = False
    print "Failed to import RPi.GPIO, continuing in hopes that we don't need it"

SOCKET_NAME = "/tmp/thechillsocket"
INPUT_PIN   = 24
DEBUG = False

NO_STRIP_ATTACHED = False
try:
    StreamServer = SocketServer.UnixStreamServer
except AttributeError:
    # Probably on a Windows machine, we must be testing with no LED strip attached
    NO_STRIP_ATTACHED = True
    StreamServer = SocketServer.BaseServer


class States:
    RANDOMSELECTION = 'random selection'
    MODESELECTION   = 'mode selection'

class ButtonEvent:
    SINGLEPRESS = 'singlepress'
    DOUBLEPRESS = 'doublepress'

class ControlCommand:
    TOGGLEXMASMODE = 'togglexmasmode'

class Animator(StreamServer, object):
    def __init__(self, handler, noStrip=NO_STRIP_ATTACHED):
        super(Animator, self).__init__(SOCKET_NAME, handler)
        self.queue         = Queue.Queue(1)
        if noStrip:
            strip          = Strip.TestingStrip(32)
        else: 
            strip          = Strip.Strip(32)
        self.strip         = strip
        self.xmastoggle    = False

        #transitions keys are for current state
        #transitions values are a tuple of the next state and Animation to be played, or None
        self.transitions = {States.RANDOMSELECTION : (States.MODESELECTION, Animation.BLINKTWICE),
                            States.MODESELECTION   : (States.RANDOMSELECTION, Animation.BLINKONCE)}

        self.counter     = ModCounter(len(Animation.DYNAMIC_ANIMATIONS))
        self.state       = States.MODESELECTION

        self.stepper = Stepper(self.queue, Animation.ANIMATIONS[Animation.BLACKOUT], strip)
        self.stepper.start()

        if GPIO_AVAILABLE:
            self.buttonmonitor = ButtonMonitor()
            self.buttonmonitor.start()

        # self.processCommand(ButtonEvent.SINGLEPRESS)
        self.processCommand(Animation.MUSIC)

    def processCommand(self, command):
        animation = None

        if re.search(r"^r:\d{1,3},g:\d{1,3},b:\d{1,3}$", command):
            r, g, b = [int(i.split(":")[-1]) for i in command.split(",")]
            animation = Animation.ANIMATIONS[Animation.COLOR]
            animation.color.setrgb(r, g, b)

        elif command == ButtonEvent.SINGLEPRESS:
            if self.state == States.RANDOMSELECTION:
                animation = Animation.ANIMATIONS[Animation.RANDOM]
            else:
                animation = Animation.ANIMATIONS.get(Animation.DYNAMIC_ANIMATIONS[self.counter.i])
                self.counter += 1

        elif command == ButtonEvent.DOUBLEPRESS:
            state, anim = self.transitions.get(self.state)
            self.state = state
            print "Changed to {0}".format(self.state)
            animation = Animation.ANIMATIONS.get(anim)

        elif command == ControlCommand.TOGGLEXMASMODE:
            self.xmastoggle = not self.xmastoggle
            self.strip.enableXmasMode(self.xmastoggle)

        else:
            animation = Animation.ANIMATIONS.get(command)

        if animation:
            try:        
                self.queue.put(animation, False)
            except Queue.Full:
                pass

    def shutdown(self):
        self.stepper.join()
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
        print "Stepper thread started"
        while not self.stop_request.isSet():
            done = self.animation.step(self.strip)
            self.strip.show()
            time.sleep(self.animation.wait)
            if done:
                try:
                    next_animation = self.queue.get(False)
                    if next_animation.returns_control:
                        self.queue.put(self.animation, False)
                    self.animation = next_animation
                    self.animation.setup(self.strip)
                    debugprint('Stepper retreived {0} from queue'.format(self.animation))
                    print self.animation
                except Queue.Empty:
                    pass

    def join(self, timeout=None):
        print 'Stepper thread exiting'
        self.stop_request.set()
        super(Stepper, self).join(timeout)

class ButtonMonitor(threading.Thread, object):
    def __init__(self, wait=.01):
        super(ButtonMonitor, self).__init__()
        self.stop_request = threading.Event()
        self.wait = wait
        self.buffer_length = 25

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN)

    def run(self):
        print "Button Monitor thread started"
        buffer = [False] * self.buffer_length
        counter = ModCounter(self.buffer_length)
        num_presses = 0
        while not self.stop_request.isSet():
            input = not GPIO.input(INPUT_PIN)
            new_num_presses = self.num_clicks(buffer[counter.i:] + buffer[:counter.i])
            buffer[counter.i] = input
            counter += 1
            if new_num_presses == 0:
                if num_presses == 1:
                    sendMessage(ButtonEvent.SINGLEPRESS)
                elif num_presses == 2:
                    sendMessage(ButtonEvent.DOUBLEPRESS)
                num_presses = 0
            else:
                num_presses = max(num_presses, new_num_presses)

            time.sleep(self.wait)

    def num_clicks(self, buffer):
        clicks = 0
        for i in range(len(buffer) - 1):
            if buffer[i + 1] and not buffer[i]:
                clicks += 1
        return clicks

    def join(self, timeout=None):
        print "Button Monitor thread exiting"
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
            print e
    except Exception as e:
        print e
    finally:
        sock.close()

def debugprint(msg):
    if DEBUG:
        print msg

if __name__ == "__main__":
    noServe = len(sys.argv) > 1 and sys.argv[1] == 'noserve'

    print "Starting server"
    if os.path.exists(SOCKET_NAME):
        os.remove(SOCKET_NAME)

    server = Animator(AnimationRequestHandler, noServe)

    if not noServe:
        print "Animation server is running on socket {0}".format(SOCKET_NAME)
        print "Quit the server with CONTROL-C."
        server.serve_forever()
    else:
        print 'noserve specified, debug stuff happening'
        mainloop()
