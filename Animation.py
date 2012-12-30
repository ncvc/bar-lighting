import random
import Colors
from ModCounter import ModCounter


# Base Animation class that implements nearly all necessary functionality.
# Implementing classes must override the step() method
class BaseAnimation(object):
    def __init__(self, wait):
        self.wait = wait
        self.name = "Default"
        self.returns_control = False

    def setup(self, strip):
        strip.blackout()

    def step(self, strip):
        raise NotImplementedError("Do not use BaseAnimation directly, use a subclass with step() implemented")

    def wheel(self, position, random=False):
        r = 0
        g = 0
        b = 0

        if position / 128 == 0:
            r = 127 - position % 128
            g = position % 128
            b = 0
        elif position / 128 == 1:
            g = 127 - position % 128
            b = position % 128
            r = 0
        elif position / 128 == 2:
            b = 127 - position % 128
            r = position % 128
            g = 0

        return [r, g, b]

    def __repr__(self):
        return self.name


class StaticColor(BaseAnimation):
    def __init__(self, color, wait=.5):
        super(StaticColor, self).__init__(wait=wait)
        self.color = color

    def step(self, strip):
        strip.setColor(self.color.rgb())
        return True

    def __repr__(self):
        return str(self.color)


class Rainbow(BaseAnimation):
    def __init__(self, wait=0.01):
        super(Rainbow, self).__init__(wait)
        self.counter = ModCounter(384)
        self.name = "Rainbow"

    def step(self, strip):
        for i in range(strip.num_pixels):
            strip.setPixelColor(i, self.wheel((i + self.counter.i) % 384))
        self.counter += 5
        return True


class RainbowCycle(BaseAnimation):
    def __init__(self, wait=0.01):
        super(RainbowCycle, self).__init__(wait)
        self.counter = ModCounter(384 * 5)
        self.name = "Rainbow Cycle"

    def step(self, strip):
        for i in range(strip.num_pixels):
            strip.setPixelColor(i, self.wheel(((i * 384 / strip.num_pixels) + self.counter.i) % 384))
        self.counter += 1
        return True


class ColorWipe(BaseAnimation):
    def __init__(self, wait=.01):
        super(ColorWipe, self).__init__(wait)
        self.color = Colors.BLACKOUT
        self.name = "Color Wipe"

    def setup(self, strip):
        super(ColorWipe, self).setup(strip)
        self.counter = ModCounter(strip.num_pixels)
        self.counter.reset()

    def step(self, strip):
        if self.counter == 0:
            rand = self.color
            while rand == self.color:
                rand = random.choice(Colors.COLORS) 
            self.color = rand
        strip.setPixelColor(self.counter.i, self.color.rgb())
        self.counter += 1
        return self.counter == 0


class Blink(BaseAnimation):
    def __init__(self, num_blinks, wait=.25):
        super(Blink, self).__init__(wait)
        self.i = 0
        self.num_blinks = num_blinks
        self.returns_control = True
        self.name = "Blink"

    def setup(self, strip):
        super(Blink, self).setup(strip)
        self.i = 0

    def step(self, strip):
        if self.i <= self.num_blinks * 2:
            if self.i % 2 == 0:
                strip.setColor([0,0,0])
            else:
                strip.setColor(Colors.WHITE.rgb())

        self.i += 1
        return self.i > self.num_blinks * 2


class RandomChoice(BaseAnimation):
    def __init__(self, wait=.02):
        super(RandomChoice, self).__init__(wait)
        self.i = 0
        self.returns_control = True
        self.winner = None
        self.color = [0,0,0]
        self.num_blinks = 7
        self.toggle = True
        self.blink_counter = 0
        self.name = "Random Choice"

    def setup(self, strip):
        super(RandomChoice, self).setup(strip)
        self.i = 0
        self.blink_counter = 0
        self.winner = random.randint(6 * strip.num_pixels, 9 * strip.num_pixels)
        self.wait = .02
        self.color = random.choice(Colors.COLORS).rgb()

    def step(self, strip):
        if self.winner - self.i < 20 and self.wait < self.winner:
            self.wait = self.wait * 1.2
        if self.i < self.winner:
            strip.setPixelColor(self.i - 1, [0,0,0])
            strip.setPixelColor(self.i, self.color)
            self.i += 1
        else:
            self.wait = 0.3
            strip.setPixelColor(self.i - 1, [0,0,0])
            if self.toggle:
                self.toggle = False
                strip.setPixelColor(self.i , [0,0,0])
            else:
                self.toggle = True
                strip.setPixelColor(self.i, [127, 127, 127])
            self.blink_counter += 1

        return self.blink_counter > 2 * self.num_blinks


class MusicReactive(BaseAnimation):
    def __init__(self):
        super(MusicReactive, self).__init__(0)
        self.i = 0
        self.returns_control = True
        self.name = "MusicReactive"

    def setup(self, strip):
        super(MusicReactive, self).setup(strip)
        self.i = 0

    def step(self, strip):
        strip.setColor([self.i] * 3)

        self.i += 1
        return False


# String constants
COLORWIPE      = 'colorwipe'
BLACKOUT       = 'blackout'
COLOR          = 'color'
STATICRED      = 'staticred'
STATICBLUE     = 'staticblue'
STATICGREEN    = 'staticgreen'
STATICMAGENTA  = 'staticmagenta'
STATICCYAN     = 'staticcyan'
STATICWHITE    = 'staticwhite'
BLACKOUT       = 'blackout'
RANDOM         = 'randomchoice'
RAINBOW        = 'rainbow'
RAINBOWCYCLE   = 'rainbowcycle'
BLINKONCE      = 'blinkonce'
BLINKTWICE     = 'blinktwice'
MUSIC          = 'music'

DYNAMIC_ANIMATIONS = [COLORWIPE,
                      RAINBOW,
                      RAINBOWCYCLE,
                      STATICRED,
                      STATICGREEN,
                      STATICBLUE,
                      STATICMAGENTA,
                      STATICCYAN,
                      STATICWHITE,
                      BLACKOUT,
                      MUSIC]

ANIMATIONS    = {COLORWIPE    : ColorWipe(),
                 RAINBOW      : Rainbow(),
                 RAINBOWCYCLE : RainbowCycle(),
                 STATICRED    : StaticColor(Colors.RED),
                 STATICGREEN  : StaticColor(Colors.GREEN),
                 STATICBLUE   : StaticColor(Colors.BLUE),
                 STATICMAGENTA: StaticColor(Colors.MAGENTA),
                 STATICCYAN   : StaticColor(Colors.CYAN),
                 STATICWHITE  : StaticColor(Colors.WHITE),
                 BLACKOUT     : StaticColor(Colors.BLACKOUT),
                 RANDOM       : RandomChoice(),
                 BLINKONCE    : Blink(1),
                 BLINKTWICE   : Blink(2),
                 COLOR        : StaticColor(Colors.CUSTOM),
                 MUSIC        : MusicReactive()}
