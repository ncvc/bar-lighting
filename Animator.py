import SocketServer
import Animation
import Strip
import Queue
import threading

class Animator(SocketServer.TCPServer, object):
    def __init__(self, host, port, handler):
        super(Animator, self).__init__((host, port), handler)
        self.queue = Queue.Queue()
        strip = Strip.Strip(32)
        self.stepper = Stepper(self.queue, Animation.Animation(strip))
        self.stepper.start()
        self.animations = {'colorchase' : Animation.ColorChase(strip),
                           'colorwipe' : Animation.ColorWipe(strip),
                           'blackout' : Animation.Blackout(strip)}
    
    def addToQueue(self, animation):
        if self.animations.has_key(animation):
            print "got " + animation
            self.queue.put(self.animations[animation])

    def shutdown(self):
        self.stepper.join()
        super(Animator, self).shutdown()

class AnimationRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        self.server.addToQueue(self.data)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data.upper())

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
                self.animation = self.queue.get(True, 0.001)
                print "retreived item from queue"
            except Queue.Empty:
                pass
            self.i = self.i + 1
            self.animation.step()
            
    def join(self, timeout=None):
        print "join called"
        self.stop_request.set()
        super(Stepper, self).join(timeout)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = Animator(HOST, PORT, AnimationRequestHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
