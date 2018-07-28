import os
import numpy as np
from scipy.io import wavfile
from math import floor
from numpy import random as rand
from scipy.signal import butter, lfilter, freqz
from bokeh.plotting import figure, output_file, show

def gaussian_window(x):
	return np.exp(-np.power(x - 0.5, 2.) / (2 * np.power(1/6., 2.)))

def tukey_window(x):
	r = 0.7
	return np.piecewise(x, 
											[(x >= 0) & (x < r/2.), (x >= r/2.) & (x < 1-r/2.), (x >= 1-r/2.) & (x <= 1)],
											[lambda x: 0.5 * (1 + np.cos((2*np.pi/r)*(x - r/2.))),
											 1,
											 lambda x: 0.5 * (1 + np.cos((2*np.pi/r)*(x - 1 + r/2.)))])

def triangle_window(x):
	return np.piecewise(x, 
											[(x >= 0) & (x < 0.5), (x >= 0.5) & (x <= 1)],
											[lambda x: 2.*x,
											 lambda x: 2.*(1 - x)])

def sinc_window(x):
	return np.piecewise(x,
											[(x == 0.5), (x != 0.5)],
											[1, lambda x: np.sin(31.4*(x - 0.5)) / (31.4*(x - 0.5))])

def expodec_window(x):
	return np.exp(-4*x)

def rexpodec_window(x):
	return np.exp(-4*(1-x))

def adsr_window(x):
	xa = 0.1
	xd = 0.1
	ys = 0.5
	xs = 0.6
	xr = 0.1

	def g1(z,l,u):
		return np.power(float(z-l)/float(u-l), 1/3.) * (u-l) + l

	def g2(z,l,u):
		return np.power((z-l)/float(u-l), 3.) * (u-l) + l

	return np.piecewise(x,
											[(x >= 0) & (x <= xa), 
											 (x > xa) & (x <= xa+xd), 
											 (x > xa+xd) & (x <= xa+xd+xs),
											 (x > xa+xd+xs) & (x <= xa+xd+xs+xr)],
											[lambda x: np.power(x/float(xa), 1/3.),
											 lambda x: g2(((ys-1)/float(xd))*(x-xa) + 1, ys, 1),
											 ys,
											 lambda x: g2((-ys/float(xr))*(x-(xa+xd+xs)) + ys, 0, ys)])

def signal_envelope(signal, windowId):
	windowFns = {'gaussian': gaussian_window,
							 'tukey':    tukey_window,
							 'triangle': triangle_window,
							 'sinc':		 sinc_window,
							 'expodec':	 expodec_window,
							 'rexpodec': rexpodec_window,
							 'adsr':		 adsr_window}
	try:
		return signal * windowFns[windowId](np.linspace(0, 1, len(signal)))
	except KeyError:
		print('Provide a valid window function name')
		raise

# Constant power panning of mono signal into stereo
def pan_signal(signal, angle):
	left = np.sqrt(2)/2.0 * (np.cos(angle) - np.sin(angle)) * signal
	right = np.sqrt(2)/2.0 * (np.cos(angle) + np.sin(angle)) * signal
	return np.dstack((left,right))[0]	

def main():
	fs = 44100
	signals = []

	# Store all .wavs in current directory to a list of ndarrays
	for file in os.listdir('../input/'):
		if file.endswith(".wav"):
			_, signal = wavfile.read('../input/' + file)
			print(file + ' is of size ' + str(len(signal)))
			signals.append(signal)

	### Parameters for distributions
	# Low and high value of grain size uniform distribution
	minGrainSz = int(0.05 * fs)
	maxGrainSz = int(0.01 * fs)

	# Parameters for pan Gaussian
	panMean = 0
	panStd = 0.25

	# Parameter to geometric distribution for determining
	# when to start next grain after end of previous;
	# this value is the probability that we start the grain
	# at any given sample of audio
	probStartGrain = 0.0005

	### Initialize output .wav
	# Length of output .wav in seconds
	tOut = 20
	nOut = tOut * fs
	#outWav = [np.int16(0)] * nOut
	outWavs = np.zeros((nOut, 2, len(signals)))

	grainCount = 0
	for i, sgnl in enumerate(signals):
		prevGrainEnd = 0
		while True:	
			# Extract grain from input wav
			# Start location is uniform over entire wav, grain len is uniform over
			# predefined parameters
			sampleStart = int(rand.uniform(0, len(sgnl))) # might cause OOB if sampleStart + sampleLen > len(sgnl)
			sampleEnd = int(sampleStart + rand.uniform(minGrainSz, maxGrainSz))
			grain = np.round(signal_envelope(sgnl[sampleStart:sampleEnd], 'asdr'))


			# Apply random panning to grain	
			angle = rand.normal(panMean, panStd)
			stereoGrain = pan_signal(grain, angle)

			# Determine how far after end of previous grain to place next grain
			pauseLength = rand.geometric(probStartGrain)
			nextGrainStart = prevGrainEnd + pauseLength
			nextGrainEnd = nextGrainStart + len(grain)

			if nextGrainEnd < nOut:
				grainCount += 1
				outWavs[nextGrainStart:nextGrainEnd, :, i] = stereoGrain
				prevGrainEnd = nextGrainEnd
			else:
				break

	print(np.shape(outWavs))

	scaled = np.float32(outWavs / 32768.0)

	print('max: ' + str(np.max(scaled)))
	combined = np.sum(scaled, axis=2)
	combined = np.float32(combined / 4.0)

	print(np.shape(combined))

	print('max: ' + str(np.max(combined)))

	wavfile.write('./cloud.wav', fs, combined)
	print('Number of grains: ' + str(grainCount))

main()

N = 50
x = np.linspace(0,1,N)
y = adsr_window(x)

# output to static HTML file
output_file("index.html", title="line plot example")

# create a new plot with a title and axis labels
p = figure(title="howdy ho neighbor!", x_axis_label='x', y_axis_label='y')

# add a line renderer with legend and line thickness
p.line(x, y, legend="Temp.", line_width=2)

# show the results
show(p)

