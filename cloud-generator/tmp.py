import numpy as np

def gaussian(x, mu, sigma):
	return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sigma, 2.)))

print(gaussian(np.linspace(-3, 3, 20), 0, 1))