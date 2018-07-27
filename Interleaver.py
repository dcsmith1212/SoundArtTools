import numpy as np
from scipy.io import wavfile
import os

fs = 44100
signals = []

# Store all .wavs in current directory to a list of ndarrays
for file in os.listdir('./input/'):
	if file.endswith(".wav"):
		_, signal = wavfile.read('./input/' + file)
		print(file + ' is of size ' + str(len(signal)))
		signals.append(signal)

if len(signals) == 0:
	print('No input files...')

minSgnl = np.inf
for sgnl in signals:
	if len(sgnl) < minSgnl:
		minSgnl = len(sgnl)
print('minSgnl: ' + str(minSgnl))

interleavedSignal = []
grainSizes = [i * 3000 for i in [3, 5, 10, 0, 8, 9, 0, 2, 5, 6, 3, 7, 6, 0, 0, 3, 4, 7, 5, 3, 4, 3]]
timeMarker = 0
currSgnl = 0
for gSz in grainSizes:
	print('Grain size: ' + str(gSz))
	print('timeMarker: ' + str(timeMarker))
	sgnl = signals[currSgnl]
	grain = sgnl[timeMarker:timeMarker+gSz]
	interleavedSignal.extend(grain)
	currSgnl = (currSgnl + 1) % len(signals)
	timeMarker += gSz
	print('New timeMarker: ' + str(timeMarker))
	if timeMarker > minSgnl:
		break

print('Size of interleaved wav: ' + str(len(interleavedSignal)))
wavfile.write('./interleaved.wav', fs, np.asarray(interleavedSignal))
print('interleaved.wav written')