#!/usr/bin/env python


# http://www.execommsys.com/VEC%20Professional%20Foot%20Pedals.htm

# 05f3:00ff PI Engineering, Inc.


hidfilename = "/dev/usb/hiddev0"
signal_chars = [4, 12, 20]
WORD_LENGTH = 24

if __name__=="__main__":

	print "Depress pedal to test..."

	hidfile = None
	try:
		hidfile = open(hidfilename)
	except IOError:
		print "You need permission to access the device.  Type the following:"
		print "sudo chmod a+r /dev/usb/hiddev0"
		exit(1)

	prev_state = [0]*3




	# Trick adopted from http://stackoverflow.com/questions/375427/non-blocking-read-on-a-stream-in-python/1810703#1810703
	# makes a non-blocking file
	import fcntl, os
	fd = hidfile.fileno()
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

	count = 0
	while True:


		# XXX There was a problem (Issue 2) where the hidfile.read(WORD_LENGTH) line
		# froze. I reduced the read bytes to 1 (i.e. hidfile.read(1)), and found that
		# the read would only freeze at the first byte at the beginning of a message
		# after a previous message was complete.
		# The approach I took to solve this was to make the I/O nonbocking.
		# To reduce CPU consumption, I sleep when the buffer is not yet full.

		try:
			mystring = hidfile.read(WORD_LENGTH)
		except:
			import time
			time.sleep(0.1)
			continue


		print "="*40, "COUNT:", count, "="*40



		print "Ord characters:", map(ord, mystring)

		'''
		buttons = [ord(mystring[i]) for i in signal_chars]
		print "Current state:", buttons, "Previous state:", prev_state
		prev_state = buttons
		'''

		count += 1

	hidfile.close()

