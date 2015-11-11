#!/usr/bin/env blue-python2.7
import zmq
import random
import sys
import os
import time
import logging
from optparse import OptionParser
import pkgutils
import ConfigParser as configparser
import json
from datetime import datetime

if os.getuid() != 0:
    print "This script must be runs as root"
    sys.exit(0)

# Reading config
conf_file='/etc/pkgevent.ini'
packagebuilder_ini = '/etc/packagebuilder.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    zmq_host=config.get('common', 'zmq_host')
    yum_master=config.get('common', 'yum_master')
    sub_port=config.get('common', 'sub_port')
    pub_port=config.get('common', 'pub_port')
    events_logfile=config.get('common', 'events_logfile')
    request_topic=config.get('common', 'request_topic')
    response_topic=config.get('common', 'response_topic')
    transport=config.get('common', 'transport')
    saltmaster=config.get('salt', 'saltmaster')

    config.read(packagebuilder_ini)
    my_mirrors=config.get('misc', 'my_mirrors')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())
    sys.exit(2)

pkgutils.get_logger('events_logger', events_logfile)
events_logger = logging.getLogger('events_logger')
my_mirrors = my_mirrors.split()

def listen_to_response(sec=5):
    '''
    This function will listen to reponse topic for 5 seconds by default and print out the response result
    '''
    # Create socket to talk to server
    con = zmq.Context()
    socket = con.socket(zmq.SUB)
    socket.connect ("tcp://%s:%s" % (zmq_host, pub_port))
    socket.setsockopt(zmq.SUBSCRIBE, response_topic)
    hosts_responded = []
    count = 0
    timer = sec * 10
    while count < timer :
        count += 1
        try:
            string = socket.recv(flags=1)
        except:
            pass
        else:
            if string:
                timenow = datetime.now()
                topic, message = string.split("=>")
                message = json.loads(message)
                hosts_responded.append(message['from'])
                if message['status'] == 'OK':
                    print "\033[94m[OK]\033[0m %s" % (message['from'])
                if message['status'] == 'SUCCESS':
                    print "\033[92m%s\033[0m: %s" % (message['from'], message['file'])

        time.sleep(0.10)

    for m in my_mirrors:
        if m not in hosts_responded:
            print "\033[91m[no response]\033[0m %s" % (m)

def use_salt(action, message):
    '''
    Function use salt client to send out the message
    action  - "rsync" or "delete" or "check"
    message - "Any data in String format"
    '''
    # WorkAround
    # Salt client lib overwrite the default system logging and have to move the import it here for system logging to work
    import salt.client
    import salt.config

    saltopts = salt.config.minion_config('/etc/salt/minion')
    saltopts['master'] = saltmaster
    caller = salt.client.Caller(mopts=saltopts)
    salt_tagname="package_mirrors/" + action

    caller.sminion.functions['event.send'](
        salt_tagname,
        {
            "rpms": message
        }
    )

def use_zmq(topic=request_topic, message=None):
    '''
    Function use ZeroMQ to send message
    topic   = "Request" or "Response"
    message = "Any data in String format or json"
    '''
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://%s:%s" % (zmq_host, sub_port))
        # ZMQ need to send 2 message in order to get data through
        # First request establish the connection and second one go through
        socket.send("dummy_message")
        time.sleep(0.5)
        socket.send("%s=>%s" % (topic, json.dumps(message)))
        # Getting the response
        # listen_to_response()
    except:
        print "ERROR", ZMQError
        logger.info('[ERROR] FAIL to send message to %s:%s' %(zmq_host, sub_port))
    

def main(action, file=''):
    ''' 
    main function which will call use_zmq or salt based on transport
    '''
    messagedata={}
    messagedata['action'] = action
    messagedata['file'] = file
    if transport == "zeromq":
        use_zmq(request_topic, messagedata)
        events_logger.info('Send event via ZeroMQ - [Request] - "%s => %s"' % (action, messagedata))
        # for now display the response for check and ping request only
        if (action == 'check') or (action == 'ping'):
            listen_to_response()
    else:
        # Salt event reactor only support remote command execution 
        # the Check require the return of result to the caller and we still need to use zeromq for this function for now
        if (action == 'check') or action == 'ping':
            use_zmq("Request", messagedata)
            events_logger.info('Send event via ZeroMQ - [Request] - "%s => %s"' % (action, messagedata))
        else:
            use_salt(action, data)
            events_logger.info('Send event via Salt - "%s => %s "' % (action, messagedata))

if __name__ == '__main__':
    parser = OptionParser(usage='%prog [-r|-d|-c|-u] [ -f filename|csvfile ]\n\nFor Example:\n%prog --rsync --files /data0/yum/6/base/x86_64/RPMS/myfile.rpm', version='%prog 0.0.1')
    parser.add_option("-r", "--rsync",
                      action="store_true",  dest="rsync",
                      help="to rsync the files provided from the --files")
    parser.add_option("-d", "--delete",
                      action="store_true",  dest="delete",
                      help="to delete the files provided from the --files")
    parser.add_option("-c", "--check",
                      action="store_true",  dest="check",
                      help="to check the files provided from the --files")
    parser.add_option("-u", "--updaterepo",
                      action="store_true",  dest="update_repo",
                      help="to update repodata to the directory path provided from the --files   ")
    parser.add_option("-p", "--ping",
                      action="store_true",  dest="ping",
                      help="to check/ping the active mirrors hosts listening for pkgevents")
    parser.add_option("-k", "--killsubscribers",
                      action="store_true",  dest="kill_subs",
                      help="will cause the subscribers to exit, to use if we push an update and want the subs to restart(if in supervisord)")
    parser.add_option("-f", "--file",
                      action="store", type="string", dest="files",
                      help="accepts a file or csv separated list of the files to check/rsync/delete/updaterepo (should be the full path)")

(options, args) = parser.parse_args()

if options.rsync:
    main("rsync", options.files)
    sys.exit(0)
if options.delete:
    main("delete", options.files)
    sys.exit(0)
if options.check:
    main("check", options.files)
    sys.exit(0)
if options.update_repo:
    main("update_repo", options.files)
    sys.exit(0)
if options.ping:
    main("ping","dummydata")
    sys.exit(0)
if options.kill_subs:
    main("kill_subs")
    sys.exit(0)
