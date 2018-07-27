from scipy.io import wavfile
from scipy import signal
import numpy as np

from bokeh.plotting import figure, show, output_file,curdoc
from bokeh.layouts import row, widgetbox, column
from bokeh.models import CustomJS, Slider, RangeSlider, ColumnDataSource, LinearColorMapper
from bokeh.models.widgets import Button, RadioButtonGroup, Div, Panel, Tabs
import sounddevice as sd

import time

class audioGetterer:
	"""A class to display, clip, and listen to wav files via a browser interface
	To run interactively, run following command from source directory:
		bokeh serve audioGetterer.py --show
		"""
	def __init__(self,filename="cats\\cats10_000.wav",index=0,showWindow = 0,showPlots = [1,0,0]):
		self.showPlots = showPlots
		self.colorIndex = index

		self.fileImported = 0
		self.heightPadding = 100
		self.figureHeight = 300
		self.figureWidth = 1600
		self.buttonWidth = 100
		self.buttonHeight = 100
		self.setupControls()

		self.gui = column(self.plotWindows(),self.getControls())
		self.gui.height = self.figureHeight+self.heightPadding #add room for the controls and tabs

		self.importFile(filename)

		if showWindow:
			show(self.gui)
			curdoc().add_root(self.gui)

	def writeFileButtonCallback(self):
		"""Writes the active timespan to a file named 'audioGetterOut.wav' """
		print "Writing wav file..."
		wavfile.write('./audioGetterOut.wav', self.sampleRate, np.asarray(self.signal))

	def resetButtonCallback(self):
		"""Resets the tool back to how it was the moment after the file was imported"""
		print 1

	def updateButtonCallback(self):
		"""Called on click of the update button, sets new max and min times to clip master audio by"""
		self.updateSignalInfo()
		self.updateGui()

	def setupControls(self):
		"""Called on setup, creates buttons and sliders to:
			open a local audio file
			update the active timespan
			play the active timespan
		"""
		self.fileButtonSetup()

		#double ended slider to clip audio
		self.timeWindowSlider = RangeSlider(start=0, end=1, value=[0,1], step=.05,title="Wav File Window",width = self.figureWidth)
		self.timeWindowSlider.on_change("value",self.timeSliderCallback)
		self.timeSliderUpdateIndex = 0 #set up an update index so the slider doesn't update too often

		#button to play windowed audio sample
		self.playButton = Button(label="Play", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.playButton.on_click(self.playSound)

		self.updateButton = Button(label="Update", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.updateButton.on_click(self.updateButtonCallback)

		self.writeFileButton = Button(label="Write Active File", button_type="success",width=self.buttonWidth, height = self.buttonHeight)
		self.writeFileButton.on_click(self.writeFileButtonCallback)

		self.resetButton = Button(label="Reset", button_type="success",width=self.buttonWidth,height=self.buttonHeight)
		self.resetButton.on_click(self.resetButtonCallback)		

	def importFile(self,filename):
		self.sampleRate, self.originalSignal = wavfile.read(filename) #keep the original for master reference
		self.originalSignalDuration = len(self.originalSignal)/float(self.sampleRate) #full audio duration in seconds

		self.timeWindowSlider.end = self.originalSignalDuration #update the max value of the time control slider
		self.timeWindowSlider.value = (0,self.originalSignalDuration)

		self.fileImported = 1

		self.updateSignalInfo()
		self.updateGui()

	def updateSignalInfo(self):
		"""Uses the values set by the time slider to clip the imported audio at the start and end"""
		newTimeRange = self.timeWindowSlider.value
		self.startSample = int(newTimeRange[0] * self.sampleRate)
		self.endSample = int(newTimeRange[1] * self.sampleRate)

		self.numSamples = self.endSample - self.startSample
		self.signal = self.originalSignal[self.startSample:self.endSample]
		self.ts = range(self.numSamples)

		self.updateGui()


	def getButtons(self):
		"""Returns a bokeh column object of the tool's buttons:
			import file button
			update button
			play button
			write file button
			reset button
		"""
		buttonColumn = column(self.importFileButton,self.updateButton,self.playButton,self.writeFileButton,self.resetButton,width=self.buttonWidth,height=self.figureHeight)
		return buttonColumn

	def getControls(self):
		"""Returns a bokeh row object containing:
			import file button
			update time window button
			play active time window button
			lo/hi time slider
		"""
		return self.timeWindowSlider
		# controlsRow = row(self.importFileButton,self.updateButton,self.playButton,self.timeWindowSlider,width=self.figureWidth,height=10)#,sizing_mode="scale_width")
		# return controlsRow

	def fileCallback(self,attr,old,new):
		"""Callback assigned to choosing a file from the file browser"""
		filename =  new['file_name'][0]
		self.importFile('cats\\'+filename)

	def fileButtonSetup(self):
		"""Creates a "File opener" button and assigns a javascript callback to it that opens an os-independent file picker window
		imports chosen file into the class"""
		fileSource = ColumnDataSource({'file_name':[]})

		self.importFileButton = Button(label="Upload", button_type="success",width=self.buttonWidth)

		self.importFileButton.callback = CustomJS(args=dict(file_source=fileSource), code = """
		function read_file(filename) {
		    var reader = new FileReader();
		    reader.onload = load_handler;
		    reader.onerror = error_handler;
		    // readAsDataURL represents the file's data as a base64 encoded string
		    reader.readAsDataURL(filename);
		}

		function load_handler(event) {
		    file_source.data = {'file_name':[input.files[0].name]};
		    file_source.trigger("change");
		}

		function error_handler(evt) {
		    if(evt.target.error.name == "NotReadableError") {
		        alert("Can't read file!");
		    }
		}

		var input = document.createElement('input');
		input.setAttribute('type', 'file');
		input.onchange = function(){
		    if (window.FileReader) {
		        read_file(input.files[0]);
		    } else {
		        alert('FileReader is not supported in this browser');
		    }
		}
		input.click();
		""")

		fileSource.on_change('data', self.fileCallback)

	def playSound(self):
		"""Callback for the playSound button, uses the native sound device to play the clipped audio file through speakers"""
		sd.play(self.signal, self.sample_rate,blocking=True)

	def getFileByTimeRange(self,startTime,endTime):
		"""Queries master audio file and returns only those samples between start and end time, provided in float seconds"""
 		startIndex = int(startTime * self.sample_rate)
 		endIndex = int(endTime * self.sample_rate)
 		return self.originalSignal[startIndex:endIndex]

	def getFileByIndexRange(self,startIndex,endIndex):
		"""Queries master audio file and returns samples between start and ending index, provided in int sampleNumber"""
 		startIndex = int(startTime * self.sample_rate)
 		endIndex = int(endTime * self.sample_rate)
 		return self.originalSignal[startIndex:endIndex]

	def getWaveform(self):
		"""Plots the active audio in the time domain, returns a figure object"""
		colors = ["red","green","blue","purple"]
		waveformPlot = figure(height = self.figureHeight,width = self.figureWidth,toolbar_location=None)#,x_range = (0,len(movedSignal)))
		waveformPlot.line(self.ts,self.signal,color=colors[self.colorIndex])

		waveformPlot.line([self.startSample,self.startSample],[-5000,5000])
		waveformPlot.line([self.endSample,self.endSample],[-5000,5000])

		return waveformPlot

	def timeSliderCallback(self,attr,old,new):
		"""Called on change of the time slider, sets new max and min times to clip master audio by, but doesn't actually update the audio (too slow)
		Moves start/stop lines on waveform plot"""
		self.timeSliderUpdateIndex+=1
		if self.timeSliderUpdateIndex > 10:
			self.timeSliderUpdateIndex = 0
			self.updateGui()

	def plotWindows(self):
		"""Returns a figure containing the following possible windows, determined by the value of "showPlots" passed upon creation
			showPlots[0] = waveform plot
			showPlots[1] = spectrogram plot
			showPlots[2] = fft plot
		"""
		if self.fileImported == 0: #if no file to read, just create a blank window
			return figure(height = self.figureHeight,width = self.figureWidth,x_range = (0,1),y_range=(0,1))

		plotLabels = ["Waveform","Spectrogram","FFT"]
		plotFunctions = [self.getWaveform,self.getSpectrogram,self.getFFT]

		panelList = []

		for plotIndex,showPlot in enumerate(self.showPlots):
			if showPlot:
				plotWindow = plotFunctions[plotIndex]()
				plotTab = Panel(child=plotWindow,title = plotLabels[plotIndex])
				panelList.append(plotTab)

		tabs = Tabs(tabs=panelList)

		window = row(self.getButtons(),tabs,height = self.figureHeight,width=self.figureWidth+self.buttonWidth)#,sizing_mode="scale_width")
		return window

	def getSpectrogram(self):
		"""Plots a log spectrogram of the active audio, returns figure object"""
		freqs,times,data = self.log_specgram(self.signal,self.sample_rate)
		spectrogramPlot = figure(height = self.figureHeight,width = self.figureWidth,x_range = (0,max(times)),y_range=(0,max(freqs)),toolbar_location=None)
		spectrogramPlot.image(image=[data], x=0, y=0, dw=max(times), dh=max(freqs), palette="Spectral11")
		return spectrogramPlot

	def log_specgram(self,audio, sample_rate, window_size=20, step_size=10, eps=1e-10):
		"""Kraggin log spectrogram useful for MFCC analysis"""
		nperseg = int(round(window_size * sample_rate / 1e3))
		noverlap = int(round(step_size * sample_rate / 1e3))
		freqs, times, spec = signal.spectrogram(audio,
		                                fs=sample_rate,
		                                window='hann',
		                                nperseg=nperseg,
		                                noverlap=noverlap,
		                                detrend=False)
		return freqs, times, np.log(spec.T.astype(np.float32) + eps)

	def getFFT(self):
		"""Plots the fast fourier transform of the active audio, returns a figure object"""
		sigPadded = self.signal
		# Determine frequencies
		f = np.fft.fftfreq(self.numSamples) * self.sample_rate
		#pull out only positive frequencies (upper half)
		fHalf = f[:len(f)/2]
		# Compute power spectral density
		psd = np.abs(np.fft.fft(sigPadded))**2 / self.numSamples
		#pull out only power densities for the positive frequencies
		psdHalf = psd[:len(psd)/2]

		fftPlot = figure(height = self.figureHeight,width = self.figureWidth,toolbar_location=None)#x_range = (0,len(movedSignal)))
		fftPlot.line(fHalf,psdHalf)

		return fftPlot

	def updateGui(self):
		"""Called upon changing any of the parameters, update the main plot window, the controls row, and button column"""
		self.gui.children[0] = self.plotWindows()
		self.gui.children[1] = self.getControls()

help(audioGetterer)


import os
import numpy as np
import timeDrawer

class multiAudioSplicer:

	def __init__(self,numFiles):
		self.signals = []
		sourceList = []
		for fileInd in range(1,1+numFiles):

			audioGetterer(showWindow=0,showPlots=[1,0,0])
			sourceList.append(audioGetter.gui)

			self.fs = audioGetter.sample_rate
			self.signals.append(audioGetter.signal)

		self.sourceColumn = column(sourceList)

		self.minSgnl = np.inf
		for sgnl in self.signals:
			if len(sgnl) < self.minSgnl:
				self.minSgnl = len(sgnl)

	def splitAudio(self,grainSizes):

		interleavedSignal = []

		grainSizes = [i * 3000 for i in [3, 5, 10, 0, 8, 9, 0, 2, 5, 6, 3, 7, 6, 0, 0, 3, 4, 7, 5, 3, 4, 3]]
		timeMarker = 0
		currSgnl = 0

		for gSz in grainSizes:
			# print('Grain size: ' + str(gSz))
			# print('timeMarker: ' + str(timeMarker))

			sgnl = self.signals[currSgnl]
			grain = sgnl[timeMarker:timeMarker+gSz]
			interleavedSignal.extend(grain)
			currSgnl = (currSgnl + 1) % len(self.signals)
			timeMarker += gSz
			# print('New timeMarker: ' + str(timeMarker))
			if timeMarker > self.minSgnl:
				break

		print('Size of interleaved wav: ' + str(len(interleavedSignal)))
		wavfile.write('./interleaved.wav', self.fs, np.asarray(interleavedSignal))

		compositeAudio = audioGetterer('interleaved.wav',showWindow=1).gui
		# timeDraw = timeDrawer.timeDrawer().gui
		spacer = Div(text=" ",)

		# self.compositeColumn = column(compositeAudio)#,timeDraw)
		self.guiRow = column(self.sourceColumn,compositeAudio)#,spacer,self.compositeColumn,width=1400)
		show(self.guiRow)
		curdoc().add_root(self.guiRow)

# multiAudioSplicer(2).splitAudio(2)
# audioGetterer(1)

# audioGetterer(showWindow=1,showPlots=[1,0,0])