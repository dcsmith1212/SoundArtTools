from signalHandler import signalHandler
from signalRearranger import masterRearranger
from multiSignalSplicer import multiSignalSplicer

def showSignalSplicer(signalFilenames):
	multiSignalSplicer(signalFilenames).showGui()

def showSignalRearranger(signalFilename):
	masterRearranger(signalFilename).showGui()

def showSignalHandler(signalFilename):
	signalHandler(signalFilename = signalFilename).showGui()

toolFunctions = {
	"Player":showSignalHandler,
	"Rearranger":showSignalRearranger,
	"Splicer":showSignalSplicer,
}

validTools = toolFunctions.keys()

def soundArtTools(commandLineArgs):
	numArgs = len(commandLineArgs)

	if numArgs<2:
		print ("Specify which tool to use")
		return
	else:
		toolToShow = commandLineArgs[1]
		if toolToShow not in validTools:
			print ("Please enter a valid tool")
			return
		if numArgs>2:
			if numArgs==3:
				toolArgs = commandLineArgs[2]
			else:
				toolArgs = commandLineArgs[2:]
		else:
			toolArgs = ""

		toolFunction = toolFunctions[toolToShow]
		toolFunction(toolArgs)

import sys
args = sys.argv
soundArtTools(args)