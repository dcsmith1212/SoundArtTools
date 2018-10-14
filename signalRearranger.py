from scipy.stats import norm
import numpy as np
import os

from bokeh.plotting import figure, show, curdoc, output_file
from bokeh.layouts import row, column
from bokeh.models import Slider, RangeSlider
from bokeh.models.widgets import Button, RadioButtonGroup, Div

from audioLogger import audioLogger
logger = audioLogger()

class rearrangerControls:
	"""Class to move around an audio file"""
	def __init__(self):
		logger.logData(source="Rearranger tools",priority="INFO",msgType="Setup start",msgData=())

		self.setupVariables()
		self.setupPlots()

		logger.logData(source="Rearranger tools",priority="INFO",msgType="Setup done",msgData=())

	def showGUI(self):
		show(self.gui)
		curdoc().add_root(self.gui)

	def setupVariables(self):
		#dummy values until tool is used

		self.pctToShift = 0.6
		self.shiftStandardDev = 10
		self.shiftMean = 0
		self.startSample = 0

		self.minGrainSz = 0
		self.maxGrainSz = 10
		self.modeGrainSz = 5

		self.sliderWidth = 400
		self.toolWidth = 1000
		self.subplotSize = 300
		
	#GUI CALLBACKS
	def grainSizeSliderCallback(self,attr,old,new):
		newMin = new[0]
		newMax = new[1]

		self.minGrainSz = int(newMin)
		self.maxGrainSz = int(newMax)
		self.modeGrainSz = int(.5* (self.minGrainSz + self.maxGrainSz))

		grainSizePDF = self.maxSamplePlot.select_one({'name': 'sampleSizePDF'})

		numPoints = 10
		chunkSizes = np.linspace(self.minGrainSz,self.maxGrainSz,numPoints)
		probs = np.linspace(0,1,numPoints/2)
		probs = np.append(probs,probs[::-1])

		grainSizePDF.data_source.data = {'x': chunkSizes, 'y': probs}

	def setupChunkTimeWindow(self):
		#subtool to control the chunk size distribution
		self.grainSizeSlider = RangeSlider(start=0, end=300, value=[0,20],step=1,title="Chunk Time Bounds",width=self.sliderWidth)#, callback=timeSliderCallback)
		self.grainSizeSlider.on_change("value",self.grainSizeSliderCallback)

		maxSamplePlot = figure(height = self.subplotSize,x_range=(0,300),y_range=(0,1.1),width = self.subplotSize,toolbar_location=None,title="Grain Size PDF",tools="")#x_range = (0,len(movedSignal)))
		maxSamplePlot.yaxis.visible = False
		maxSamplePlot.grid.visible = False

		numPoints = 10
		chunkSizes = np.linspace(self.minGrainSz,self.maxGrainSz,numPoints)
		probs = np.linspace(0,1,int(numPoints/2))
		probs = np.append(probs,probs[::-1])

		maxSamplePlot.line(chunkSizes,probs,name="sampleSizePDF")
		# maxSampleWindow = column(maxSamplePlot,grainSizeSlider)
		return maxSamplePlot


	def setupSampleDisplacementWindow(self):
		self.sampleDisplacementWidthSlider = Slider(start=-10, end=10, value=self.shiftMean,step=1,title="Sample Displacement Average",width=self.sliderWidth)
		self.sampleDisplacementWidthSlider.on_change("value",self.sampleDisplacementWidthCallback)

		self.sampleDisplacementWidthStdSlider = Slider(start=1, end=30, value=self.shiftStandardDev,step=1,title="Sample Displacement Std",width=self.sliderWidth)
		self.sampleDisplacementWidthStdSlider.on_change("value",self.sampleDisplacementWidthStdCallback)

		sampleDisplacementPlot = figure(height = self.subplotSize,width=self.subplotSize,x_range=(-10,10),y_range=(0,.2),toolbar_location=None,title = "Sample Displacement PDF",tools="")
		# sampleDisplacementPlot.axis.visible = False
		sampleDisplacementPlot.grid.visible = False

		ts = np.linspace(-10,10)
		sampleDisplacementPlot.line(ts,norm.pdf(ts,self.shiftMean,self.shiftStandardDev),name="sampleDispacePDF")
		return sampleDisplacementPlot

	def updateSampleDisplacementPDF(self):
		sampleDisplacement = self.sampleDisplacementPlot.select_one({'name': 'sampleDispacePDF'})
		ts = np.linspace(-10,10)
		sampleDisplacement.data_source.data = {'x': ts, 'y': norm.pdf(ts,self.shiftMean,self.shiftStandardDev)}

	def sampleDisplacementWidthCallback(self,attr,old,new):
		self.shiftMean = new
		self.updateSampleDisplacementPDF()

	def sampleDisplacementWidthStdCallback(self,attr,old,new):
		self.shiftStandardDev = new
		self.updateSampleDisplacementPDF()

	def setupGeneralControls(self):
		channelRadioButtons = RadioButtonGroup(labels=["Independent", "Coupled"], active=0,disabled = True)

		self.switcherooButton = Button(label="Switcheroo", button_type="success")

		fractionOfWaveToDisturbSlider = Slider(start=0, end=1, value=self.pctToShift,step=.1,title="Portion Of Wave To Disturb",width = self.sliderWidth)#, callback=timeSliderCallback)
		fractionOfWaveToDisturbSlider.on_change("value",self.fractionOfWaveToDisturbCallback)

		controlButtonsColumn = column(channelRadioButtons,fractionOfWaveToDisturbSlider,self.sampleDisplacementWidthSlider,self.sampleDisplacementWidthStdSlider,self.grainSizeSlider,self.switcherooButton)
		return controlButtonsColumn

	def fractionOfWaveToDisturbCallback(self,attr,old,new):
		self.pctToShift = new

	def setupPlots(self):
		sampleDis = self.setupSampleDisplacementWindow()
		self.sampleDisplacementPlot = sampleDis

		maxSampleWindow = self.setupChunkTimeWindow()
		self.maxSamplePlot = maxSampleWindow

		generalControls = self.setupGeneralControls()

		self.gui = row(maxSampleWindow,sampleDis,generalControls,height=self.subplotSize)

	def getGrainSizes(self):
		return (self.minGrainSz,self.modeGrainSz, self.maxGrainSz)

	def getShiftInfo(self):
		return (self.pctToShift,self.shiftStandardDev)

def testRearrangerControls():
	r = rearrangerControls()
	r.showGUI()

# testRearrangerControls()

from signalHandler import signalHandler
from grainShuffler import granularize_signal,shuffle_grains

class masterRearranger:
	"""Class to handle the shuffler controls, a source audio, and a sink audio"""

	def __init__(self,sourceFilename = ""):
		logger.logData(source="Master rearranger",priority="INFO",msgType="Setup start",msgData=())

		self.sourceAudio = signalHandler(signalFilename=sourceFilename)
		self.sinkAudio = signalHandler()

		self.rearrangerControls = rearrangerControls()
		self.rearrangerControls.switcherooButton.on_click(self.shuffleButtonCallback)

		columnHeight = self.sourceAudio.figureHeight * 2# + self.rearranger.subplotSize
		self.gui = column(self.sourceAudio.gui,self.rearrangerControls.gui,self.sinkAudio.gui,height = 10,sizing_mode="fixed")

		logger.logData(source="Master rearranger",priority="INFO",msgType="Setup done",msgData=())

	def showGui(self):
		output_file(os.path.join("webpages","signalRearranger.html"))

		show(self.gui)
		curdoc().add_root(self.gui)

	def shuffleButtonCallback(self):
		if not self.sourceAudio.activeSignal.any():
			logger.logData(source="Master rearranger",priority="WARN",msgType="Empty",msgData=())
			return

		#query parameters from tool settings
		(minGrainSz,modeGrainSz, maxGrainSz) = self.rearrangerControls.getGrainSizes()
		(pctToShift,shiftStandardDev) = self.rearrangerControls.getShiftInfo()
	
		logger.logData(source="Master rearranger",priority="INFO",msgType="Shuffle",msgData=(minGrainSz,modeGrainSz, maxGrainSz,pctToShift,shiftStandardDev))

		#create vector to store rearranged channel signals in
		messedUpSignals = []

		for channelInd in self.sourceAudio.activeChannels:
			sigToGranularize = self.sourceAudio.signal[:,channelInd]

			grainMarkers = granularize_signal(sigToGranularize, minGrainSz, modeGrainSz, maxGrainSz)
			messedUpSignal = shuffle_grains(sigToGranularize,grainMarkers, pctToShift,shiftStandardDev)
			messedUpTs = shuffle_grains(self.sourceAudio.sampleIndices,grainMarkers,pctToShift,shiftStandardDev)

			messedUpSignals.append(messedUpSignal)

		arraySig = np.transpose(np.array(messedUpSignals))
		self.sinkAudio.addSignal(arraySig,self.sourceAudio.sampleRate)
		self.sinkAudio.updateColorBar(messedUpTs)

		logger.logData(source="Master rearranger",priority="INFO",msgType="Shuffle complete",msgData=())

def testMasterRearranger():
	#load filename on start
	signalFilename = "2ch.wav"
	mS = masterRearranger(signalFilename)

	#start empty
	mS = masterRearranger()

	mS.showGUI()