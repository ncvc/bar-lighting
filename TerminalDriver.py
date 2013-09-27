import Animator
import subprocess

while True:
    s = raw_input(">")
    if s is "q":
        break
    Animator.sendMessage(s)
