from colorama import init, Fore,Back, Style
import datetime
import os
from loggerMessages import *

class audioLogger:
	"""class to print logs to the console and to write them to the appropriate log files"""

	def __init__(self):
		init(autoreset=True) #setup colorama to use ANSI codes, and reset style after every print statement
		self.setupLoggerVariables()

	def setupLoggerVariables(self):
		self.logSourceStrings = {
			"Signal handler" : signalHandlerMessages,
			"Lyrics" : lyricsMessages,
			"Time draw" : timeDrawerMessages,
			"Rearranger tools" : rearrangerToolsMessages,
			"Master rearranger" : masterRearrangerMessages,
			"Splicer tools" : splicerToolsMessages,
			"Master splicer" : masterSplicerMessages
			}

		self.colorMappings = {
			"CRIT": Fore.RED + Style.BRIGHT,
			"INFO" : Fore.GREEN + Style.BRIGHT,
			"WARN": Fore.YELLOW + Style.BRIGHT
			}

		self.logPath = os.path.join("logs")
		self.logFilename = os.path.join(self.logPath,"log.txt")

	def parseLogDict(self,logIn):
		messageSource = logIn["Source"]
		messageType = logIn["MessageType"]
		logMessage = logIn["MessageData"]
		priority = logIn["Priority"]

		return messageSource,messageType,priority,logMessage

	def writeLogToFile(self,logToWrite):
		logFile = open(self.logFilename,"a")
		logFile.write(logToWrite + "\n")
		logFile.close()

	def printLog(self,datestamp,timestamp,logPriority,log):
		print (datestamp, timestamp, self.colorMappings[logPriority] + logPriority, log)

	def getDateTimestamp(self):
		# get the current datetime in str format with no trailing microseconds -- output form is 
		# YYYY-MM-DD HH:MM:SS.mmm
		return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3].split(" ")

	def log(self,logIn):
		messageSource,messageType,priority,logMessageData = self.parseLogDict(logIn)
		datestamp, timestamp = self.getDateTimestamp()
		
		logMessage = messageSource + " -- " + (self.logSourceStrings[messageSource][messageType] % logMessageData)
		logToWrite = datestamp + " " + timestamp + " " + priority + " " + logMessage

		self.printLog(datestamp,timestamp,priority,logMessage)
		self.writeLogToFile(logToWrite)

	def logData(self,source,priority,msgType,msgData):
		logMessage = {
			"Source" : source,
			"Priority" : priority,
			"MessageType" : msgType,
			"MessageData" : msgData
		}
		self.log(logMessage)