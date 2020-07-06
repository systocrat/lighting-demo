import time


class TimedCallback(object):
	def __init__(self, seconds: float, f, *args, **kwargs):
		self.seconds = seconds
		self.scheduled_at = time.monotonic()

		self.f = f
		self.stored_args = args
		self.stored_kwargs = kwargs

	def send(self):
		self.f(*self.stored_args, **self.stored_kwargs)


class TimerCallbackQueue(object):
	def __init__(self):
		self.callbacks = []

	def schedule(self, from_now: float, f, *args, **kwargs):
		self.callbacks.append(TimedCallback(
			from_now,
			f,
			*args,
			**kwargs
		))

	def runCallbacks(self):
		now = time.monotonic()

		tmp = []

		for i, callback in enumerate(self.callbacks):
			if (now - callback.scheduled_at) >= callback.seconds:
				callback.send()

				tmp.append(i)

		counter = 0

		for index in tmp:
			index -= counter

			del self.callbacks[index]

			counter += 1
