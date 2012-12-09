#tests the socket connection to the Animator
#run as sudo, all arguments get passed as the message

import Animator
import sys

if __name__ == "__main__":
    Animator.sendMessage(" ".join(sys.argv[1:]))
