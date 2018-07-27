import numpy as np
from scipy.io import wavfile
from math import floor

fs = 44100
farr = [440.0]
N = 4
for i in range(1,N):
	farr.append(farr[i-1]*5/4)
t = 4

samples = np.linspace(0, t, int(fs*t), endpoint=False)
for f in farr:
	signal = np.sin(2 * np.pi * f * samples)
	signal *= 32767
	signal = np.int16(signal)

	filename = 'input/' + str(f) + 'hz.wav'
	wavfile.write(filename, fs, signal)
	print('File ' + filename + ' written.')


