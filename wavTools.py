from scipy.io import wavfile

def trimWav(signalIn,sampleRate,duration,startTime=0):
	startSample = startTime * sampleRate
	endSample = (duration * sampleRate) + startSample
	trimmedSignal = signalIn[startSample:endSample]
	return trimmedSignal

def reverseSignal(signalIn):
	revSignal = signalIn[:][::-1]
	return revSignal

# ##tone generator
# import numpy as np
# from scipy.io import wavfile
# from math import floor

# fs = 44100
# farr = [440.0]
# N = 4
# for i in range(1,N):
# 	farr.append(farr[i-1]*5/4)
# t = 4

# samples = np.linspace(0, t, int(fs*t), endpoint=False)
# for f in farr:
# 	signal = np.sin(2 * np.pi * f * samples)
# 	signal *= 32767
# 	signal = np.int16(signal)

# 	filename = 'input/' + str(f) + 'hz.wav'
# 	wavfile.write(filename, fs, signal)
# 	print('File ' + filename + ' written.')




##end tone generator

# directory = "audio/"
# filename = "beatles.wav"
# wavPath = directory + filename

# sampleRate, originalSignal = wavfile.read(wavPath)
# outWave = trimWav(originalSignal,sampleRate,duration=10)
# reverseSignal(outWave)
# wavfile.write(directory+"Rev"+filename,sampleRate,clippedWav)