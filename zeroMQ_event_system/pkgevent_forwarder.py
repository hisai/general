#!/usr/bin/env blue-python2.7
'''
ZeroMQ Forwarder which forward messages messages from SUB interface to PUB interface 
https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/devices/forwarder.html
'''
import zmq
import time
import sys
from  multiprocessing import Process
from optparse import OptionParser

def main():
    try:
        context = zmq.Context(1)
        frontend = context.socket(zmq.SUB)
        frontend.bind("tcp://0.0.0.0:%s" % 5559)
        frontend.setsockopt(zmq.SUBSCRIBE, "")

        backend = context.socket(zmq.PUB)
        backend.bind("tcp://0.0.0.0:%s" % 5560)

        zmq.device(zmq.FORWARDER, frontend, backend)
        print "Starting ZeroMQ forwarder on port %s and %s" % (pub_port,sub_port)
    except Exception, e:
        print e
        print "Bringing down ZeroMQ forwarder"


if __name__ == '__main__':
    p = Process(target=main)
    p.start()
    p.join()
