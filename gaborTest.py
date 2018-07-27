import scipy.io.wavfile
from scipy.stats import norm
from scipy.io import wavfile
from scipy import signal
import numpy as np

from bokeh.plotting import figure, show, output_file,curdoc
from bokeh.layouts import row, widgetbox, column
from bokeh.models import CustomJS, Slider, RangeSlider, ColumnDataSource, LinearColorMapper
from bokeh.models.widgets import Button, RadioButtonGroup, Div
import sounddevice as sd

from GrainShuffler import granularize_signal,shuffle_grains
class wavRearranger:

	def __init__(self):
		self.sample_rate, self.originalSignal = scipy.io.wavfile.read('cats\\cats10_000.wav')  # File assumed to be in the same directory
		self.originalNumSamples = len(self.originalSignal)
		self.originalSignalDuration = self.originalNumSamples/float(self.sample_rate)

		self.minGrainSz = int(1e-4 * self.sample_rate)
		self.maxGrainSz = int(1e-1 * self.sample_rate)
		self.modeGrainSz = int(10*self.minGrainSz)
		self.pctToShift = 0.3
		self.shiftStandardDev = 20
		self.shiftMean = 0

		self.startSample = 0
		self.endSample = self.originalNumSamples  -1
		self.numSamples = self.endSample - self.startSample
		self.ts = range(self.numSamples)

		self.signal = self.originalSignal[self.startSample:self.endSample]
		self.messedUpSignal = self.signal
		self.messedU9pTs = self.ts

		self.setupControls()
		self.setupPlots()
		self.setupMasterWindow()

	def playSound(self):
		sd.play(self.messedUpSignal, self.sample_rate,blocking=True)

	def timeSliderCallback(self,attr,old,new):
		newTimeRange = new
		self.startSample = int(newTimeRange[0] * self.sample_rate)
		self.endSample = int(newTimeRange[1] * self.sample_rate)
		self.numSamples = self.endSample - self.startSample

		self.signal = self.originalSignal[self.startSample:self.endSample]
		self.ts = range(self.numSamples)

	def grainSizeSliderCallback(self,attr,old,new):
		newMin = new[0]
		newMax = new[1]

		self.minGrainSz = int(newMin * self.sample_rate)
		self.maxGrainSz = int(newMax * self.sample_rate)

		self.modeGrainSz = int(.5* (self.minGrainSz + self.maxGrainSz))

	def log_specgram(audio, sample_rate, window_size=20,
	                 step_size=10, eps=1e-10):
	    nperseg = int(round(window_size * sample_rate / 1e3))
	    noverlap = int(round(step_size * sample_rate / 1e3))
	    freqs, times, spec = signal.spectrogram(audio,
	                                    fs=sample_rate,
	                                    window='hann',
	                                    nperseg=nperseg,
	                                    noverlap=noverlap,
	                                    detrend=False)
	    return freqs, times, np.log(spec.T.astype(np.float32) + eps)

	def getSpectrogram(self):
		freqs,times,data = self.log_specgram(self.signal,self.sample_rate)
		plot = figure(height = 800,width = 1200,x_range = (0,max(times)),y_range=(0,max(freqs)))
		plot.image(image=[data], x=0, y=0, dw=max(times), dh=max(freqs), palette="Spectral11")

	def shuffleButtonCallback(self):
		grainMarkers = granularize_signal(self.signal, self.minGrainSz, self.modeGrainSz, self.maxGrainSz)
		self.messedUpSignal = shuffle_grains(self.signal,grainMarkers, self.pctToShift,self.shiftStandardDev)
		self.messedUpTs = shuffle_grains(self.ts,grainMarkers, self.pctToShift,self.shiftStandardDev)
		self.updateGUI()

	def fractionOfWaveToDisturbCallback(self,attr,old,new):
		self.pctToShift = new
	def sampleDisplacementWidthStdCallback(self,attr,old,new):
		self.shiftStandardDev = new

	def updateGUI(self):
		self.setupPlots()
		self.windowLayout.children[0] = self.signalPlotRow
		
		# curdoc().(windowLayout)

	def setupControls(self):
		timeWindowSlider = RangeSlider(start=0, end=self.originalSignalDuration, value=[0,self.originalSignalDuration], step=.05,title="Wav File Window",width = 300)#, callback=timeSliderCallback)
		timeWindowSlider.on_change("value",self.timeSliderCallback)

		openFileButton = Button(label="Open file", button_type="success")

		self.switcherooButton = Button(label="Switcheroo", button_type="success")
		self.switcherooButton.on_click(self.shuffleButtonCallback)


		playButton =  Button(label="Play", button_type="success")
		playButton.on_click(self.playSound)

		fractionOfWaveToDisturbSlider = Slider(start=0, end=1, value=self.pctToShift,step=.1,title="Portion Of Wave To Disturb")#, callback=timeSliderCallback)
		fractionOfWaveToDisturbSlider.on_change("value",self.fractionOfWaveToDisturbCallback)

		grainSizeSlider = RangeSlider(start=0, end=.2, value=[1e-4,1e-1],step=.0001,title="Max Chunk Time",width=200)#, callback=timeSliderCallback)
		grainSizeSlider.on_change("value",self.grainSizeSliderCallback)

		# maxSampleStdSlider = Slider(start=1, end=100, value=1,step=.1,title="Max Chunk Time",width=200)#, callback=timeSliderCallback)

		maxSamplePlot = figure(height = 200,width = 200)#x_range = (0,len(movedSignal)))
		maxSamplePlot.yaxis.visible = False
		maxSamplePlot.grid.visible = False

		ts = range(0,10)
		probs = range(10,0,-1)
		maxSamplePlot.line(ts,probs)
		maxSampleWindow = column(maxSamplePlot,grainSizeSlider)

		sampleDisplacementWidthSlider = Slider(start=-10, end=10, value=self.shiftMean,step=1,title="Sample Displacement Average",width=200)
		sampleDisplacementWidthStdSlider = Slider(start=0, end=30, value=self.shiftStandardDev,step=1,title="Sample Displacement Std",width=200)
		sampleDisplacementWidthStdSlider.on_change("value",self.sampleDisplacementWidthStdCallback)

		sampleDisplacementPlot = figure(height = 200,width=200,x_range=(-4,4),toolbar_location=None)
		sampleDisplacementPlot.axis.visible = False
		sampleDisplacementPlot.grid.visible = False

		ts = range(-10,10)
		sampleDisplacementPlot.line(ts,norm.pdf(ts))
		sampleDisplacementWidthWindow = column(sampleDisplacementPlot,sampleDisplacementWidthSlider,sampleDisplacementWidthStdSlider)

		# sampleDisplacementWidthColumn = column(sampleDisplacementWidthText,sampleDisplacementWidthSlider,height=60)

		#temporalInfo - moving forwards only, backwards only, or both
		directionOfTravelButtons = RadioButtonGroup(labels=["Forwards", "Backwards", "Both"], active=0)
		directionOfTravelText = Div(text="<b>Direction of travel:</b>",width=200, height=1)
		directionOfTravelColumn = column(directionOfTravelText,directionOfTravelButtons,height=60)

		self.controlsSlidersRow = row(maxSampleWindow,sampleDisplacementWidthWindow)
		self.controlButtonsColumn = column(openFileButton,timeWindowSlider,fractionOfWaveToDisturbSlider,directionOfTravelColumn,self.switcherooButton,playButton)

		self.controlsLayout = row(self.controlsSlidersRow,self.controlButtonsColumn,width=800)

	def setupPlots(self):

		colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
		mapper = LinearColorMapper(palette="Inferno256", low=0, high=self.numSamples)

		#number of chunks to 
		ogPlot = figure(title="Original Signal",toolbar_location=None,x_axis_type="datetime")#,width = 300)
		ogPlot.line(self.ts,self.signal)
		ogPlot.yaxis.visible = False
		ogPlot.grid.visible = False

		modifiedPlot = figure(title="Modified Signal",toolbar_location=None,x_axis_type="datetime",  x_range=ogPlot.x_range, y_range=ogPlot.y_range,)

		modifiedPlot.line(self.ts,self.messedUpSignal)
		modifiedPlot.yaxis.visible = False
		modifiedPlot.grid.visible = False

		linePlotSource = ColumnDataSource(dict(x=self.ts,xBad = self.messedUpTs))

		ogLinePlot = figure(height = 60, y_range = (-.5,.5),
			x_range = (0,self.numSamples),toolbar_location=None)

		ogLinePlot.axis.visible = False
		ogLinePlot.grid.visible = False

		ogLinePlot.rect(x="x", y=0, width=1, height=1, source = linePlotSource,
		       fill_color={'field':"x",'transform': mapper},
		       line_color= None,line_alpha = 0.0
		       )

		ogWindow = column(ogPlot,ogLinePlot)

		movedLinePlot = figure(height = 60,y_range = (-.5,.5),toolbar_location=None,
			x_range = (0,self.numSamples))

		movedLinePlot.axis.visible = False
		movedLinePlot.grid.visible = False

		movedLinePlot.rect(x="xBad", y=0, width=1, height=1, source = linePlotSource,
		       fill_color={'field':"x",'transform': mapper},
		       line_color= None,line_alpha = 0.0
		       )

		modifiedWindow = column(modifiedPlot,movedLinePlot)

		self.signalPlotRow = row(ogWindow,modifiedWindow)

	def setupMasterWindow(self):

		self.windowLayout = column(self.signalPlotRow,self.controlsLayout)
		# print dir(self.windowLayout/)
		# print self.windowLayout.children
		curdoc().add_root(self.windowLayout)

		# show(windowLayout)

wavRearranger()