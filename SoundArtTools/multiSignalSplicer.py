import numpy as np
import os

from bokeh.plotting import figure, show, curdoc, output_file
from bokeh.layouts import row, column
from bokeh.models.widgets import Button, TextInput, RangeSlider, Toggle, CheckboxButtonGroup, RadioButtonGroup, Div

from chunkDrawer import chunkDrawer

from audioLogger import audioLogger
logger = audioLogger()

class signalSplicerControls:

	def __init__(self):

		logger.logData(source="Splicer tools",priority="INFO",msgType="Setup start",msgData=())

		self.buttonHeight = 100
		self.buttonWidth = 200
		self.spliceButton = Button(label="Splice", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.resetButton =  Button(label="Reset", button_type="success",width=self.buttonWidth,height = self.buttonHeight)

		self.buttonRow = row(self.spliceButton,self.resetButton)
		self.chunkDrawer = chunkDrawer()

		self.gui = column(self.chunkDrawer.gui,self.buttonRow)

		logger.logData(source="Splicer tools",priority="INFO",msgType="Setup done",msgData=())

	def showGui(self):
		show(self.gui)

from signalHandler import signalHandler

class multiSignalSplicer:

	def __init__(self,signalFilenames = []):
		logger.logData(source="Master splicer",priority="INFO",msgType="Setup start",msgData=())

		self.signalColors = ["green","red","purple","blue","orange"]
		self.setupAudioSources(signalFilenames)

		sinkColor = "black"
		self.audioSink = signalHandler(color=sinkColor)

		self.splicerControls = signalSplicerControls()
		self.splicerControls.spliceButton.on_click(self.spliceCallback)
		self.splicerControls.resetButton.on_click(self.resetCallback)
		self.setupGUI()
		self.grainSizes = [i * 1000 for i in [3, 5, 10, 0, 8, 9, 0, 2, 5, 6, 3, 7, 6, 0, 0, 3, 4, 7, 5, 3, 4, 3]]

		logger.logData(source="Master splicer",priority="INFO",msgType="Setup done",msgData=())

	def setupAudioSources(self,signalFilenames):
		self.audioSources = []
		if len(signalFilenames) > 1:
			for signalIndex,signalFilename in enumerate(signalFilenames):
				audioSource = signalHandler(signalFilename = signalFilename,color=self.signalColors[signalIndex]) 
				self.audioSources.append(audioSource)

		else:
			self.audioSources = [signalHandler(),signalHandler()]

		self.numSources = len(self.audioSources)

	def resetCallback(self):
		self.splicerControls.chunkDrawer.resetChunkLengths()

	def spliceCallback(self):
		logger.logData(source="Master splicer",priority="INFO",msgType="Splice",msgData=())

		self.updateSourceSignals()

		chunkTimes = self.splicerControls.chunkDrawer.getLastChunks()

		grainSizeToTimeRatio = self.minSgnl/sum(chunkTimes)
		self.grainSizes = [int(grainSizeToTimeRatio*chunkTime) for chunkTime in chunkTimes]

		self.splitAudio()

		logger.logData(source="Master splicer",priority="INFO",msgType="Splice complete",msgData=())

	def updateSourceSignals(self):
		self.signals = []
		self.colorPallete = []

		for audioSource in self.audioSources:
			self.colorPallete.append(audioSource.color)

			#get just the first channel for now
			self.signals.append(list(audioSource.signal[:,0]))

		self.minSgnl = np.inf
		for sgnl in self.signals:
			if len(sgnl) < self.minSgnl:
				self.minSgnl = len(sgnl)

	def setupGUI(self):
		sourceGuiList = [signalSource.gui for signalSource in self.audioSources]

		sourceGuiColumn = column(sourceGuiList)
		topControls = row(sourceGuiColumn,self.splicerControls.gui)
		self.gui = column(topControls,self.audioSink.gui)

	def showGui(self):
		output_file(os.path.join("webpages","multiSignalSplicer.html"))

		logger.logData(source="Master splicer",priority="INFO",msgType="Show",msgData=())
		show(self.gui)
		curdoc().add_root(self.gui)

	def splitAudio(self):
		interleavedSignal = []
		allTimes = []
		allColors = []

		timeMarker = 0
		currSgnl = 0

		for gSz in self.grainSizes:
			#get current signal by index
			sgnl = self.signals[currSgnl]

			grain = sgnl[timeMarker:timeMarker+gSz]
			interleavedSignal += grain

			times = range(timeMarker,timeMarker+gSz)
			allTimes += times

			#color index
			color = [currSgnl]*gSz
			allColors += color


			currSgnl = (currSgnl + 1) % self.numSources

			timeMarker += gSz
			# print('New timeMarker: ' + str(timeMarker))
			if timeMarker > self.minSgnl:
				break

		sampleRate = self.audioSources[0].sampleRate
		# self.audioSink.plotStyle = 1

		self.audioSink.addSignal(interleavedSignal,sampleRate)
		self.audioSink.updateMapperHigh(self.numSources)

		self.audioSink.updateColorBar(allColors)
		self.audioSink.updateMapperPalette(self.colorPallete)

def testSignalSplicer():
	signalFilenames = ["cats_000.wav","cats_001.wav","2ch.wav"]
	# signalFilenames = ["ClipBad romance.wav","ClipRubber biscuit.wav","ClipFly me to the moon.wav"]

	mAs = multiSignalSplicer(signalFilenames)
	mAs.showGui()

# testSignalSplicer()