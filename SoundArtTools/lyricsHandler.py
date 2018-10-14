from bokeh.models.widgets import Toggle, Button
from bokeh.layouts import column, row

import srt
from dataTableGenerator import dataTableGenerator
from audioLogger import audioLogger
logger = audioLogger()

class lyricsHandler:

	def __init__(self,lyricsPath):
		logger.logData(source="Lyrics",priority="INFO",msgType="Setup start",
			msgData = ())

		self.toolWidth = 400
		self.buttonWidth = int(self.toolWidth/2)
		self.lyricsImported = 0
		self.importLyrics(lyricsPath)
		self.setupLyricTable()

		logger.logData(source="Lyrics",priority="INFO",msgType="Setup done",
			msgData = (self.lyricsImported))

	def importLyrics(self,lyricsPath):
		self.subtitleDict = {"lyrics":[],"timestamps":[]}

		#open the subtitles file and remove all non-ascii characters
		try:
			srtFile = open(lyricsPath,"r").read().encode('ascii', 'ignore').decode()

		except:
			logger.logData(source="Lyrics",priority="WARN",msgType="Import failed",msgData = (lyricsPath))
			return

		subs = srt.parse(srtFile)
		self.lyricsImported = 1
		for subEntry in subs:
			self.subtitleDict["lyrics"].append(subEntry.content)
			self.subtitleDict["timestamps"].append(subEntry.start)

			# startTime = subEntry.start
			# startTimestamp = startTime.seconds + startTime.microseconds/1000000.
			# self.subtitleDict["timestamps"].append(startTimestamp)

		#get the timestamp of the last entry to find the duration of the subtitle file
		lastTime = subEntry.start
		numEntries = len(self.subtitleDict['lyrics'])

		logger.logData(source="Lyrics",priority="INFO",msgType="Import",
			msgData = (lyricsPath,numEntries,lastTime))

	def setupLyricTable(self):
		self.lyricTableHandler = dataTableGenerator(self.subtitleDict)
		# self.dtg.source.selected.on_change('indices', self.dataTableCallback)
		self.importFileButton = Button(label="Import file", button_type="success",width=self.buttonWidth)

		self.lyricModeButton = Toggle(label="Change to end lyric", button_type="success",width=self.buttonWidth)
		self.gui = column(self.lyricTableHandler.gui,
			row(self.importFileButton,self.lyricModeButton)
			,width = self.toolWidth)

def testLyrics():
	from bokeh.io import show
	import os
	subPath = os.path.join("lyrics","testLyrics.srt")
	show(lyricHandler(subPath).gui)