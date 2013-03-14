import cProfile
import Strip

s = Strip.HardwareStrip(64, "/dev/spidev0.0")

cProfile.run("s.setColor([127,127,127])")
