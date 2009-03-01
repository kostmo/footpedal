#!/usr/bin/env python


# http://www.execommsys.com/VEC%20Professional%20Foot%20Pedals.htm

# 05f3:00ff PI Engineering, Inc.


hidfilename = "/dev/usb/hiddev0"
signal_chars = [4, 12, 20]
WORD_LENGTH = 24

if __name__=="__main__":

	try:
		hidfile = open(hidfilename)
	except IOError:
		print "You need permission to access the device.  Type the following:"
		print "sudo chmod a+r /dev/usb/hiddev0"
		exit(1)

	prev_state = [0]*3

	while True:

		mystring = hidfile.read(WORD_LENGTH)

		buttons = [ord(mystring[i]) for i in signal_chars]

		print "Current state:", buttons, "Previous state:", prev_state
		prev_state = buttons

	hidfile.close()

