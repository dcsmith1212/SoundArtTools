from bokeh.plotting import show, ColumnDataSource, curdoc
from bokeh.models.widgets import HTMLTemplateFormatter, DataTable, DateFormatter, TableColumn, Div, NumberFormatter
from bokeh.layouts import widgetbox
from bokeh.models import NumberFormatter
from datetime import date, datetime, timedelta
from random import randint, random

class dataTableGenerator():
	def __init__(self,data):
		tfmt = DateFormatter(format="%M:%S")
		tfmt = NumberFormatter(format="00:00:00")
		self.metadata = [
			self.generateTableMetadataEntry(field="name", title="Time",width=3,formatter=tfmt),
		    self.generateTableMetadataEntry(field="lyrics", title="Lyrics",width=50),
		    ]

		dictionary = {
			"title":"Lyrics",
			"data":data,
			"metadata":self.metadata
			}
		self.createTable(dictionary)

	def createTable(self,dictionaryIn):
		title = dictionaryIn["title"]
		div = Div(text=title, width=55, height=10)

		tableMetadata = dictionaryIn["metadata"]

		columns = [TableColumn(
			field=tableRowInfo["field"],
			title=tableRowInfo["title"],
			width=tableRowInfo["width"],
			formatter=tableRowInfo["formatter"]
			)
			for tableRowInfo in tableMetadata]

		self.source = ColumnDataSource(dictionaryIn["data"])
		dataTable = DataTable(source=self.source, columns=columns,index_position = None, width=400, height=280)

		self.gui = widgetbox(div,dataTable)

	def generateTableMetadataEntry(self,field,title,width=10,formatter=None):
		return {"field":field,"title":title,"width":width,"formatter":formatter}

# import srt
# filename = "beatles.srt"
# srtFile = open(filename,"r").read().encode('ascii', 'ignore').decode("utf8")

# subs = srt.parse(srtFile)
# entryDict = {"lyrics":[],"timestamps":[]}
# for subEntry in subs:
# 	entryDict["lyrics"].append(subEntry.content)
# 	startTime = subEntry.start
# 	startTimestamp = startTime.seconds + startTime.microseconds/1000000.
# 	# print (startTimestamp)
# 	entryDict["timestamps"].append(startTimestamp)

# print (entryDict["lyrics"])
# print (entryDict["timestamps"])
# dtg = dataTableGenerator(entryDict)


# show(dtg.gui)

# # def callback(attr, old, new):
#     try:
# 		# selected_index = dtg.source.selected["1d"]["indices"][0]
# 		selectionIndex=dtg.source.selected.indices[0]

# 		print dtg.source.data["timestamps"][selectionIndex]
# 		# print dtg.source[selectionIndex
# 		# table_row.value = str(selected_index)
# 		print selectionIndex
#     except IndexError:
#         pass

# dtg.source.selected.on_change('indices', callback)


# dtg.source.on_change('selected', function_source)
# curdoc().add_root(dtg.gui)
# aF.showGUI()