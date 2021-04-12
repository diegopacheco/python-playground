﻿import time
import sys

import stomp

class Listener(object):
    def on_error(self, headers, message):
        print '[message-sucker.py] sucking ERROR message: %s' % message

    def on_message(self, headers, message):
		print '[message-sucker.py] sucking message: %s Kb' %  (len(message) / 1024)
		

conn=stomp.Connection([('127.0.0.1',61613)])
conn.add_listener(Listener())

conn.start()
conn.connect(wait=True)

conn.subscribe(destination='/queue/my_queue_out', ack='auto')

time.sleep(10000)
conn.disconnect()
