#!/usr/bin/env python

import sys
try:
 	import pygtk
  	pygtk.require("2.0")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)



class HellowWorldGTK:
	"""This is an Hello World GTK application"""

	def __init__(self):
		
		#Set the Glade file
		self.gladefile = "footpedal.glade"  
	        self.wTree = gtk.glade.XML(self.gladefile) 
		
		#Get the Main Window, and connect the "destroy" event
		self.window = self.wTree.get_widget("window1")
		if (self.window):
			self.window.connect("destroy", gtk.main_quit)

		self.window.show_all()


if __name__ == "__main__":
	hwg = HellowWorldGTK()
	gtk.main()
