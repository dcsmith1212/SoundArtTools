import numpy as np

# Constant power panning of mono signal into stereo
def pan_signal(signal, angle):
	left = np.sqrt(2)/2.0 * (np.cos(angle) - np.sin(angle)) * signal
	right = np.sqrt(2)/2.0 * (np.cos(angle) + np.sin(angle)) * signal
	return np.dstack((left,right))[0]