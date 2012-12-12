import SocketServer
import Animation
import Strip
import Queue
import threading
import os.path
import socket
import datetime

socket_name = "/tmp/thechillsocket"

class Animator(SocketServer.UnixStreamServer, object):
    def __init__(self, socket_name, handler):
        super(Animator, self).__init__(socket_name, handler)
        self.queue      = Queue.Queue(1)
        strip           = Strip.Strip(32)
        self.stepper    = Stepper(self.queue, Animation.Animation(strip, 0.01))
        self.stepper.start()
        self.animations = {'colorchase' : Animation.ColorChase(strip),
                           'colorwipe' : Animation.ColorWipe(strip),
                           'blackout' : Animation.Blackout(strip),
                           'rainbow' : Animation.Rainbow(strip),
                           'rainbowcycle' : Animation.RainbowCycle(strip)}
    
    def addToQueue(self, animation):
        if self.animations.has_key(animation):
            try:        
                self.queue.put(self.animations[animation], False)
            except Queue.Full:
                pass

    def shutdown(self):
        self.stepper.join()
        super(Animator, self).shutdown()

class AnimationRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        print "Received:     {}".format(self.data)
        self.server.addToQueue(self.data)

class Stepper(threading.Thread, object):
    def __init__(self, queue, anim):
        super(Stepper, self).__init__()
        self.stop_request = threading.Event()
        self.queue        = queue
        self.animation    = anim
        self.start_time   = None

    def run(self):
        while not self.stop_request.isSet():
            try:
                self.animation = self.queue.get(False)
                print "retreived item from queue"
            except Queue.Empty:
                pass
            self.animation.step()
            
    def join(self, timeout=None):
        print "join called"
        self.stop_request.set()
        super(Stepper, self).join(timeout)

def sendMessage(message):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(socket_name)
        sock.send(message)
        print "Sent:     {}".format(message)
    except IOError as e:
        if e.errno == 13:
            print "{0}\nTry again using sudo".format(e)
        elif e.errno == 111:
            print "{0}\nError connecting to socket {1}\nMake sure the server is running and is on this socket".format(e, socket_name)
        else:
            print e
    except Exception as e:
        print e
    finally:
        sock.close()

if __name__ == "__main__":
    print "Starting server"
    if os.path.exists(socket_name):
        os.remove(socket_name)
    try:
        server = Animator(socket_name, AnimationRequestHandler)
    except Exception as e:
        print "{0}\nError starting server:\n".format(e)
        raise

    print "Animation server is running on socket {0}".format(socket_name)
    print "Quit the server with CONTROL-C."
    server.serve_forever()
