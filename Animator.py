import SocketServer
import Animation
import Strip
import Queue
import threading
import os.path

socket_name = "/tmp/thechillsocket"

class Animator(SocketServer.UnixStreamServer, object):
    def __init__(self, socket_name, handler):
        super(Animator, self).__init__(socket_name, handler)
        self.queue = Queue.Queue()
        strip = Strip.Strip(32)
#        strip.enableXmasMode()
        self.stepper = Stepper(self.queue, Animation.Animation(strip))
#        self.stepper.start()
        self.animations = {'colorchase' : Animation.ColorChase(strip),
                           'colorwipe' : Animation.ColorWipe(strip),
                           'blackout' : Animation.Blackout(strip),
                           'rainbow' : Animation.Rainbow(strip),
                           'rainbowcycle' : Animation.RainbowCycle(strip)}
    
    def addToQueue(self, animation):
        if self.animations.has_key(animation):
            self.queue.put(self.animations[animation])

    def shutdown(self):
        self.stepper.join()
        super(Animator, self).shutdown()

class AnimationRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
#        print "{} wrote:".format(self.client_address[0])
        print "Received:     {}".format(self.data)
        #self.server.addToQueue(self.data)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
#        self.wfile.write(self.data.upper())

class Stepper(threading.Thread, object):
    def __init__(self, queue, anim):
        super(Stepper, self).__init__()
        self.stop_request = threading.Event()
        self.queue = queue
        self.animation = anim
        self.i = 0

    def run(self):
        while not self.stop_request.isSet():
            try:
                self.animation = self.queue.get(True, 0.0000001)
                print "retreived item from queue"
            except Queue.Empty:
                pass
            self.i = self.i + 1
            self.animation.step()
            
    def join(self, timeout=None):
        print "join called"
        self.stop_request.set()
        super(Stepper, self).join(timeout)


import socket
import sys
import os.path

def sendMessage(message):
    if os.path.exists(socket_name):
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            # Connect to server and send data
            sock.connect(socket_name)
            sock.send(message)
            print "Sent:     {}".format(message)

            # Receive data from the server and shut down
            # received = sock.recv(1024) 
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
    else:
        print "Couldn't connect to socket"

if __name__ == "__main__":
    print "Starting server"
    try:
        if os.path.exists(socket_name):
            os.remove(socket_name)

            # Create the server, binding to localhost on port 9999
            server = Animator(socket_name, AnimationRequestHandler)

            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl-C
    except Exception as e:
        print "Error starting server:\n" + str(e)
        raise

    print "Animation server is running on socket {0}".format(socket_name)
    print "Quit the server with CONTROL-C."
    server.serve_forever()
