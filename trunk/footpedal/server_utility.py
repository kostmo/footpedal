#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk, gobject
import threading

import os

# =========================

class ServerThread(threading.Thread):

	"""Server thread"""

	hidfilename = "/dev/usb/hiddev0"
	signal_chars = [4, 12, 20]
	WORD_LENGTH = 24

	stopthread = threading.Event()

	# -----------------------------
	def __init__(self, controller_window):
		threading.Thread.__init__(self)

		self.setDaemon(True)

		self.controller_window = controller_window

		self.prev_state = [0]*3

	# -----------------------------
	def run(self):

		try:
			hidfile = open(self.hidfilename)
		except IOError:

			msg = "You need permission to access the device.  Type the following:\n"
			msg += "sudo chmod a+r " + self.hidfilename
			self.controller_window.hello(None, title="Permission lacking", message=msg)
			return


		while not self.stopthread.isSet():

			mystring = hidfile.read(self.WORD_LENGTH)
			buttons = [ord(mystring[i]) for i in self.signal_chars]

			self.handle_pedal_press(buttons)


		hidfile.close()

	# -----------------------------
	def handle_pedal_press(self, buttons):


#		print "Current state:", buttons, "Previous state:", self.prev_state


		any_down = reduce(lambda x, y: x or y, buttons)
		self.controller_window.set_foot( any_down )


		treestore = self.controller_window.pedalpress_treeview.get_model()
		toplevel_iter = treestore.get_iter_first()

		for i, value in enumerate(buttons):
			treestore.set_value(toplevel_iter, 2, value)
			toplevel_iter = treestore.iter_next(toplevel_iter)


		function_group = self.controller_window.pedal_function_selector.get_active()

		prev_any_down = reduce(lambda x, y: x or y, self.prev_state)
		if not prev_any_down:

			active_button = -1
			for idx in [0, 2, 1]:	# Priority: Left, Center, Right
				if buttons[idx]:
					active_button = idx
					break
			
			if active_button >= 0:
				# Perform pedal action:

				key = self.controller_window.command_matrix[function_group][active_button]
				if function_group == 0:
					self.special_key_sequence( key )

				else:
					os.system( 'xte "key ' + key + '"' )

				print self.controller_window.pedal_function_groups[function_group][active_button]


		self.prev_state = buttons

	# -----------------------------
	def special_key_sequence(self, key):

		os.system( 'xte "keydown Control_L"' )
		os.system( 'xte "key ' + key + '"' )
		os.system( 'xte "keyup Control_L"' )

	# -----------------------------
	def stop(self):
		"""send QUIT request to http server running on localhost:<port>"""

		self.stopthread.set()

# =========================

class FootpedalServer(gtk.Window):


	def cb_dummy(self, widget):
		print "Dummy callback."


	DEFAULT_PORT = 46645
	X11_KEY_DEFINITIONS = "/usr/share/X11/XKeysymDB"
	ANDROID_ICON = "foot.png"

	feet_images = ["foot_up.png", "foot_down.png"]

	pedal_identifiers = ["Left", "Center", "Right"]


	# -------------------------------------------
	def __init__(self):
		gtk.Window.__init__(self)


		# These are "default" or "builtin" presets
		self.pedal_function_groups = [
			["Cut", "Copy", "Paste"],
			["VolDown", "Mute", "VolUp"],
			["Rew", "Play", "FF"],
			["Home", "Down", "PgDown"]
		]

		self.command_matrix = [
			["x","c","v"],
			["XF86AudioLowerVolume", "XF86AudioMute", "XF86AudioRaiseVolume"],
			["XF86AudioPrev", "XF86AudioPlay", "XF86AudioNext"],
			["Home", "Down", "Page_Down"]
		]




		import sys
		self.img_directory = sys.path[0]
		from os import path
		self.icon_path = path.join(self.img_directory, self.ANDROID_ICON)
		


		self.connect("delete_event", self.delete_event)
		self.connect("destroy", self.destroy)
		self.set_border_width(10)

		self.hidden_window = True
		self.pynotify_enabled = False

		
		
		try:
			import pynotify
			if pynotify.init("My Application Name"):
				self.pynotify_enabled = True
			else:
				print "there was a problem initializing the pynotify module"

		except:
			print "you don't seem to have pynotify installed"




		vbox = gtk.VBox(False, 5)

		button = gtk.Button("Show message")
		button.connect("clicked", self.hello)
#		vbox.pack_start(button, False, False)



		lil_hbox = gtk.HBox(False, 5)
		lil_hbox.set_tooltip_text("Select pedal functions")
		vbox.pack_start( lil_hbox, False, False)
		lil_hbox.pack_start( gtk.Label("Operation Mode:"), True, True)
		self.pedal_function_selector = gtk.combo_box_new_text()
		for src in self.pedal_function_groups:
			self.pedal_function_selector.append_text( "/".join(src) )
		self.pedal_function_selector.append_text( "New..." )

		lil_hbox.pack_start( self.pedal_function_selector, False, False)
		self.pedal_function_selector.connect("changed", self.cb_functions_changed)

		button = gtk.Button("Edit...")
		lil_hbox.pack_start( button, False, False)
		button.connect("clicked", self.cb_edit_dialog)



		ts = gtk.ListStore(str, str, bool)
		for s in self.pedal_identifiers:
			ts.append( [s, "", False] )
		self.pedalpress_treeview = gtk.TreeView( ts )
		self.pedalpress_treeview.set_tooltip_text("Pedal status")
		self.pedalpress_treeview.set_rules_hint(True)	# alternates row coloring automatically
		self.pedalpress_treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)

		for i, new_col_label in enumerate(["Pedal", "Function", "Depressed"]):
			cell = gtk.CellRendererText()

			
			if i==2:
				tvcolumn = gtk.TreeViewColumn(new_col_label, cell)
				tvcolumn.set_cell_data_func(cell, self.treeview_renderfunc)
			else:
				tvcolumn = gtk.TreeViewColumn(new_col_label, cell, text=i)

			tvcolumn.set_expand(True)
			self.pedalpress_treeview.append_column(tvcolumn)

		vbox.pack_start(self.pedalpress_treeview, False, False)



		self.add(vbox)

		vbox.show_all()


		self.my_status_icon = gtk.StatusIcon()
		self.my_status_icon.set_tooltip("Footswitch")

		self.my_status_icon.connect("activate", self.toggle_window)
		self.my_status_icon.connect("popup-menu", self.systray_popup_callback)

		self.set_icon_from_file( self.icon_path )
		self.set_title("Foot pedal")


		self.set_foot(False)
		self.pedal_function_selector.set_active(1)


	# -------------------------------------------
	def cb_dialog_close(self, dialog):

		# FIXME: This never gets called.

		print "Foo"

		return True

	# -------------------------------------------
	def cb_edit_dialog(self, widget):

		d = gtk.Dialog("My dialog",
                     self,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
		)

		d.connect("close", self.cb_dialog_close)	# This apparently does nothing.



		function_group = self.pedal_function_selector.get_active()

		ts = gtk.ListStore(str, str, str)


		if function_group < len(self.pedal_function_groups):
			for i in range(3):
				ts.append( 
					[
						self.pedal_identifiers[i],
						self.pedal_function_groups[function_group][i],
						self.command_matrix[function_group][i]
					]
				)
		else:
			for i in range(3):
				ts.append( 
					[
						self.pedal_identifiers[i],
						"Command "+`i`,
						""
					]
				)

		tv = gtk.TreeView( ts )
		tv.set_tooltip_text("Pedal status")
		tv.set_rules_hint(True)	# alternates row coloring automatically
		tv.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_VERTICAL)

		for i, new_col_label in enumerate(["Pedal", "Function", "Keystroke"]):
			cell = gtk.CellRendererText()

			
			tvcolumn = gtk.TreeViewColumn(new_col_label, cell, text=i)
			if i:
				cell.set_property('editable', True)


			tvcolumn.set_expand(True)
			tv.append_column(tvcolumn)

		d.vbox.pack_start(tv, False, False)
		d.vbox.show_all()


		d.run()

		# TODO:
		# Save the new values.

		d.destroy()

	# -------------------------------------------
	def cb_functions_changed(self, widget):
		
		function_group = widget.get_active()
		if function_group == len(widget.get_model()) - 1:
			self.cb_edit_dialog(widget)
			return

		treestore = self.pedalpress_treeview.get_model()
		toplevel_iter = treestore.get_iter_first()

		labels = self.pedal_function_groups[function_group]

		for value in labels:
			treestore.set_value(toplevel_iter, 1, value)
			toplevel_iter = treestore.iter_next(toplevel_iter)

	# -------------------------------------------
	def treeview_renderfunc(self, column, cell_renderer, tree_model, my_iter):

		data_value = tree_model.get_value(my_iter, 2)
		if data_value:
			cell_renderer.set_property('text', "X")
		else:
			cell_renderer.set_property('text', "")

	# -----------------------------
	def show_preferences_dialog(self, widget):

		self.hidden_window = True
		self.toggle_window(widget)

	# -----------------------------
	def cb_menuitem_activate(self, menuitem, idx):

		self.pedal_function_selector.set_active(idx)

		return False

	# -----------------------------
	def build_menu(self):
		menu = gtk.Menu()

		command_submenu = gtk.Menu()

#		grp = None
		for i, src in enumerate(self.pedal_function_groups):

#			grp = gtk.RadioMenuItem( grp, "/".join(src) )
			grp = gtk.MenuItem( "/".join(src) )
			grp.connect("activate", self.cb_menuitem_activate, i)
			command_submenu.append( grp )

#		grp.set_active(True)





		temp_item = gtk.MenuItem("Command set")
		temp_item.set_submenu( command_submenu )
		menu.append(temp_item)

		temp_item = gtk.MenuItem("Configure...")
		temp_item.connect("activate", self.show_preferences_dialog)
		menu.append(temp_item)

		temp_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		temp_item.connect("activate", self.destroy)
		menu.append(temp_item)

		menu.show_all()
		return menu
	# -----------------------------

	def systray_popup_callback(self, status_icon, button, activate_time):
		my_popup_menu = self.build_menu()
		my_popup_menu.popup(None, None, None, button, activate_time, data=None)

	# -----------------------------

	def toggle_window(self, status_icon):
		if self.hidden_window:
			self.show()
			self.hidden_window = False
		else:
			self.hide()
			self.hidden_window = True


	# -------------------------------------------
	def set_foot(self, down):

		from os import path
		icon_path = path.join(self.img_directory, self.feet_images[down])
		self.my_status_icon.set_from_file( icon_path )

	# -------------------------------------------
	def hello(self, widget, title="Title", message="message"):

		if not self.pynotify_enabled:
			return

		n = pynotify.Notification(title, message)

		pixbuf = gtk.gdk.pixbuf_new_from_file( self.icon_path )
#		n.set_urgency(pynotify.URGENCY_CRITICAL)
#		n.set_category("device")
		n.set_icon_from_pixbuf( pixbuf )
 		n.set_timeout(5000)


		# Note: When this is enabled, the notification bubble may be delayed
		# until the app regains focus, which may be a long time and requires user interaction
#		n.attach_to_status_icon( self.my_status_icon )


		# Note: The "pie" countdown only shows up when we add a button, like this:
		n.add_action("empty", "Do it now", self.cb_dummy)

		if not n.show():
			print "Well then..."

	# -------------------------------------------
	def delete_event(self, widget, event, data=None):

		self.hidden_window = False
		self.toggle_window(widget)

		return True

#		return False

	# -------------------------------------------
	def destroy(self, widget, data=None):
		print "destroy signal occurred"
		gtk.main_quit()


# =========================

if __name__ == "__main__":

	gobject.threads_init()

	fs = FootpedalServer()

	server_thread = ServerThread(fs)
	server_thread.start()

	gtk.main()

	print "Shutting down..."

	server_thread.stop()

