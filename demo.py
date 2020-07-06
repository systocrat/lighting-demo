import pygame as pg
import typing
from operator import itemgetter
from timer import TimerCallbackQueue
import math
import random
import colorsys

SCREENRECT = pg.Rect(0, 0, 640, 480)

PYLON_LIGHT_EVENT = pg.USEREVENT + 1


class Circle(object):
	def __init__(self, x, y, radius):
		self.x = x
		self.y = y
		self.radius = radius

	def collidespoint(self, x, y):
		_x = self.x - x
		_y = self.y - y

		dist = math.sqrt((_x * _x) + (_y * _y))

		return dist < self.radius


class PylonFade(object):
	def __init__(self, pylon, queue, full_fade_time: float):
		self.pylon = pylon
		self.queue = queue

		self.full_fade_time = full_fade_time

		self.original_color = self.pylon.saveColor()

		self.limit = (0, 1)

		_, l, _ = colorsys.rgb_to_hls(*self.original_color)

		self.start = l
		self.end = 0

	def tick(self, diff):
		t = self.limit[0] * (1 - diff) + self.limit[1] * diff
		t /= self.full_fade_time

		if t < 0.5:
			return 2 * t * t

		return (-2 * t * t) + (4 * t) - 1
	

class Pylon(object):
	def __init__(self, x: int, y: int, size: float, color: typing.Tuple[int, int, int]):
		self.x = x
		self.y = y
		self.size = size

		self.box = pg.Rect(self.x, self.y, size * 2, size * 2)

		self.r, self.g, self.b = color

		self.has_color_event = False

	def setColor(self, r, g, b):
		self.r = r
		self.g = g
		self.b = b

	def saveColor(self):
		return self.r, self.g, self.b

	def dist(self, pylon):
		dx = (self.x - pylon.x)
		dy = (self.y - pylon.y)

		dist = math.sqrt((dx * dx) + (dy * dy))

		return dist


class PylonJumpTrigger(object):
	def __init__(self, pylons: 'Pylons', origin: Pylon):
		self.pylons = pylons
		self.origin = origin

		self.pylon_list = self.pylons.pylons[::]
		random.shuffle(self.pylon_list)

		self._visited = {self.origin}

	def enablePylon(self, pylon: Pylon):
		r, g, b = pylon.saveColor()

		nr, ng, nb = tuple([random.randint(1, 255) for _ in range(3)])

		pylon.setColor(nr, ng, nb)
		pylon.has_color_event = True

		self.pylons.queue.schedule(.05, self.disablePylon, pylon, r, g, b)

	def disablePylon(self, pylon: Pylon, r, g, b):
		pylon.setColor(r, g, b)
		pylon.has_color_event = False

	def start(self):
		self.enablePylon(self.origin)
		self.trigger_closest(self.origin)

	def trigger_closest(self, current_origin: Pylon, max_jump: int = 3, iterations=0):
		iterations += 1

		lowest = []

		all_distances = [
			(p, p.dist(current_origin)) for p in self.pylons.pylons if p != self.origin and p not in self._visited
		]

		if not all_distances:
			return

		all_distances.sort(key=itemgetter(1))

		for pylon, dist in all_distances:
			lowest.append(pylon)

			if len(lowest) >= max_jump:
				break

		for low in lowest:
			self._visited.add(low)
			self.pylons.queue.schedule(iterations * .05, self.enablePylon, low)

		for low in lowest:
			self.trigger_closest(low, max_jump=max_jump, iterations=iterations)


class Pylons(object):
	def __init__(self, queue: TimerCallbackQueue):
		self.pylons: typing.List['Pylon'] = []
		self.queue = queue

	def draw(self, surface):
		for pylon in self.pylons:
			pg.draw.circle(surface, (pylon.r, pylon.g, pylon.b), (pylon.x, pylon.y), pylon.size)

	def onLeftClick(self, x, y):
		self.pylons.append(Pylon(x, y, 5, (100, 100, 100)))

	def _setPylonColor(self, pylon, r, g, b):
		pylon.r, pylon.g, pylon.b = (r, g, b)
		pylon.has_color_event = False

	def onRightclick(self, x, y):
		for pylon in self.pylons:
			if pylon.box.collidepoint(x, y) and not pylon.has_color_event:
				pylon.has_color_event = True
				pj = PylonJumpTrigger(self, pylon)
				pj.start()


def main(winstyle=1):
	pg.init()

	bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
	screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

	clock = pg.time.Clock()

	timer_queue = TimerCallbackQueue()
	pylons = Pylons(timer_queue)

	while True:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				return
			if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
				return

			if event.type == pg.MOUSEBUTTONDOWN:
				if event.button == pg.BUTTON_LEFT:
					pylons.onLeftClick(*event.pos)
				elif event.button == pg.BUTTON_RIGHT:
					pylons.onRightclick(*event.pos)

		timer_queue.runCallbacks()

		pylons.draw(screen)

		pg.display.update((0, 0, 640, 480))

		clock.tick(40)


if __name__ == '__main__':
	main()
