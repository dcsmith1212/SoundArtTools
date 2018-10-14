from bokeh.models import ColumnDataSource, LinearColorMapper
from bokeh.models.glyphs import Rect
from bokeh.models.widgets import RadioButtonGroup, Slider
from bokeh.io import curdoc, show, output_file
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.events import MouseMove

import numpy as np
import os

from audioLogger import audioLogger
logger = audioLogger()

class chunkDrawer:
	"""A tool for visually drawing microsound intervals"""
	def __init__(self):
		logger.logData(source = "Time draw",priority="INFO",msgType="Setup start",msgData=())

		self.setupVariables()
		self.createFigure()
		self.setupColorBar()
		self.setupControls()
		self.gui = column(self.p,self.colorBar,self.controls)

		logger.logData(source = "Time draw",priority="INFO",msgType="Setup done",msgData=())

	def showGUI(self):
		output_file(os.path.join("webpages","chunkDrawer.html"))
		show(self.gui)
		curdoc().add_root(self.gui)

	def setupVariables(self):
		self.resetChunkLengths()

		self.chunkModes = ["Time","Sample"]
		self.chunkMode = "Time"
		self.figureWidth = 800
		self.figureHeight = 400

		self.numSamples = 200
		self.ySampleRange = (-10,100)

		self.yTimeRange = (-1,5)
		self.tRange = (0,10)

		self.maxSample = self.numSamples
		self.maxTime = self.tRange[1]

		self.textHeight = self.yTimeRange[1] - 1.0
		self.textOffset = .5
		self.lineWidth = 4 #line width for chunk timestamp markers

		#colors for the chunk marker lines
		self.knownChunkColor = "blue"
		self.nextChunkColor = "red"
		self.nextNextChunkColor = "green"

	def resetChunkLengths(self):
		self.currentNextIndex = 0
		self.chunkIndex = 0
		self.nextNextTimestamp = 0
		self.chunkLengths = []
		self.chunkTimestamps = [0.]
		self.chunkSampleIndices = [0]

	def setLastChunks(self):
		self.lastChunkLengths = self.chunkLengths

	def getLastChunks(self):
		return self.lastChunkLengths

	def updateKnownTimeChunks(self,yVal):
		#called once the mouse crosses the known chunk threshhold
		#if yVal is 0 or less, it means a skip, but needs to be represented as a discrete chunk
		if yVal <= 0:
			self.chunkLengths.append(0)
			self.currentNextIndex += 1.0
			nextTimestamp = self.chunkTimestamps[-1] + 1.0

		else:
			self.chunkLengths.append(yVal)
			self.currentNextIndex += yVal
			nextTimestamp = self.chunkTimestamps[-1] + self.chunkLengths[-1]

		if nextTimestamp > self.maxTime:
			self.setLastChunks()
			roundedChunks = [round(chunkTime,2) for chunkTime in self.getLastChunks()]
			logger.logData(source = "Time draw",priority="INFO",msgType="Time chunk finished",msgData=(roundedChunks))
			# self.resetChunkLengths()

		else:
			self.chunkIndex +=1
			self.chunkTimestamps.append(nextTimestamp)

		nextChunkLine = self.p.select_one({'name': "nextChunkLine"})
		nextChunkLine.data_source.data = {'x': [self.chunkTimestamps[-1],self.chunkTimestamps[-1]], 'y': self.yTimeRange}

	def updateLastTimeChunkLines(self):
		chunkLines = self.p.select_one({'name': 'chunkLines'})

		ts = [[tVal,tVal] for tVal in self.chunkTimestamps[:-1]]
		ys = [self.yTimeRange for i in range(self.chunkIndex)]

		chunkLines.data_source.data = {'xs': ts, 'ys': ys}

	def updateLastTimeChunkLabels(self):
		chunkLabels = self.p.select_one({'name': 'chunkLabels'})

		ts = [(tVal + self.textOffset) for tVal in self.chunkTimestamps]
		ys = [self.textHeight for i in range(self.chunkIndex+1)]
		labels = list(map(str,range(self.chunkIndex+1)))

		chunkLabels.data_source.data = {'x': ts, 'y': ys,"text":labels}

	def mouseMoveTimeCallback(self,xVal,yVal):

		#check to make sure the mouse isn't too far from the last value for drawing the line
		#means the system won't engage until you are close to the last value
		if xVal > (self.currentNextIndex)+1.5:
			return

		if yVal <=0:
			self.nextNextTimestamp = self.currentNextIndex + 1.0
		else:
			self.nextNextTimestamp  = self.currentNextIndex + yVal

		nextNextChunkLine = self.p.select_one({'name': 'nextNextChunkLine'})
		nextNextChunkLine.data_source.data = {'x': [self.nextNextTimestamp,self.nextNextTimestamp], 'y': self.yTimeRange}

		if xVal > self.currentNextIndex:
			self.updateKnownTimeChunks(yVal)
			self.updateLastTimeChunkLines()
			self.updateLastTimeChunkLabels()

			logger.logData(source = "Time draw",priority="INFO",msgType="Time chunk",msgData=(yVal))

	##SAMPLE CHUNK FUNCTIONS
	def updateLastSampleChunkLines(self):
		chunkLines = self.p.select_one({'name': 'chunkLines'})

		ts = [[tVal,tVal] for tVal in self.chunkSampleIndices[:-1]]
		ys = [self.ySampleRange for i in range(self.chunkIndex)]

		chunkLines.data_source.data = {'xs': ts, 'ys': ys}

	def updateKnownSampleChunks(self,yVal):
		#called once the mouse crosses the known chunk threshhold
		#if yVal is 0 or less, it means a skip, but needs to be represented as a discrete chunk
		if yVal <= 0:
			self.chunkLengths.append(0)
			self.currentNextIndex += 10
			nextSampleIndex = self.chunkSampleIndices[-1] + 10

		else:
			self.chunkLengths.append(yVal)
			self.currentNextIndex += yVal
			nextSampleIndex = self.chunkSampleIndices[-1] + self.chunkLengths[-1]

		if nextSampleIndex > self.maxSample:
			self.setLastChunks()
			logger.logData(source = "Time draw",priority="INFO",msgType="Sample chunk finished",msgData=(self.getLastChunks()))
			# self.resetChunkLengths()

		else:
			self.chunkIndex +=1
			self.chunkSampleIndices.append(nextSampleIndex)

		nextChunkLine = self.p.select_one({'name': "nextChunkLine"})
		nextChunkLine.data_source.data = {'x': [self.chunkSampleIndices[-1],self.chunkSampleIndices[-1]], 'y': self.ySampleRange}

	def mouseMoveChunkCallback(self,xVal,yVal):
		#check to make sure the mouse isn't too far from the last value for drawing the line
		#means the system won't engage until you are close to the last value
		xVal = int(xVal)
		yVal = int(yVal)

		if xVal > (self.currentNextIndex)+10:
			return

		if yVal <=0:
			self.nextNextChunkIndex = self.currentNextIndex + 10
		else:
			self.nextNextChunkIndex  = self.currentNextIndex + yVal

		nextNextChunkLine = self.p.select_one({'name': 'nextNextChunkLine'})
		nextNextChunkLine.data_source.data = {'x': [self.nextNextChunkIndex,self.nextNextChunkIndex], 'y': self.ySampleRange}

		if xVal > self.currentNextIndex:
			self.updateKnownSampleChunks(yVal)
			self.updateLastSampleChunkLines()
			# self.updateLastTimeChunkLabels()

			logger.logData(source = "Time draw",priority="INFO",msgType="Sample chunk",msgData=(yVal))

	def mouseMoveCallback(self,event):
		#called on mouse move event
		# self.mouseEventIndex+=1

		xVal = event.x
		yVal = event.y

		if self.chunkMode == "Time":
			self.mouseMoveTimeCallback(xVal,yVal)

		if self.chunkMode == "Sample":
			self.mouseMoveChunkCallback(xVal,yVal)

		return

	def repeatResolutionCallback(self,attr,old,new):
		if self.chunkMode == "Time":
			self.maxTime = self.tRange[1]/new
			self.p.x_range.end = self.maxTime
			self.p.y_range.start = -1.0/new
			self.p.y_range.end = self.yTimeRange[1]/new

		if self.chunkMode == "Sample":
			self.maxSample = self.numSamples/new
			self.p.y_range.end = self.ySampleRange[1]/new
			# self.p.y_range.start = -1.0/new
			self.p.x_range.end = self.maxSample

	def setupControls(self):
		repeatResolutionSlider = Slider(start=1, end=10, value=1, step=1,title="Repeat resolution")#,width = self.figureWidth,height = self.buttonHeight)
		repeatResolutionSlider.on_change("value",self.repeatResolutionCallback)

		chunkModeButtons = RadioButtonGroup(labels=["Time","Sample"],active=0,button_type="warning")#,width=self.buttonWidth,height = self.buttonHeight)
		chunkModeButtons.on_change("active",self.chunkModeCallback)

		yAxisModeButtons =  RadioButtonGroup(labels=["Linear","Log"],active=0,button_type="warning")
		yAxisModeButtons.on_change("active",self.yAxisModeCallback)

		self.controls = row(repeatResolutionSlider,chunkModeButtons,yAxisModeButtons)


	def yAxisModeCallback(self,att,old,new):
		if new ==1:
			print ("lin")
		else:
			print ("log")

	def chunkModeCallback(self,att,old,new):
		chunkModes = ["Time","Sample"]
		self.resetChunkLengths()
		self.chunkMode = chunkModes[new]

		if self.chunkMode == "Time":
			self.p.x_range.end = self.tRange[1]
			self.p.y_range.end = self.yTimeRange[1]

		if self.chunkMode == "Sample":
			self.p.y_range.end = self.ySampleRange[1]
			self.p.x_range.end = self.numSamples

			startingChunkLines = self.p.select_one({'name': 'chunkLines'})
			startingChunkLines.data_source.data = {'xs': [[0,0]], 'ys': [self.ySampleRange]}

			nextNextChunkLine = p.line(x =[self.nextNextTimestamp,self.nextNextTimestamp],y=self.yTimeRange,line_width=self.lineWidth, color = self.nextNextChunkColor,name="nextNextChunkLine")

			# self.updateLastSampleChunkLines()

	def createFigure(self):
		#create a figure ranging 10 seconds, with y from -1 to 5
		p = figure(x_range=self.tRange, y_range=self.yTimeRange, width=self.figureWidth, height=self.figureHeight, tools="", title='Chunk Length Tracer Tool',toolbar_location=None)

		zeroLine = p.line(x =[0,self.tRange[1]],y=[0,0],line_width=self.lineWidth/3, color = "black",name="zeroLine")

		knownChunkLines = p.multi_line(xs=[0,0], ys=self.yTimeRange, line_color="#8073ac", line_width=2,name="chunkLines")
		knownChunkLabels = p.text(x=[], y=[], text=[], text_color="black",name="chunkLabels")
		nextChunkLine = p.line(x =[],y=[],line_width=self.lineWidth, color = self.nextChunkColor,name="nextChunkLine")
		nextNextChunkLine = p.line(x =[self.nextNextTimestamp,self.nextNextTimestamp],y=self.yTimeRange,line_width=self.lineWidth, color = self.nextNextChunkColor,name="nextNextChunkLine")

		# mouseTrailLine = p.multi_line(xs="xs",ys="ys",source=self.lineSource, line_width=5, alpha=0.4, color='red')
		#set callback on mousemove to update line
		p.on_event(MouseMove,self.mouseMoveCallback)
		self.p = p

	def updateColorBar(self,times):
		colorBarPlot = self.gui.select_one({'name': 'colorBarPlot'})
		colorBarPlot.x_range.end = self.numSamples
		colorBar =  self.gui.select_one({'name': 'colorBar'})

		self.messedUpTs = times
		self.colorSource.data = {"x":self.sampleIndices,"place":self.messedUpTs}


	def setupColorBar(self):
		colorTimeline = figure(height = 30, y_range = (-.5,.5),width=self.figureWidth,x_range = (0,100),toolbar_location=None,output_backend="webgl",name="colorBarPlot",tools="")

		colorTimeline.axis.visible = False
		colorTimeline.grid.visible = False
		self.mapper = LinearColorMapper(palette="Inferno256", low=0, high=100)

		# colorTimeline.image(image=range(self.numSamples),x=0,y=.5,dh=1,dw=1,fill_color={'field':"x",'transform': self.mappers[colorBarType-1]},
		#        name="cbar" + str(colorBarType))

		self.colorSource = ColumnDataSource({"x":range(100),"place":range(100)})

		# colorTimeline.rect(x="x", y=0, width=1, height=1,fill_color={'field':"place",'transform': self.mapper},name="colorBar",
		#        line_width=0.0,line_color= None,line_alpha = 0.0,source=colorSource
		#        )

		colorBar = Rect(x="x", y=0, width=1, height=1, fill_color={'field':"place",'transform': self.mapper},name="colorBar",
		       line_width=0.0,line_color= None,line_alpha = 0.0
		       )

		colorTimeline.add_glyph(self.colorSource, colorBar)

		self.colorBar = colorTimeline


def testChunkDrawer():
	t = timeDrawer()
	t.showGUI()