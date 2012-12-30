class ModCounter:
	def __init__(self, mod):
		self.mod = mod
		self.i = 0

	def reset(self):
		self.i = 0

	def set(self, amount):
		self.i = amount % self.mod

	def __add__(self, amount):
		self.i = (self.i + amount) % self.mod
		return self

	def __sub__(self, amount):
		self.i = (self.i - amount) % self.mod
		return self

	def __repr__(self):
		return "mod i: " + str(self.i)

	def __eq__(self, value):
		return self.i == value
