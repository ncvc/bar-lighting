class Color(object):
    def __init__(self, name, r, g, b):
         self.r = r
         self.g = g
         self.b = b
         self.name = name

    def rgb(self):
        return [self.r, self.g, self.b]
    
    def __repr__(self):
        return "{0}, R: {1} G: {2} B: {3}".format(self.name, self.r, self.g, self.b)

class Red(Color):
    def __init__(self):
        super(Red, self).__init__('Red', 127, 0, 0)


class Blue(Color):
    def __init__(self):
        super(Blue, self).__init__('Blue', 0, 0, 127)


class Green(Color):
    def __init__(self):
        super(Green, self).__init__('Green', 0, 127, 0)


class Magenta(Color):
    def __init__(self):
        super(Magenta, self).__init__('Magenta', 127, 0, 127)


class Yellow(Color):
    def __init__(self):
        super(Yellow, self).__init__('Yellow', 127, 127, 0)


class Cyan(Color):
    def __init__(self):
        super(Cyan, self).__init__('Cyan', 0, 127, 127)


class White(Color):
    def __init__(self):
        super(White, self).__init__('White', 127, 127, 127)

class Blackout(Color):
    def __init__(self):
        super(Blackout, self).__init__('Blackout', 0, 0, 0)


RED      = Red()
GREEN    = Green()
BLUE     = Blue()
MAGENTA  = Magenta()
YELLOW   = Yellow()
CYAN     = Cyan()
WHITE    = White()
BLACKOUT = Blackout()

COLORS = [RED, GREEN, BLUE, MAGENTA, YELLOW, CYAN, WHITE]
