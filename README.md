# SoundArtTools

Collection of tools to do sample level mixing of audio signals

## Requirements:
	python3 (probably works on python 2)

### Libraries:
	bokeh
	scipy
	numpy
	colorama
	sounddevice
	time
	os
	srt

### To install all requirements:
	pip install --user bokeh,scipy,numpy,colorama,sounddevice,srt

### Confirmed working setups:
* Windows 10, python 3.7.0, Firefox

Tool must be run via bokeh server to function.  Tool to use is chosen via command line arguments and (optional) filenames are passed in after tool name.

Eg to run the rearranger with an empty source, cd into soundArtTools directory and run:

	bokeh serve soundArtTools.py --show --args Rearranger

Eg to run the Splicer with two audio sources, cd into soundArtTools directory and run:

	bokeh serve soundArtTools.py --show --args Splicer Yankee.wav Cats.wav


# Tools available:

## Player - Base tool 

### Capable of being a source or sink of audio files
* load in audio by filename
* direct signal import from another tool
* export signal to another tool
* save active signal to wav file

### Displays waveform, FFT, and spectrogram of signal
* allows zooming on each
* Displays "continuity" of current signal

### Operations on signal
* Allows playing, pausing, looping of audio
* Allows enabling of only specific channels
* Trim audio via slider

### Integrated with lyrics for easier trimming
* Allows importation of .srt files
* Allows seleting start/end lyric to set trim time bounds

## Splicer - tool to mesh together multiple signals
Uses chunk drawer - a way to choose which signal is active at times

### Operates on N+1 audioHandlers and 1 time drawer:
* N sources
* 1 sink

## Signal shuffler - A tool to switch around samples within a signal

### Operates on an 2 audioHandlers:
* 1 sink
* 1 source

### Supports setting of
* Percentage of signal to disturb
* Max grain size
* Min grain size
* Grain size standard deviation
* Grain shift average

### Populates audioHandler sink with output file
* Displays continuity of output signal in colorbar


# Auxillary Tools:

## Logger

### Outputs relevant logs to the console and text file with following info:
* Severity
* Timestamp
* Source
* Message

## Chunk Tool

### Uses mouse position to set chunk window lengths
* How it works
	A vertical line is drawn at t=0
	The yVal at which this line is crossed determines the chunk length of the next chunk
	A new vertical line is drawn at t=yVal, representing the  timestamp at which the _next_ chunk will begin
	The yVal at which this line is crossed determines the chunk length of the next chunk.
	Repeat

* Supports time or sample units
* Supports skipping signals by setting yVal<0
* Supports full signal delineation or partial signal with periodic expansion


## To do:

### General:
* improve memory efficiency
* use JS callbacks
* identify way to couple channels
* Add gifs
* Add sample audio with parameters
* License

### Player:
* improve scroll along

### Splicer:
* enable channel coupling

### Shuffler:
* reverse chunks of the wave based on probability

### Chunk drawer:
* seamless between sample and time mode
* log/lin y axis

### Streaming Audio:
* Generate web interface
* Seed + modify

### Cloud Generator:
* ~~Vectorize ADSR (needs to work with numpy arrays)~~
* ~~Replace envelope with eval~~
* Classify
  
### Grain Shuffler:
* Classify
