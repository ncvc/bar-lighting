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

SOCKET_NAME = "/tmp/thechillsocket"
INPUT_PIN   = 8

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
                              Animation.BLACKOUT     : Animation.Blackout(strip),
                              Animation.RAINBOW      : Animation.Rainbow(strip),
                              Animation.RAINBOWCYCLE : Animation.RainbowCycle(strip),
                              Animation.COLOR        : Animation.StaticColor(strip),
                              Animation.RANDOM       : Animation.RandomChoice(strip)}
        
        self.stepper.start()
        self.buttonmonitor.start()

    def addToQueue(self, command):
        if re.search(r"^r:\d{1,3},g:\d{1,3},b:\d{1,3}$", command):
            r, g, b = [int(i.split(":")[-1]) for i in command.split(",")]
            self.animations[Animation.COLOR].setRGB(r, g, b)
            command = Animation.COLOR

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
        print "Animator Received:     {}".format(self.data)
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
                    print 'Stepper retreived {0} from queue'.format(self.animation)
                except Queue.Empty:
                    pass
            
    def join(self, timeout=None):
        print 'Stepper thread exiting'
        self.stop_request.set()
        super(Stepper, self).join(timeout)

class ButtonMonitor(threading.Thread, object):
    def __init__(self, wait=.25):
        super(ButtonMonitor, self).__init__()
        self.stop_request = threading.Event()
        self.wait = wait
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN)

    def run(self):
        print "Button Monitor thread started"
        message_sent = False
        while not self.stop_request.isSet():
            if GPIO.input(INPUT_PIN) and not message_sent:
                sendMessage(Animation.RANDOM)
                message_sent = True
            else:
                message_sent = False
            time.sleep(self.wait)

    def join(self, timeout=None):
        print "Button Monitor thread exiting"
        self.stop_request.set()
        super(ButtonMonitor, self).join(timeout)

def sendMessage(message):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_NAME)
        sock.send(message)
        print "Sent:     {}".format(message)
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
