import numpy as np
import sounddevice as sd

from bokeh import events
from bokeh.plotting import figure, show, output_file,curdoc
from bokeh.layouts import row, widgetbox, column
from bokeh.models import CustomJS, Slider, RangeSlider, ColumnDataSource, LinearColorMapper, MultiLine
from bokeh.models.widgets import Button, RadioButtonGroup, Div, Panel, Tabs
from bokeh.models.glyphs import Text
class timeDrawer:
	"""A tool for visually drawing microsound intervals"""
	def __init__(self):

		self.currentNextIndex = 0
		self.xs = []
		self.ys = []

		self.mouseEventIndex = 0

		self.chunkLengths = []
		self.chunkTimestamps = [0.]

		# self.lineSource = ColumnDataSource(data = {
		# 	"xs":[[]],
		# 	"ys":[[]],
		# 	}
		# )
		self.chunkIndex = 0
		self.nextNextTimestamp = 0

		plot = self.drawFigure()
		self.gui = column(plot)

		show(self.gui)
		curdoc().add_root(self.gui)

	def lineUpdate(self,event):
		if self.mouseEventIndex>20:
			self.mouseEventIndex = 0
			return

		if self.currentNextIndex > 9:
			del self.xs
			del self.ys
			return

		self.mouseEventIndex+=1
		xVal = round(event.x,2)

		if xVal > (self.currentNextIndex)+1.5:
			return

		yVal = round(event.y,2)

		self.xs.append(xVal)
		self.ys.append(yVal)


		self.nextNextTimestamp  = self.currentNextIndex + yVal

		# self.lineSource.data['xs'][0].append(xVal)
		# self.lineSource.data['ys'][0].append(yVal)


		if xVal > self.currentNextIndex:
			if yVal <= 0:
				self.chunkLengths.append(0)
				self.currentNextIndex += 1.0
				nextTimestamp = self.chunkTimestamps[-1] + 1.0

			else:
				self.chunkLengths.append(yVal)
				self.currentNextIndex += yVal
				nextTimestamp = self.chunkTimestamps[-1] + self.chunkLengths[-1]

			self.chunkIndex +=1
			self.chunkTimestamps.append(round(nextTimestamp,2))

		self.gui.children[0] = self.drawFigure()

	def drawFigure(self):
		p = figure(x_range=(0, 10), y_range=(-1, 5), width=1600, height=1000, tools="", title='Poly Draw Tool',toolbar_location=None)

		for chunkInd,tVal in enumerate(self.chunkTimestamps):
			p.line(x =[tVal,tVal],y=[-10,10],line_width=5)


			textSource =  ColumnDataSource(data = {"xs":[tVal],"ys":[4],"label":[str(chunkInd)]})
			text = Text(x="xs", y="ys", text="label", text_color="black")
			p.add_glyph(textSource,text)

		p.line(x =[self.currentNextIndex,self.currentNextIndex],y=[-10,10],line_width=5)
		p.line(x =[self.nextNextTimestamp,self.nextNextTimestamp],y=[-10,10],line_width=5)

		lineSource = ColumnDataSource(data = {
			"xs":[self.xs],
			"ys":[self.ys],
			}
		)

		l1 = p.multi_line(xs="xs",ys="ys",source=lineSource, line_width=5, alpha=0.4, color='red')
		p.on_event(events.MouseMove,self.lineUpdate)

		return p

timeDrawer()