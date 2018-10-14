import numpy as np
from scipy.io import wavfile
from math import floor
from numpy import random as rnd
from scipy.signal import butter, lfilter, freqz

# Definte lowpass filter
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

# Break original signal into grains of random size
def granularize_signal(wav, minGrainSz, modeGrainSz, maxGrainSz):
	sampleMarker = 0
	grainMarkers = []
	numSamples = len(wav)
	while sampleMarker < numSamples:
		grainSz = floor(rnd.triangular(minGrainSz, modeGrainSz, maxGrainSz))
		grainMarkers.append([int(sampleMarker), int(sampleMarker+grainSz)])
		sampleMarker = sampleMarker + grainSz
	return grainMarkers

# Shuffle grains using a Gaussian offset and write file
def shuffle_grains(wav,grainMarkers, pctToShift,standardDev):
	for grainIdx, grain in enumerate(grainMarkers):
		if rnd.uniform(0,1) < pctToShift:
			shift = int(rnd.normal(0, standardDev))
			del grainMarkers[grainIdx]
			grainMarkers.insert(grainIdx+shift, grain)
		
	granularizedWav = []
	for grain in grainMarkers:
		grainStart = grain[0]
		grainEnd = grain[1]
		granularizedWav.extend(wav[grainStart:grainEnd])

	return np.asarray(granularizedWav)

	# wavfile.write('./granularized.wav', fs, np.asarray(granularizedWav))
	# print('Granularized .wav file written')

# fs, wav = wavfile.read('cats\\cats10_000.wav')

# minGrainSz = int(1e-4 * fs)
# maxGrainSz = int(1e-1 * fs)
# modeGrainSz = int(10*minGrainSz)
# grainMarkers = granularize_signal(wav, minGrainSz, modeGrainSz, maxGrainSz)

# # print grainMarkers

# pctToShift = 0.3
# fs, newWav = shuffle_grains(grainMarkers, pctToShift)

# # print newWav