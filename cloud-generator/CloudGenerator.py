import numpy as np
from numpy import random as rand
from os import listdir
from scipy.io import wavfile
from scipy.signal import butter, lfilter, freqz
from bokeh.plotting import figure, output_file, show
from SignalWindowerer import SignalWindowerer
from AudioUtils import pan_signal

class CloudGenerator:
	def __init__(self):
		# Sampling frequency
		self.fs = 44100

		# Stores input signals
		self.signals = []
		
		# Low and high value of grain size uniform distribution
		self.minGrainSz = int(0.05 * self.fs)
		self.maxGrainSz = int(0.01 * self.fs)

		# Parameters for pan Gaussian
		self.panMean = 0
		self.panStd = 0.25

		# Parameter to geometric distribution for determining
		# when to start next grain after end of previous;
		# this value is the probability that we start the grain
		# at any given sample of audio
		self.probStartGrain = 0.0005

		# Number of output tracks for each input signal
		self.outputsPerInput = 1

		# Windowing function for grain envelope
		self.windowId = 'gaussian'
		self.wndwr = SignalWindowerer(self.windowId)

	def read_input_signals(self, input_dir):
		# Store all .wavs in current directory to a list of ndarrays
		for file in listdir(input_dir):
			if file.endswith(".wav"):
				_, signal = wavfile.read(input_dir + file)
				print(file + ' is of size ' + str(len(signal)))
				self.signals.append(signal)

		# Also create output ndarray of corresponding size
		# Length of output .wav in seconds
		tOut = 20
		self.nOut = tOut * self.fs

		# Output will contain outputPerInputs-many tracks for each
		# input signal
		self.outWavs = np.zeros((self.nOut, 2, self.outputsPerInput*len(self.signals)))

	def _extract_stereo_grain(self, sgnl):
		# Extract grain from input wav
		# Start location is uniform over entire wav, grain len is uniform over
		# predefined parameters
		sampleStart = int(rand.uniform(0, len(sgnl)))  # might cause OOB if sampleStart + sampleLen > len(sgnl)
		sampleEnd = int(sampleStart + rand.uniform(self.minGrainSz, self.maxGrainSz))
		grain = np.round(self.wndwr.signal_envelope(sgnl[sampleStart:sampleEnd]))

		# Pan mono signal with normally distributed angle
		angle = rand.normal(self.panMean, self.panStd)
		return pan_signal(grain, angle)

	def _write_output_wav(self, outFilename):
		# Add signals together and convert to 32-bit floating-point
		scaled = np.float32(self.outWavs / 32768.0)
		combined = np.sum(scaled, axis=2)
		combined = np.float32(combined / 4.0)

		# Write out to .wav file
		wavfile.write(outFilename, self.fs, combined)
		print('Number of grains: ' + str(self.grainCount))

	def cloudify_signals(self, outFilename):
		# Loop over each of the input signals
		self.grainCount = 0
		outputIter = 0
		for sgnl in self.signals:
			for _ in range(0, self.outputsPerInput):
				prevGrainEnd = 0
				while True:
					# Sample a grain from the signal and pan to stereo
					stereoGrain = self._extract_stereo_grain(sgnl)

					# Determine how far after end of previous grain to place next grain
					pauseLength = rand.geometric(self.probStartGrain)
					nextGrainStart = prevGrainEnd + pauseLength
					nextGrainEnd = nextGrainStart + len(stereoGrain)

					# Place the grain (if it is fully contained in the output wav size)
					if nextGrainEnd < self.nOut:
						self.grainCount += 1
						self.outWavs[nextGrainStart:nextGrainEnd, :, outputIter] = stereoGrain
						prevGrainEnd = nextGrainEnd
					else:
						break
				outputIter += 1

		self._write_output_wav()