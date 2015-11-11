#!/usr/bin/env blue-python2.7
import sys
import os
import zmq
import time
import subprocess
from datetime import datetime
import pkgutils
import ConfigParser as configparser 
import json
import ast
import logging

# Reading config
conf_file='/etc/pkgevent.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    zmq_host=config.get('common', 'zmq_host')
    yum_master=config.get('common', 'yum_master')
    pub_port=config.get('common', 'pub_port')
    sub_port=config.get('common', 'sub_port')
    events_logfile=config.get('common', 'events_logfile')
    action_logfile=config.get('common', 'action_logfile')
    request_topic=config.get('common', 'request_topic')
    response_topic=config.get('common', 'response_topic')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())
    sys.exit(2)

send_from=os.uname()[1]
pkgutils.get_logger('events_logger', events_logfile)
pkgutils.get_logger('action_logger', action_logfile)
events_logger = logging.getLogger('events_logger')
action_logger = logging.getLogger('action_logger')

#events_logger=pkgutils.get_logger(events_logfile)
#action_logger=pkgutils.get_logger(action_logfile)

# Create socket to subcribe to "Request" queue from the zeroMQ server
context = zmq.Context()
socket = context.socket(zmq.SUB)
events_logger.info("Listening for events from %s" % zmq_host)
socket.connect ("tcp://%s:%s" % (zmq_host, pub_port))
socket.setsockopt(zmq.SUBSCRIBE, request_topic)


def seppuku():
    #to exist so supervisord can restart me
    events_logger.info("I was asked to kill myself, I will die with honor.")
    sys.exit(2)

def check_file(files):
    # Support for both individual file input or csv format
    nay = '\033[91m[N]\033[0m'
    my_files = file.split(',')
    resp = []
    status = 'SUCCESS'

    for each_f in my_files:
        if not each_f:
            continue
        if os.path.exists(each_f):
            cmd = ["/usr/bin/sha1sum", "-b", each_f ]
            sum = pkgutils.run_cmd(cmd, action_logger, cmd_out=True)
            events_logger.info(sum)
            #get the sha1sum, pick the first 8 chars
            sum = sum.split()[0].strip()[:8]
            resp.append("\033[94m[%s]\033[0m%s" % (sum, os.path.basename(each_f)))
        else:
            resp.append(nay + os.path.basename(each_f))

    if len(resp) > 0:
        log_and_format_response_msg("check", ','.join(resp), status)


def rsync_file(files):
    '''
    Support for both individual file input or csv format
    These files are to be rsynced over from the yum-master
    '''
    rsync      = '/usr/bin/rsync'
    rsync_user = 'nobody'
    rsync_args = [ '-qaplH',
                   '--password-file=/root/rsync_yum_password',
                   '--delete-delay',
                   '--delay-updates'
                 ]
    to_update_list=[]

    if len(files) > 0:
        rpms = files.split(',')
        for rpm in rpms:
            remote_file = rpm[1:]  #remove the '/' at the start, data0 is the rsync exposed module
            rsync_url   = "%s@%s::%s" % (rsync_user, yum_master, remote_file.strip())
            local_file  = rpm

            #flatten out the command to run, sum() expects all args to be lists,
            cmd = sum([ [rsync], rsync_args, [rsync_url], [local_file] ], [])

            if pkgutils.run_cmd(cmd, action_logger) == True :
                status="SUCCESS"
                #rsync completed successfully, we add this to our updaterepo list
                if os.path.dirname(local_file) not in to_update_list:
                    if os.path.basename(os.path.dirname(local_file)) == 'RPMS':
                        to_update_list.append(os.path.dirname(local_file))
            else:
                status="FAIL"

    #append to our to_update_list we run createrepo on this list
    if len(to_update_list) > 0:
        pkgutils.updaterepos(to_update_list, action_logger)
    
    # Log and send the response 
    log_and_format_response_msg("rsync", files, status)

def update_repo(file_paths):
    '''This function accept a directory path or csv format and run createrepo_c on it'''
    if len(file_paths) > 0:
        for f_path in set(file_paths.split(',')):
            try:
                # All repodata we have is under 'RPMS' directory
                # let's do a check on this first
                basepath = os.path.dirname(f_path)
                if os.path.exists(basepath) and os.path.basename(basepath) == 'RPMS':
                    pkgutils.updaterepos([basepath], action_logger)
                else:
                    raise PkgeventError('[ERROR] %s does not exist or not conform to rpm repo directory format') 
            except:
                status="FAIL"
                action_logger.info("[FAIL] update_repo %s" % f_path)
            else:
                status="SUCCESS"
                action_logger.info("[SUCCESS] update_repo %s" % f_path)

    # Log and send the response
    log_and_format_response_msg("update_repo", file_paths, status)


def delete_file(files):
    to_update_list = []
    if len(files) > 0:
        rpms = files.split(',')
        for rpm in rpms:
            try:
                os.remove(rpm)
            except:
                status="FAIL"
                action_logger.info("[FAIL] delete %s" % rpm)
            else:
                status="SUCCESS"
                action_logger.info("[SUCCESS] delete %s" % rpm)
                # Only updaterepo if the dir path is with "RPMS"
                if os.path.dirname(rpm) not in to_update_list:
                    if os.path.basename(os.path.dirname(rpm)) == 'RPMS':
                        to_update_list.append(os.path.dirname(rpm))

    if len(to_update_list) > 0:
        pkgutils.updaterepos(to_update_list, action_logger)

    # Log and send the response
    log_and_format_response_msg("delete", files, status)


def ping():
    ''' A ping function act like a health check and just return OK '''
    log_msg={}
    log_msg['status'] = "OK"
    send_response(log_msg)


def log_and_format_response_msg(action, files, status):
    ''' This function simply format the log message, log it and call send_reponse '''
    log_msg={}
    log_msg['action'] = action
    log_msg['file'] = files
    log_msg['status'] = status
    send_response(log_msg)


def send_response(message):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://%s:%s" % (zmq_host, sub_port))

    message['from'] = send_from
    events_logger.info("Sending [%s] - %s" % (response_topic, message))
    # ZMQ need to send 2 message in order to get data through
    # First dummy request establish the connection and second one go through
    socket.send("dummy_message")
    time.sleep(0.5)
    socket.send("%s=>%s" % (response_topic, json.dumps(message)))


if __name__ == '__main__': 
    while True:
        string = socket.recv()
        if string:

            timenow = datetime.now()
            topic, msg = string.split('=>')
            message = ast.literal_eval(msg)
            action = message['action']
            file = message['file']
            events_logger.info('Receiving [%s] - "%s"' % (topic, message))

            if action == 'check':
                check_file(file)
            if action == 'update_repo':
                update_repo(file)
            elif action == 'rsync':
                rsync_file(file)
            elif action == 'delete':
                delete_file(file)
            elif action == 'ping':
                ping()
            elif action == 'kill_subs':
                seppuku()

        time.sleep(1)
