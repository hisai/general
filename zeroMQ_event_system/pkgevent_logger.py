#!/usr/bin/env blue-python2.7
''' 
This script will listen to "Response" channel on ZeroMQ and logging the events of client's action
'''
import sys
import os
import zmq
import time
import subprocess
from datetime import datetime
import pkgutils
import ConfigParser as configparser
import logging

# Reading config
conf_file='/etc/pkgevent.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    zmq_host=config.get('common', 'zmq_host')
    pub_port=config.get('common', 'pub_port')
    events_logfile=config.get('common', 'events_logfile')
    response_topic=config.get('common', 'response_topic')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())
    sys.exit(2)

pkgutils.get_logger('events_logger', events_logfile)
events_logger = logging.getLogger('events_logger')


# Create socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect ("tcp://%s:%s" % (zmq_host, pub_port))
socket.setsockopt(zmq.SUBSCRIBE, response_topic)

events_logger.info("Starting pkgevent_listener")

if __name__ == '__main__':
    while True:
        string = socket.recv()
        if string:
            timenow = datetime.now()
            topic, message = string.split("=>")
            events_logger.info('Receive event via ZeroMQ - [%s] - %s' %(response_topic, message))
            time.sleep(0.3)

