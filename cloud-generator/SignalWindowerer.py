import numpy as np

#####################################################
### Windowing functions to control grain envelope ###
#####################################################

class SignalWindowerer:
	# If user doesn't give a windowing function, 
	# default Gaussian is used
	def __init__(self, windowId='gaussian'):
		self.windowFns = {'gaussian': self._gaussian_window,
			 			  'tukey':    self._tukey_window,
			 			  'triangle': self._triangle_window,
			 			  'sinc':	  self._sinc_window,
						  'expodec':  self._expodec_window,
						  'rexpodec': self._rexpodec_window,
						  'adsr':	  self._adsr_window}
		self.set_window_function(windowId)

	# All functions will be evaluated on the domain
	# [0,1] and have max value of 1 (to be multiplied
	# element-wise by signal

	def _gaussian_window(self, x):
		return np.exp(-np.power(x - 0.5, 2.) / (2 * np.power(1/6., 2.)))

	def _tukey_window(self, x):
		r = 0.7
		return np.piecewise(x, 
							[(x >= 0) & (x < r/2.), (x >= r/2.) & (x < 1-r/2.), (x >= 1-r/2.) & (x <= 1)],
							[lambda x: 0.5 * (1 + np.cos((2*np.pi/r)*(x - r/2.))),
							 1,
							 lambda x: 0.5 * (1 + np.cos((2*np.pi/r)*(x - 1 + r/2.)))])

	def _triangle_window(self, x):
		return np.piecewise(x, 
							[(x >= 0) & (x < 0.5), (x >= 0.5) & (x <= 1)],
							[lambda x: 2.*x,
							 lambda x: 2.*(1 - x)])

	def _sinc_window(self, x):
		return np.piecewise(x,
							[(x == 0.5), (x != 0.5)],
							[1, lambda x: np.sin(31.4*(x - 0.5)) / (31.4*(x - 0.5))])

	def _expodec_window(self, x):
		return np.exp(-4*x)

	def _rexpodec_window(self, x):
		return np.exp(-4*(1-x))

	# Emulates configurable synthesizer envelope pattern
	# Equations unabashedly pulled from https://www.desmos.com/calculator/nduy9l2pez
	def _adsr_window(self, x):
		xa = 0.1
		xd = 0.1
		ys = 0.5
		xs = 0.6
		xr = 0.1

		def ease(z,l,u):
			return np.power((z-l)/float(u-l), 3.) * (u-l) + l

		return np.piecewise(x,
							[(x >= 0) & (x <= xa), 
							 (x > xa) & (x <= xa+xd), 
							 (x > xa+xd) & (x <= xa+xd+xs),
							 (x > xa+xd+xs) & (x <= xa+xd+xs+xr)],
							[lambda x: np.power(x/float(xa), 1/3.),
							 lambda x: ease(((ys-1)/float(xd))*(x-xa) + 1, ys, 1),
							 ys,
							 lambda x: ease((-ys/float(xr))*(x-(xa+xd+xs)) + ys, 0, ys)])

	# Checks that user's input is a valid window function
	# and saves the selection for further use
	def set_window_function(self, windowId):
		try:
			self.windowFn = self.windowFns[windowId]
		except KeyError:
			print('Provide a valid window function name')
			raise

	# Applies given windowing function to the signal
	def signal_envelope(self, signal):
		return signal * self.windowFn(np.linspace(0, 1, len(signal)))

	# Utility for visualizing shape of ADSR envelope
	def plot_adsr(self):
		N = 50
		x = np.linspace(0,1,N)
		y = self._adsr_window(x)

		# output to static HTML file
		output_file("index.html", title="ADSR Envelope")

		# create a new plot with a title and axis labels
		p = figure(title="howdy ho neighbor!", x_axis_label='x', y_axis_label='y')

		# add a line renderer with legend and line thickness
		p.line(x, y, legend="Temp.", line_width=2)

		# show the results
		show(p)