import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import spectrogram
import time
import numpy as np
import os

from bokeh.plotting import figure, show, curdoc, output_file
from bokeh.layouts import row, column
from bokeh.models.glyphs import Rect
from bokeh.models import LinearColorMapper, ColumnDataSource, CustomJS
from bokeh.models.widgets import Button, TextInput, RangeSlider, Toggle, CheckboxButtonGroup, RadioButtonGroup, Div

from lyricsHandler import lyricsHandler
from audioLogger import audioLogger
logger = audioLogger()

class signalHandler:

	def __init__(self,signalFilename = "",lyricsFilename = "",signal=[],sampleRate=0,color="red"):
		self.path = os.getcwd()

		logger.logData(source = "Signal handler",priority="INFO",msgType="Setup start",msgData=())

		self.setupVariables()

		self.color = color
		self.setupMapper()
		self.setupColorBar()

		self.lyricsImported = 0
		if lyricsFilename:
			self.setupLyricTable(lyricsFilename)
			self.lyricsImported = 1

		self.setupPlotWindow()
		self.setupControls()
		self.setupGUI()

		if signalFilename:
			self.importFile(signalFilename)

		if len(signal):
			self.addSignal(signal,sampleRate)

		logger.logData(source = "Signal handler",priority="INFO",msgType="Setup done",msgData=((self.signalImported)))

	def setupGUI(self):
		"""Wraps the plot, slider, and tool column into one layout"""

		audioCol = column(self.p,self.colorBar,self.timeWindowSlider,height=self.figureHeight)
		# dtgCol = column(self.dtg.gui,width=400)
		if self.lyricsImported:
			# self.gui = self.lyricTable
			self.gui = row(self.lyricsGui,audioCol,self.controls,height = self.figureHeight-110)
		else:
			self.gui = row(audioCol,self.controls,height = self.figureHeight-110)

	def setupVariables(self):
		"""sets up important variables to the tool, including
			figure size
			dummy variables to use before file import
			tool options - loop, button sizes, button delay
		"""

		try:
		    self.masterPath = os.getcwd() #use when running from Sublime
		    os.listdir(self.masterPath)

		except:
		    self.masterPath = os.path.join("soundTools","") #use when running from Bokeh
		    os.listdir(self.masterPath)

		self.subtitlePath = os.path.join(self.masterPath,"lyrics")
		self.audioPath = os.path.join(self.masterPath,"audio")
		self.webpagePath = os.path.join(self.masterPath,"webpages")

		self.figureWidth = 1000
		self.figureHeight = 500

		self.buttonWidth = 200
		self.buttonHeight = 15
		self.numXTicks = 4
		self.soundPlaying = 0
		self.signalImported = 0
		self.lastChunkIndex = 0

		self.strideMultiplier = 100

		self.sweepStartSample = 0
		self.sweepEndSample = 10
		self.activeChannels = []
		self.yRange = (-1,1)
		self.channelAnchorYs = np.arange(0,self.yRange[1],2)

		self.plotStyle = 0
		self.glyphsSetup = 0
		self.loop = 0
		self.plotMode = 0

		self.outputFilename = "output"
		self.updateDelay = 12 #delay period in milliseconds befwen timeline update while playing the active signal
		self.windowChunkLength = 10 #seconds

	def showGui(self):
		output_file(os.path.join("webpages","signalHandler.html"))

		logger.logData(source = "Signal handler",priority="INFO",msgType="Show",msgData=())

		show(self.gui)
		curdoc().add_root(self.gui)

	def addSignal(self,signalIn,sampleRate):
		"""Adds a prexisting list/mutliDim ndarray  (with known sample rate) as the active signal and updates plot"""

		#keep the original in case of a reset
		self.originalSignal = signalIn

		#signal gets changed on update of time slider
		self.signal = self.originalSignal
		#activeSignal gets changed on update of of signal AND update of active channels
		self.activeSignal = self.signal

		self.sampleRate = sampleRate
		self.signalImported = 1

		logger.logData(source = "Signal handler",priority="INFO",msgType="Signal add",msgData=())

		self.analyzeSignal()

	def importFile(self,filename):
		"""imports a wav file into the tool and updates the plot and tools"""

		#check to make sure the filename is valid
		try:
			self.sampleRate, self.originalSignal = wavfile.read(os.path.join(self.audioPath,filename)) #keep the original for master reference
		except:
			logger.logData(source = "Signal handler",priority="WARN",msgType="Import file fail",msgData=(filename))
			return
		#update tool's internal filename
		self.filename = filename
		#import the wav file
		self.signal = self.originalSignal
		self.activeSignal = self.signal
		self.signalImported = 1

		logger.logData(source = "Signal handler",priority="INFO",msgType="Import file",msgData=(filename))

		#get relevant signal info and update plot
		self.analyzeSignal()

	def analyzeSignal(self):
		"""Parses the metadata from the active signal and updates plot and tools"""

		self.glyphsSetup = 0
		#get number of channels of signal
		try:
			self.numChannels = self.signal.shape[1]
		except:
			#if it's single channel its imported as a list, make it a 1D ndarray
			self.numChannels = 1
			self.signal = np.transpose(np.array([self.signal]))

		self.activeChannels = list(range(self.numChannels))
		self.channelButtons.labels = list(map(str,self.activeChannels))

		self.channelButtons.active = self.activeChannels

		if not np.any(self.signal):

			logger.logData(source = "Signal handler",priority="WARN",msgType="Empty",msgData=())

			return

		self.numSamples = len(self.signal)
		self.sampleIndices = range(self.numSamples)
		self.messedUpTs = self.sampleIndices

		self.updateMapperHigh(self.numSamples)
		self.updateColorBar(self.sampleIndices)

		self.signalDuration = self.numSamples / float(self.sampleRate)
		self.windowChunks = int((self.signalDuration/self.windowChunkLength)) + 1

		#update the time slider with the imported signal's duration
		self.timeWindowSlider.end = self.signalDuration
		self.timeWindowSlider.value = [0,self.signalDuration]

		self.sweepStartSample = 0
		self.sweepEndSample = self.numSamples

		#setup the ticker to replace indices with timestamps
		self.setMasterXAxisTicker()

		#PLOT SCATTER PARAMS
		#get max amplitude of signal to adjust y range and channel spacing
		self.sigPeak = np.amax(self.signal)
		self.yRange = (0,2*self.numChannels*self.sigPeak)

		#generate offsets to space multiple channels out in the y axis
		self.channelAnchorYs = np.arange(self.sigPeak,self.yRange[1],2*self.sigPeak)

		logger.logData(source = "Signal handler",priority="INFO",msgType="Analyze",
			msgData=(round(self.signalDuration,3),self.numChannels,self.numSamples,self.sampleRate))

		self.drawActivePlot()
		# self.drawFullSignal()

	def setMasterXAxisTicker(self):
		#ticker dictionary to rpaplce x axis index ticks with their coirrosponding timestamps
		self.masterTicker = list(range(0,self.numSamples,int(self.numSamples/self.numXTicks)))
		self.masterXAxisOverrideDict = {}

		timeLabels = np.linspace(0,self.signalDuration,self.numXTicks)
		for sampleInd,timeLabel in zip(self.masterTicker,timeLabels):
			self.masterXAxisOverrideDict[sampleInd] = str(round(timeLabel,3))

		#set up the size and duration of the sub-chunks displayed while the signal is playing
		self.samplesPerChunk = int(self.numSamples/self.windowChunks)

		self.chunkDuration = self.samplesPerChunk/float(self.sampleRate)
		#the absolute index values comprising the x axis ticks
		self.chunkTicker = list(range(0,self.samplesPerChunk,int(self.samplesPerChunk/self.numXTicks)))

		# self.chunkLabels = np.linspace(0,self.chunkDuration,10)
		# self.chunkTickOverride = {}
		# for sampleInd,timeLabel in zip(self.chunkTicker,self.chunkLabels):
		# 	self.chunkTickOverride[sampleInd] = str(round(timeLabel,3))

	def fileCallback(self,attr,old,new):
		"""Callback assigned to choosing a file from the file browser"""

		filename =  new['file_name'][0]
		self.importFile(filename)

	def fileButtonSetup(self):
		"""Creates a "File opener" button and assigns a javascript callback to it that opens an os-independent file picker window
		imports chosen file into the class"""
		fileSource = ColumnDataSource({'file_name':[]})

		self.fileImportButton.callback = CustomJS(args=dict(file_source=fileSource), code = """
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

	def setupControls(self):
		"""Called on setup, creates buttons and sliders to:
			open a local audio file
			set loop mode
			update the active timespan
			play the active timespan
			set filename to save active signal to
			save active signal to that filename
		"""

		#check boxes to choose what plots to display
		self.plotModeButtons = RadioButtonGroup(labels=["Wav","FFT","Spectrogram"],active=self.plotMode,button_type="warning",width=self.buttonWidth,height = self.buttonHeight)
		self.plotModeButtons.on_change("active",self.plotModeCallback)

		#choose betwen line or scatter plot
		self.plotStyleButtons = RadioButtonGroup(labels=["Line","Scatter"],active=0,button_type="danger",width=self.buttonWidth,height = self.buttonHeight)
		self.plotStyleButtons.on_change("active",self.plotStyleCallback)

		channelTitle = Div(text="""<b>Audio Channels:</b>""",width=self.buttonWidth, height=2)
		self.channelButtons = CheckboxButtonGroup(labels = ["-"],active = [0],button_type = "primary",width = self.buttonWidth,height= self.buttonHeight)
		self.channelButtonRow = column(channelTitle,self.channelButtons,width=self.buttonWidth,height = self.buttonHeight*2)
		self.channelButtons.on_change("active",self.channelButtonCallback)

		#creates a filebutton and assigns it a callback linked to a broser-based file browser
		self.fileImportButton = Button(label="Import File", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.fileButtonSetup()

		#create a loop toggle button and assigns a callback to it
		self.loopAudioToggle= Toggle(label="Loop", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.loopAudioToggle.on_click(self.loopAudioCallback)

		#double ended slider to clip audio by time
		self.timeWindowSlider = RangeSlider(start=0, end=1, value=[0,1], step=.05,title="Wav File Window",width = self.figureWidth,height = self.buttonHeight)
		self.timeWindowSlider.on_change("value",self.timeSliderCallback)

		#button to commit clip changes to active signal
		self.updateButton = Button(label="Update", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.updateButton.on_click(self.updateButtonCallback)

		#button to play active signal,
		self.playButton = Button(label="Play", button_type="success",width=self.buttonWidth,height = self.buttonHeight)
		self.playButton.on_click(self.playSound)

		self.filenameBox = TextInput(value="output", title="Output Filename:",width=self.buttonWidth)

		#button to write active signal to file
		self.writeFileButton = Button(label="Write Active File", button_type="success",width=self.buttonWidth, height = self.buttonHeight)
		self.writeFileButton.on_click(self.writeFileButtonCallback)

		#button to reset tool to state right after signal import
		self.resetButton = Button(label="Reset", button_type="success",width=self.buttonWidth,height=self.buttonHeight)
		self.resetButton.on_click(self.resetButtonCallback)		
		
		self.resetZoomButton = Button(label="Reset Zoom", button_type="success",width=self.buttonWidth, height = self.buttonHeight)
		self.resetZoomButton.js_on_click(CustomJS(args=dict(p=self.p), code="""
    		p.reset.emit()
			"""))

		self.generalControlsColumn = column(
			self.plotModeButtons,
			self.plotStyleButtons,
			self.filenameBox,
			self.channelButtonRow,
				width=self.buttonWidth)

		self.buttonColumn = column(
			self.resetZoomButton,
			self.fileImportButton,
			self.updateButton,
			self.loopAudioToggle,
			self.playButton,
			self.writeFileButton,
			self.resetButton,
				width=self.buttonWidth)#,height=self.figureHeight)

		self.controls = row(self.generalControlsColumn,self.buttonColumn)
		#wrap buttons and text box in a column of fixed width
		# self.buttonColumn = column(self.plotModeButtons,self.plotStyleButtons,self.channelButtonRow,self.resetZoomButton,self.fileImportButton,self.updateButton,self.loopToggle,self.playButton,self.writeFileButton,self.resetButton,self.filenameBox,width=self.buttonWidth)#,height=self.figureHeight)

	#choose active channels
	def channelButtonCallback(self,attr,old,new):
		if not self.signalImported: return

		try:
			self.activeChannels = new
			self.activeSignal = self.signal[:,self.activeChannels]
			self.glyphsSetup = 0
			self.drawActivePlot()

			logger.logData(source = "Signal handler",priority="INFO",msgType="Channel update",msgData=((old,new)))

		except:
			logger.logData(source = "Signal handler",priority="WARN",msgType="Channel fail",msgData=(old))

			return

		#choose between line or scatter plot
	def plotStyleCallback(self,attr,old,new):
		self.plotStyle = new
		self.glyphsSetup = 0

		# self.drawFullSignal()
		self.drawActivePlot()


	def plotModeCallback(self,att,old,new):
		self.plotMode = new
		self.drawActivePlot()

	def loopAudioCallback(self,event):
		"""Called on toggling of the loop button,
			binary inverts previous loop val"""

		self.loop = 1 - self.loop

	def writeFileButtonCallback(self):
		"""Called on click of the write Fiile button
		Writes the active signal to the filename set by the textbox"""
		outputFilename = self.filenameBox.value + ".wav"
		outputPath = os.path.join(self.path,"audio",outputFilename)

		numChannels = len(self.activeChannels)

		logger.logData(source = "Signal handler",priority="INFO",msgType="Write",msgData=(outputFilename,numChannels,self.sampleRate,self.signalDuration))

		wavfile.write(outputPath, self.sampleRate, self.activeSignal)

	# def resetZoomCallback(self):
	# 	print(1)

	def resetButtonCallback(self):
		"""Returns the tool to state it was immediately after file was imported"""

		#if no signal is imported, do nothing
		if not self.signalImported: return

		#reset active to signal to the original, unclipped signal
		self.signal = self.originalSignal

		logger.logData(source = "Signal handler",priority="INFO",msgType="Reset",msgData=())

		#return variables and plot to original state
		self.analyzeSignal()

	def updateButtonCallback(self):
		"""Called on press of the update button,
			clips the signsal by the estart and end trimes decreed by the time slider,
			resets the plot to like the clipped signal is the new full signal"""

		#if no signal is imported, do nothing
		if not self.signalImported:
			logger.logData(source = "Signal handler",priority="WARN",msgType="Update failed",msgData=())

			return

		#clip all channel samples corresponding to the times on slider
		self.signal = self.signal[self.sweepStartSample:self.sweepEndSample,:]

		logger.logData(source = "Signal handler",priority="INFO",msgType="Update signal",msgData=())

		#update variables and plot with clipped signal
		self.analyzeSignal()

	def timeSliderCallback(self,attr,old,new):
		"""Called on update of the time slider
			moves the sweep start/end lines used for clipping the signal when the update button is pressed"""

		if not self.signalImported:
			return

		try:
			#convert the start and end times to integer sample numbers and update internal locations
			self.sweepStartSample = int(new[0]*self.sampleRate)
			self.sweepEndSample = int(new[1]*self.sampleRate)

			#update sweep line graphics
			startLine = self.p.select_one({'name': 'sweepStartLine'})
			startLine.data_source.data = {'x': [self.sweepStartSample,self.sweepStartSample], 'y': self.yRange}
			
			endLine = self.p.select_one({'name': 'sweepEndLine'})
			endLine.data_source.data = {'x': [self.sweepEndSample,self.sweepEndSample], 'y': self.yRange}
		except:
			return

	def shiftSamples(self,channelIndex):
		"""Element wise adds to the channel's vector to offset a channel so it can vbe plotted alongside other channels"""

		channelSamples = self.signal[:,channelIndex]

		reducedSamples = channelSamples[::self.strideMultiplier]
		return reducedSamples + self.channelAnchorYs[channelIndex]

	def setupPlotWindow(self):
		"""Creates a window containing the channel plots"""

		p = figure(height=300,width=self.figureWidth,x_range=(0,1), y_range=(0,1),tools="box_zoom",toolbar_location=None,output_backend="webgl")
		# p.toolbar.active_scroll = "auto"
		p.yaxis.visible = False
		p.grid.visible = False
		self.p = p

	def updateFigureForSpectrogram(self):
		self.p.x_range.end=self.numSamples
		self.p.y_range.end  = self.yRange[1]

		self.p.xaxis.ticker = self.masterTicker
		self.p.xaxis.major_label_overrides = self.masterXAxisOverrideDict

	def plotSpectrogram(self):
		"""Plots a log spectrogram of the active audio, returns figure object"""

		#max freq represetnedf (nyquist constrained)
		imgHeight = self.sampleRate/2

		self.p.y_range.end  = imgHeight * self.numChannels

		imgWidth = self.signalDuration
		self.p.x_range.end = imgWidth

		for channelNum in self.activeChannels:
			channelSignal = self.signal[:,channelNum]

			freqs,times,data = self.log_specgram(channelSignal,self.sampleRate)

			self.p.image(image=[data], x=0, y=imgHeight*channelNum, dw=imgWidth, dh=imgHeight, palette="Spectral11")

	def log_specgram(self,audio, sampleRate, window_size=20, step_size=10, eps=1e-10):
		"""Kraggin log spectrogram useful for MFCC analysis"""
		
		nperseg = int(round(window_size * sampleRate / 1e3))
		noverlap = int(round(step_size * sampleRate / 1e3))
		freqs, times, spec = spectrogram(audio,
		                                fs=sampleRate,
		                                window='hann',
		                                nperseg=nperseg,
		                                noverlap=noverlap,
		                                detrend=False)
		return freqs, times, np.log(spec.T.astype(np.float32) + eps)

	def setupPlotScatterGlyphs(self):
		self.p.line([self.sweepStartSample,self.sweepStartSample],self.yRange,color="blue",line_width=2,name="sweepStartLine")
		self.p.line([self.sweepEndSample,self.sweepEndSample],self.yRange,color="blue",line_width=2,name="sweepEndLine")

		self.p.line([0,0], self.yRange, color='red', line_width=2, name='timeLine')

		# self.scatterSource = {"x":[],"place":[]}

		self.scatterSources = []
		for channelNum in self.activeChannels:
			self.scatterSources.append(ColumnDataSource({"x":list(self.sampleIndices),"y":list(self.sampleIndices),"place":self.messedUpTs}))
			# self.p.scatter(x=[],y=[],radius=.1, fill_color={'field':"place",'transform': self.mapper},name="audioLine" + str(channelNum))
			self.p.scatter(x="x",y="y",radius=1,
				source=self.scatterSources[channelNum], 
				fill_color={'field':"place",'transform': self.mapper},line_color={'field':"place",'transform': self.mapper},
				name="audioLine" + str(channelNum))

	def setupLinePlotGlyphs(self):
		self.p.line([self.sweepStartSample,self.sweepStartSample],self.yRange,color="blue",line_width=2,name="sweepStartLine")
		self.p.line([self.sweepEndSample,self.sweepEndSample],self.yRange,color="blue",line_width=2,name="sweepEndLine")

		self.p.line([0,0], self.yRange, color='red', line_width=2, name='timeLine')
		for channelNum in self.activeChannels:
			self.p.line(x=[],y=[],line_width=.3,color=self.color,name="audioLine" + str(channelNum))

	def drawActivePlot(self):
		if not self.signalImported: return

		if self.plotMode == 0:
			self.drawFullSignal()
		elif self.plotMode == 1:
			self.getFFT()
		else:
			self.plotSpectrogram()
		
	def drawFullSignal(self):
		if self.glyphsSetup == 0:
			self.p.renderers = []

			if self.plotStyle:
				self.setupPlotScatterGlyphs()
			else:
				self.setupLinePlotGlyphs()

			self.glyphsSetup = 1

		"""redraws each channel of the full plot and updates the xaxis to the full signal duration"""
		for channelNum in self.activeChannels:

			shiftedSamples = self.shiftSamples(channelNum)


			reducedSampleIndices = self.sampleIndices[::self.strideMultiplier]

			if self.plotStyle:
				self.scatterSources[channelNum].data = {'x':reducedSampleIndices, 'y': list(shiftedSamples),"place":reducedSampleIndices}
			else:
				channelLine = self.p.select_one({'name': 'audioLine' + str(channelNum)})
				channelLine.data_source.data = {'x': reducedSampleIndices, 'y': shiftedSamples,"place":reducedSampleIndices}
		#update x axis with full timespan
		self.p.x_range.end=self.numSamples
		self.p.y_range.end  = self.yRange[1]

		self.p.xaxis.ticker = self.masterTicker
		self.p.xaxis.major_label_overrides = self.masterXAxisOverrideDict

	def playSound(self):
		"""Starts playing the signal, and draws a sweeping vertical line on actively updating sub-samples of the audfio"""

		#if the "Play" button is pushed during play, it acts as a stop button
		if self.soundPlaying == 1:
			logger.logData(source = "Signal handler",priority="INFO",msgType="Pause",msgData=())

			self.stopAudio()
			return

		#if no signal is imported, do nothing
		if not self.signalImported: return

		#hide sweep lines until their chunk occurs	
		startLine = self.p.select_one({'name': 'sweepStartLine'})
		startLine.visible = False

		endLine = self.p.select_one({'name': 'sweepEndLine'})
		endLine.visible = False

		##Chunk-specific sweep lines
		self.startLineAdded = 0
		self.endLineAdded = 0

		#precompute which chunk the sweep lines are in for speed
		self.sweepStartChunk = int(np.floor(self.sweepStartSample/(self.samplesPerChunk+1)))
		self.sweepEndChunk = int(np.floor(self.sweepEndSample/(self.samplesPerChunk+1)))

		#precompute their indices in their chunk
		self.shiftedSweepStart = self.sweepStartSample - self.sweepStartChunk * self.samplesPerChunk
		self.shiftedSweepEnd = self.sweepEndSample - self.sweepEndChunk * self.samplesPerChunk

		if self.p.select_one({'name': 'sweepEndLineChunk'}) == None:
			#preadd the lines for speed
			self.p.line([self.shiftedSweepStart,self.shiftedSweepStart],self.yRange,color="blue",line_width=2,visible=False,name="sweepStartLineChunk")
			self.p.line([self.shiftedSweepEnd,self.shiftedSweepEnd],self.yRange,color="blue",line_width=2,visible=False,name="sweepEndLineChunk")
		
		#update the x axis with the sub-chunk values
		self.p.x_range.end = self.samplesPerChunk
		self.p.xaxis.ticker = self.chunkTicker
		self.p.xaxis.major_label_overrides = self.createChunkXAxisOverrideDict(0)

		#set the play button to read "Pause" to pull double duty
		self.playButton.label= "Pause"

		logger.logData(source = "Signal handler",priority="INFO",msgType="Play",msgData=())

		#log start time to keep track of where the time line should be
		self.startTime = time.time()

		#start playing the sound
		try:
			sd.play(self.activeSignal, self.sampleRate,loop=self.loop,blocking=False)
		except:
			logger.logData(source = "Signal handler",priority="CRIT",msgType="Play failed",msgData=())
			self.playButton.label= "Play"
			return
		self.soundPlaying = 1

		#add a call callback to trigger periodcially and update the timeline and sub-samples
		self.perCallback = curdoc().add_periodic_callback(self.update, self.updateDelay)

	def createChunkXAxisOverrideDict(self,chunkIndex):
		"""	creates a dictionary replacing absolute index ticks on the x axis with their corrosponding times
		"""
		#get the time labels corrosponding to this chunk
		chunkTimeLabels = np.linspace(self.chunkDuration*chunkIndex,self.chunkDuration*(chunkIndex+1),self.numXTicks)

		chunkTickOverride = {}
		for sampleInd,timeLabel in zip(self.chunkTicker,chunkTimeLabels):
			#replace each sample index x tick with the time label
			chunkTickOverride[sampleInd] = str(round(timeLabel,3))
		return chunkTickOverride

	def update(self):
		"""Set to be called periodically when audio is playing to draw the active time line on the audio signal"""

		if self.loop:
			#mod the time played by total signal duration to keep the time line accurate for multiple plays
			deltaTime = (time.time() - self.startTime) % self.signalDuration #get time elapsed since the file started playing
		else:
			deltaTime = time.time() - self.startTime #get time elapsed since the file started playing

		#if signal not done playing
		if deltaTime < self.signalDuration:
			#number of samples elapsed
			dSamples = deltaTime*self.sampleRate

			#get the active chunk
			chunkIndex = int(self.windowChunks*(dSamples/self.numSamples))

			#if the chunk is different, need to update the audio plot window to the next chunk
			if self.lastChunkIndex != chunkIndex:
				#get the starting and ending sample indices for the next chunk
				chunkStartIndex = self.samplesPerChunk*chunkIndex
				chunkEndIndex = self.samplesPerChunk*(chunkIndex+1)

				#check if any of the sweep lines lie in this chunk
				if self.startLineAdded:
					self.p.select_one({'name': 'sweepStartLineChunk'}).visible = False
					self.startLineAdded = 0

				if chunkIndex == self.sweepStartChunk:
					self.p.select_one({'name': 'sweepStartLineChunk'}).visible = True
					self.startLineAdded = 1

				if self.endLineAdded:
					self.p.select_one({'name': 'sweepEndLineChunk'}).visible = False
					self.endLineAdded = 0

				if chunkIndex == self.sweepEndChunk:
					self.p.select_one({'name': 'sweepEndLineChunk'}).visible = True
					self.endLineAdded = 1

				#get the signal samples from this chunk and downsample them and shift them by channel
				reducedChunkSamps = self.signal[chunkStartIndex:chunkEndIndex:self.strideMultiplier] + self.channelAnchorYs

				reducedPlaces = list(range(chunkStartIndex,chunkEndIndex,self.strideMultiplier))
				#original
				# chunkSamps = self.signal[chunkStartIndex:chunkEndIndex]
				# shiftedChunkSamps = chunkSamps + self.channelAnchorYs

				reducedSampleIndices = list(range(0,self.samplesPerChunk,self.strideMultiplier))

				#update plot for each channel
				for channelIndex in self.activeChannels:
					if self.plotMode==0:
						audioLine = self.p.select_one({'name': "audioLine"+str(channelIndex)})
						audioLine.data_source.data = {'x': reducedSampleIndices, 'y': reducedChunkSamps[:,channelIndex],"place":reducedPlaces}

						# audioLine.data_source.data = {'x': reducedSampleIndices, 'y': shiftedChunkSamps[:,channelIndex],"place":reducedPlaces}
					else:
						self.scatterSources[channelIndex].data = {"x":reducedSampleIndices,"y":self.sampleIndices,"place":self.messedUpTs}

				#update the x-axis ticks with the new times
				self.p.xaxis.major_label_overrides = self.createChunkXAxisOverrideDict(chunkIndex)

				#update chunk index with new one
				self.lastChunkIndex = chunkIndex

			##time line update
			#get the glyph for the time line
			timeLine = self.p.select_one({'name': 'timeLine'})

			#sample index of the timeline is total samples elapsed less the number of samples in all previous chunks
			timeLineIndex = dSamples - chunkIndex*self.samplesPerChunk

			#update the time line with the new times
			timeLine.data_source.data = {'x': [timeLineIndex,timeLineIndex], 'y': self.yRange}

		#signal IS done playing
		else:
			if self.loop:
				return
			else:
				self.stopAudio()

	def stopAudio(self):
		"""Stops the audio playing, returns the plot to state before audio started playing"""
		#stop the updating of the time line
		curdoc().remove_periodic_callback(self.perCallback)

		#stop playing the signal
		sd.stop()
		self.soundPlaying = 0

		#change play button back to play from pause
		self.playButton.label = "Play"

		logger.logData(source = "Signal handler",priority="INFO",msgType="Play done",msgData=())

		#restore plot to full signal
		self.drawActivePlot()

		#redraw sweep lines on the full signal plot
		startLine = self.p.select_one({'name': 'sweepStartLine'})
		startLine.visible = True

		endLine = self.p.select_one({'name': 'sweepEndLine'})
		endLine.visible = True

		#return time line to t=0
		timeLine = self.p.select_one({'name': 'timeLine'})
		timeLine.data_source.data["x"] = [0,0]

	def setupMapper(self):
		self.mapper = LinearColorMapper(palette="Inferno256", low=0, high=10)

	def updateMapperPalette(self,newColors):
		self.mapper.palette = newColors

	def updateMapperHigh(self,newHigh):
		self.mapper.high = newHigh

	def updateColorBar(self,times):
		colorBarPlot = self.gui.select_one({'name': 'colorBarPlot'})
		colorBarPlot.x_range.end = self.numSamples
		colorBar =  self.gui.select_one({'name': 'colorBar'})

		self.messedUpTs = times
		self.colorSource.data = {"x":self.sampleIndices,"place":self.messedUpTs}

		# if self.plotMode == 1:
		# 	for channelInd in self.activeChannels:
		# 		self.scatterSources[channelIndex].data = {"x":self.sampleIndices,"y":self.sampleIndices,"place":self.messedUpTs}

	def setupColorBar(self):
		colorTimeline = figure(height = 30, y_range = (-.5,.5),width=self.figureWidth,x_range = (0,10),toolbar_location=None,output_backend="webgl",name="colorBarPlot",tools="")

		colorTimeline.axis.visible = False
		colorTimeline.grid.visible = False

		# colorTimeline.image(image=range(self.numSamples),x=0,y=.5,dh=1,dw=1,fill_color={'field':"x",'transform': self.mappers[colorBarType-1]},
		#        name="cbar" + str(colorBarType))
		
		self.colorSource = ColumnDataSource({"x":range(10),"place":range(10)})

		# colorTimeline.rect(x="x", y=0, width=1, height=1,fill_color={'field':"place",'transform': self.mapper},name="colorBar",
		#        line_width=0.0,line_color= None,line_alpha = 0.0,source=colorSource
		#        )

		colorBar = Rect(x="x", y=0, width=1, height=1, fill_color={'field':"place",'transform': self.mapper},name="colorBar",
		       line_width=0.0,line_color= None,line_alpha = 0.0
		       )

		colorTimeline.add_glyph(self.colorSource, colorBar)

		self.colorBar = colorTimeline

	def getFFT(self):
		"""Plots the fast fourier transform of the active audio, returns a figure object"""
		fftHeight = self.numChannels
		self.p.y_range.end  = fftHeight

		maxFreq = self.sampleRate/2
		self.p.x_range.end = maxFreq

		for channelNum in self.activeChannels:
			sigPadded = self.signal[:,channelNum]

			# Determine frequencies
			f = np.fft.fftfreq(self.numSamples) * self.sampleRate

			#pull out only positive frequencies (upper half)
			upperHalf = int(len(f)/2)
			fHalf = f[:upperHalf]

			# Compute power spectral density
			psd = np.abs(np.fft.fft(sigPadded))**2 / self.numSamples

			#pull out only power densities for the positive frequencies
			psdHalf = psd[:upperHalf]

			#nromalize y vals
			psdHalf = psdHalf/max(psdHalf)

			#shift them to allow multiple channels
			psdHalf += channelNum

	
			self.p.line(fHalf,psdHalf)

	def lyricModeCallback(self, event):
		self.lyricMode = 1 - self.lyricMode

		if self.lyricMode:
			self.lyricsHandler.lyricModeButton.label = "Change to start lyric"
		else:
			self.lyricsHandler.lyricModeButton.label = "Change to end lyric"

	def dataTableCallback(self,att,old,new):
		if not self.activeChannels:
			logger.logData(source = "Signal handler",priority="WARN",msgType="Lyric empty",msgData=())
			return

		selectionIndex = self.lyricsHandler.lyricTableHandler.source.selected.indices[0]

		timestamp = self.lyricsHandler.lyricTableHandler.source.data["timestamps"][selectionIndex]
		lyricText = self.lyricsHandler.lyricTableHandler.source.data["lyrics"][selectionIndex]

		timestampSeconds = timestamp.seconds
		lyricSample = int(timestampSeconds * self.sampleRate)

		if self.lyricMode == 0:
			#update sweep line graphics
			self.sweepStartSample = lyricSample
			startLine = self.p.select_one({'name': 'sweepStartLine'})
			startLine.data_source.data = {'x': [lyricSample,lyricSample], 'y': self.yRange}

			logger.logData(source = "Lyrics",priority="INFO",msgType="Start lyric",msgData=(timestamp,lyricText))

		else:
			self.sweepEndSample = lyricSample
			endLine = self.p.select_one({'name': 'sweepEndLine'})
			endLine.data_source.data = {'x': [lyricSample,lyricSample], 'y': self.yRange}
			logger.logData(source = "Lyrics",priority="INFO",msgType="End lyric",msgData=(timestamp,lyricText))

	def setupLyricTable(self,lyricsFilename):
		lyricsPath = os.path.join(self.path,"lyrics",lyricsFilename)
		self.lyricsHandler = lyricsHandler(lyricsPath)

		self.lyricMode = 0

		self.lyricsHandler.lyricTableHandler.source.selected.on_change('indices', self.dataTableCallback)
		#create a loop toggle button and assigns a callback to it
		self.lyricsHandler.lyricModeButton.on_click(self.lyricModeCallback)

		self.lyricsGui = self.lyricsHandler.gui

def testSignalHandler():
	signalFilenames = ["interleaved.wav","2ch.wav","cats_000.wav","cats_001.wav"]
	signalFilename = signalFilenames[1]

	#direct sample add
	signalDirectory = "audio\\"
	sampleRate, originalSignal = wavfile.read(signalDirectory+signalFilename) #keep the original for master reference\

	#add on initialization
	sH = signalHandler(signal=originalSignal,sampleRate=sampleRate)

	# #add to empty
	# sH = signalHandler()
	# sH.addSignal(originalSignal,sampleRate)

	# #subtitles test
	# lyricsFilename = "beatles.srt"
	# sH = signalHandler(signalFilename = signalFilename,lyricsFilename = lyricsFilename)

	# # bad filename test
	# sH = signalHandler(signalFilename = "piaaa")

	sH.playSound()
	sH.showGui()