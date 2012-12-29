import SocketServer
import Animation
import Strip
import Queue
import threading
import os.path
import socket
import datetime
import re
import time
import RPi.GPIO as GPIO
from Colors import *

SOCKET_NAME = "/tmp/thechillsocket"
INPUT_PIN   = 24

class States:
    RANDOMSELECTION = 'random selection'
    MODESELECTION   = 'mode selection'

class Animator(SocketServer.UnixStreamServer, object):
    def __init__(self, handler):
        super(Animator, self).__init__(SOCKET_NAME, handler)
        self.queue         = Queue.Queue(1)
        strip              = Strip.Strip(32)
        self.strip         = strip
        self.stepper       = Stepper(self.queue, Animation.Animation(strip, 0.01))
        self.buttonmonitor = ButtonMonitor()
        self.xmastoggle    = False
        self.animations    = {Animation.COLORWIPE    : Animation.ColorWipe(strip),
                              Animation.RAINBOW      : Animation.Rainbow(strip),
                              Animation.RAINBOWCYCLE : Animation.RainbowCycle(strip),
                              Animation.STATICRED    : Animation.StaticColor(RED, strip),
                              Animation.STATICGREEN  : Animation.StaticColor(GREEN, strip),
                              Animation.STATICBLUE   : Animation.StaticColor(BLUE, strip),
                              Animation.STATICMAGENTA: Animation.StaticColor(MAGENTA, strip),
                              Animation.STATICCYAN   : Animation.StaticColor(CYAN, strip),
                              Animation.STATICWHITE  : Animation.StaticColor(WHITE, strip),
                              Animation.BLACKOUT     : Animation.StaticColor(BLACKOUT, strip),
                              Animation.RANDOM       : Animation.RandomChoice(strip),
                              Animation.BLINKONCE    : Animation.Blink(1, strip),
                              Animation.BLINKTWICE   : Animation.Blink(2, strip)
}
        
        self.dynamic_animations = [Animation.COLORWIPE,
                                   Animation.RAINBOW,
                                   Animation.RAINBOWCYCLE,
                                   Animation.STATICRED,
                                   Animation.STATICGREEN, 
                                   Animation.STATICBLUE,
                                   Animation.STATICMAGENTA,
                                   Animation.STATICCYAN,
                                   Animation.STATICWHITE,
                                   Animation.BLACKOUT]

        self.transitions = {States.RANDOMSELECTION : (States.MODESELECTION,
                                                      Animation.BLINKTWICE),
                            States.MODESELECTION   : (States.RANDOMSELECTION,
                                                      Animation.BLINKONCE)}
        self.stepper.start()
        self.buttonmonitor.start()
        self.animation_index = 0
        self.state = States.MODESELECTION

        self.addToQueue('singlepress')

    def addToQueue(self, command):
        if re.search(r"^r:\d{1,3},g:\d{1,3},b:\d{1,3}$", command):
            r, g, b = [int(i.split(":")[-1]) for i in command.split(",")]
            self.animations[Animation.COLOR].setColor(Color('Custom', r, g, b))
            command = Animation.COLOR
        
        animation = None

        if command == 'singlepress':
            if self.state == States.RANDOMSELECTION:
                animation = self.animations[Animation.RANDOM]
            else:
                animation = self.animations.get(self.dynamic_animations[self.animation_index])
                self.animation_index  = (self.animation_index + 1) % len(self.dynamic_animations)
  
        elif command == "doublepress":
            state, alert = self.transitions.get(self.state)
            self.state = state
            print "Changed to {0}".format(self.state)
            animation = self.animations.get(alert)
        else:
            animation = self.animations.get(command)
        
        if animation:
            try:        
                self.queue.put(animation, False)
            except Queue.Full:
                pass

        elif command == Animation.TOGGLEXMASMODE:
            self.xmastoggle = not self.xmastoggle
            self.strip.enableXmasMode(self.xmastoggle)
            
    def shutdown(self):
        self.stepper.join()
        self.buttonmonitor.join()
        super(Animator, self).shutdown()

class AnimationRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        #print "Animator Received:     {}".format(self.data)
        self.server.addToQueue(self.data)

class Stepper(threading.Thread, object):
    def __init__(self, queue, anim):
        super(Stepper, self).__init__()
        self.stop_request = threading.Event()
        self.queue        = queue
        self.animation    = anim
        self.previous_animation = anim

    def run(self):
        print "Stepper thread started"
        while not self.stop_request.isSet():
            done = self.animation.step()
            if done:
                try:
                    next_animation = self.queue.get(False)
                    if next_animation.returns_control:
                        self.queue.put(self.animation, False)
                    self.animation = next_animation
                    self.animation.setup()
                    #print 'Stepper retreived {0} from queue'.format(self.animation)
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
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN)
        self.buffer_length = 25

    def run(self):
        print "Button Monitor thread started"
        buffer = [False] * self.buffer_length
        buffer_index = 0
        num_presses = 0
        while not self.stop_request.isSet():
            input = not GPIO.input(INPUT_PIN)
            new_num_presses = self.num_clicks(buffer[buffer_index:] + buffer[:buffer_index])
            buffer[buffer_index] = input
            buffer_index = (buffer_index + 1) % self.buffer_length
            if new_num_presses == 0:
                if num_presses == 1:
                    sendMessage('singlepress')
                elif num_presses == 2:
                    sendMessage('doublepress')
                num_presses = 0
            else:
                num_presses = max(num_presses, new_num_presses)
            
            time.sleep(self.wait)

    def num_clicks(self, buffer):
        clicks = 0
        for i in range(len(buffer) - 1):
            if buffer[i + 1] and not buffer[i]:
                #print '\n'
                #print buffer
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
        #print "Sent:     {}".format(message)
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

if __name__ == "__main__":
    print "Starting server"
    if os.path.exists(SOCKET_NAME):
        os.remove(SOCKET_NAME)
    try:
        server = Animator(AnimationRequestHandler)
    except Exception as e:
        print "{0}\nError starting server:\n".format(e)

    print "Animation server is running on socket {0}".format(SOCKET_NAME)
    print "Quit the server with CONTROL-C."
    server.serve_forever()
