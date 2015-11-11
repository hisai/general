#!/usr/local/bin/blue-python3.4

from datetime import datetime
import sys
import logging
import logging.handlers
import configparser
from flask import Flask, jsonify, request
## app and db is defined on model.py 
from model import db, app, HP

# Reading config
conf_file='/etc/firmware.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    log_file = config.get('firmware_rest', 'log_file')
    logger_name = config.get('firmware_rest', 'logger_name')
    log_level = config.get('firmware_rest', 'log_level')
    log_rotation_count = config.get('firmware_rest', 'log_rotation_count')
    log_filesize = config.get('firmware_rest', 'log_filesize')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())

## Set logging settings
logger      = logging.getLogger(logger_name)
formatter   = logging.Formatter('[%(asctime)s] [%(filename)s->%(funcName)s()]: %(message)s')
fileHandler = logging.handlers.RotatingFileHandler(log_file, maxBytes=int(log_filesize), backupCount=log_rotation_count)
fileHandler.setFormatter(formatter)
logger.setLevel(log_level)
logger.addHandler(fileHandler)


# Misc functions
def format_return_data(object):
    object_dict = object.__dict__
    if '_sa_instance_state' in object_dict.keys():
        object_dict.pop('_sa_instance_state')
    return object_dict

def dict_to_str(dummy_dict):
    '''
    Take dict input {'username': 'Dave', 'activation_key': 'live'}
    And return string "username='Dave', activation_key='live'"
    '''
    _list=[]
    for k in dummy_dict.keys():
        _list.append("%s='%s'" % (k, dummy_dict[k]))
    return ", ".join(_list)

@app.errorhandler(400)
def custom400(error):
    return jsonify({'message': error.description})

@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

@app.after_request
def shutdown_session(response):
    db.session.remove()
    return response

@app.route('/firmware/')
def index():
    with open('/opt/firmware/firmware_restapi/api.txt') as fh:
        data= fh.read()
    return data

@app.route('/firmware/hp_server/list_all')
def list_hp_servers():
    response = {}
    try:
        ret = []
        _hp_servers = HP.query.all()
        for _server in _hp_servers:
            ret.append(format_return_data(_server))
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for serial_no %s <%s>" % (_serial_no, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for serial_no %s" % _serial_no
    else:
        logger.info("Success: retrieve servers info for serial_no %s" % _serial_no)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = ret
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/server_name/<_server_name>', methods=['GET'])
def get_hp_server(_server_name):
    response = {}
    try:
        _server = HP.query.filter_by(server_name=_server_name).one()
        ret = format_return_data(_server)
        logger.info("[Request] - %s" % request)
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for server_name %s <%s>" % (_server_name, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for server_name %s" % _server_name
    else:
        logger.info("Success: retrieve servers info for server_name %s" % _server_name)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = ret
        logger.info("[Response] - %s" % response)
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/serial_no/<_serial_no>', methods=['GET'])
def get_hp_server_by_serialno(_serial_no):
    response = {}
    try:
        _server = HP.query.filter_by(serial_no=_serial_no).one()
        ret = format_return_data(_server)
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for serial_no %s <%s>" % (_serial_no, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for serial_no %s" % _serial_no
    else:
        logger.info("Success: retrieve servers info for serial_no %s" % _serial_no)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = ret
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/chassis/<_chassis>', methods=['GET'])
def get_hp_server_by_chassis(_chassis):
    response = {}
    try:
        ret = []
        _hp_servers = HP.query.filter_by(chassis=_chassis).all()
        print("_hp_servers %s" % _hp_servers)
        for _server in _hp_servers:
            ret.append(format_return_data(_server))
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for chassis %s <%s>" % (_chassis, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for chassis %s" % _chassis
    else:
        logger.info("Success: retrieve servers info for chassis %s" % _chassis)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = ret
    return jsonify(response), response['status_code']


@app.route('/firmware/hp_server/ilo_version/<_ilo_version>', methods=['GET'])
def get_hp_server_by_ilo_version(_ilo_version):
    response = {}
    try:
        ret = []
        _hp_servers= HP.query.filter(HP.ilo_version.like(_ilo_version + "%")).all()
        if len(_hp_servers) > 0:
            for _server in _hp_servers:
                ret.append(format_return_data(_server))
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for ilo_version %s <%s>" % (_ilo_version, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for ilo_version %s" % _ilo_version
    else:
        response['status'] = "success"
        response['status_code'] = '200'
        if len(ret) == 0:
            logger.info("No data available for ilo_version %s" % _ilo_version)
            response['message'] = "No data available for ilo_version %s" % _ilo_version
        else:
            logger.info("Success: retrieve servers info for ilo_version %s" % _ilo_version)
            response['data'] = ret
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/system_rom_version/<_system_rom>', methods=['GET'])
def get_hp_server_by_system_rom(_system_rom):
    response = {}
    try:
        ret = []
        hp_servers= HP.query.filter(HP.system_rom_version.like(_system_rom + "%")).all()
        if len(hp_servers) > 0:
            for server in hp_servers:
                ret.append(format_return_data(server))
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for system_rom_version %s <%s>" % (_system_rom, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for system_rom_version %s" % _system_rom
    else:
        response['status'] = "success"
        response['status_code'] = '200'
        if len(ret) == 0:
            logger.info("No data available for system_rom_version %s" % _system_rom)
            response['message'] = "No data available for system_rom_version %s" % _system_rom
        else:
            logger.info("Success: retrieve servers info for system_rom_version %s" % _system_rom)
            response['data'] = ret
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/product_name/<_product_name>', methods=['GET'])
def get_hp_server_by_product_name(_product_name):
    response = {}
    try:
        ret = []
        _hp_servers= HP.query.filter(HP.product_name.like("%" + _product_name + "%")).all()
        for _server in _hp_servers:
            ret.append(format_return_data(_server))
    except:
        e = sys.exc_info()
        logger.info("ERROR: Fail to retrieve servers info for product_name %s <%s>" % (_product_name, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to retrieve servers info for product_name %s" % _product_name
    else:
        response['status'] = "success"
        response['status_code'] = '200'
        if len(ret) == 0:
            logger.info("No data available for product_name %s" % _product_name)
            response['message'] = "No data available for product_name %s" % _product_name
        else:
            logger.info("Success: retrieve servers info for product_name %s" % _product_name)
            response['data'] = ret
    return jsonify(response), response['status_code']


@app.route('/firmware/hp_server/new', methods=['POST'])
def new_hp_server():
    response={}
    try:
        _server = HP( 
                    serial_no=request.json['serial_no'], 
                    server_name=request.json.get('server_name',''), 
                    ilo_version=request.json.get('ilo_version',''),
                    product_name=request.json.get('product_name',''),
                    system_rom_version=request.json.get('system_rom_version',''), 
                    position=request.json.get('position',''), 
                    chassis=request.json.get('chassis',''))
        db.session.add(_server)
        db.session.commit()
    except:
        e = sys.exc_info()
        logger.info("ERROR: Unable to create new record for server_name %s <%s>" % (request.json['server_name'], e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or fail to create new record for server_name %s" % request.json['server_name']
    else:
        logger.info("Success: Adding %s" % request.json )
        response['status'] = "success"
        response['status_code'] = '201'
        response['data'] = request.json
    return jsonify(response), response['status_code']


@app.route('/firmware/hp_server/update', methods=['PUT'])
def update_hp_server():
    response={}
    try:
        _server = HP.query.filter_by(serial_no=request.json['serial_no']).one()
        # Remove serial_no as sqlalchemy won't allow this column to be updated as it is a unique column
        for key in request.json.keys():
            setattr(_server, key, request.json[key])
        _server.last_updated = datetime.now()
        db.session.commit()
    except:
        e = sys.exc_info()
        logger.info("ERROR: update %s <%s>" %( request.json, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or no record found for %s" % request.json
    else:
        logger.info("Success: Updating %s" % request.json )
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = request.json
    return jsonify(response), response['status_code']


@app.route('/firmware/hp_server/delete/server_name/<_server_name>', methods=['GET'])
def delete_hp_server_by_server_name(_server_name):
    response={}
    try:
        _server = HP.query.filter_by(server_name=_server_name).one()
        db.session.delete(_server)
        db.session.commit()
    except:
        e = sys.exc_info()
        logger.info("ERROR: Delete %s <%s>" %(_server_name, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or no record found for %s" % _server_name
        #return bad_request("Bad Request or no record found for %s" % _server_name )
    else:
        logger.info("Success: Delete %s" % _server_name)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = "null"
    return jsonify(response), response['status_code']

@app.route('/firmware/hp_server/delete/serial_no/<_serial_no>', methods=['GET'])
def delete_hp_server_by_serial_no(_serial_no):
    response={}
    try:
        print("Hello")
        _server = HP.query.filter_by(serial_no=_serial_no).one()
        print(_server)
        db.session.delete(_server)
        db.session.commit()
    except:
        e = sys.exc_info()
        logger.info("ERROR: Delete %s <%s>" %(_serial_no, e[:2]))
        response['status'] = "fail"
        response['status_code'] = '400'
        response['message'] = "Bad Request or no record found for %s" % _serial_no
    else:
        logger.info("Success: Delete %s" % _serial_no)
        response['status'] = "success"
        response['status_code'] = '200'
        response['data'] = "null"
    return jsonify(response), response['status_code']

  
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001, debug=True)
    logger.info("Starting up Firmwares API Application")

