#!/usr/local/bin/blue-python3.4

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, Date, Float
import configparser 
import sys

conf_file='/etc/firmware.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    dbhost=config.get('firmware_rest', 'dbhost')
    dbuser=config.get('firmware_rest', 'dbuser')
    dbpass=config.get('firmware_rest', 'dbpass')
    dbname=config.get('firmware_rest', 'dbname')
    db_uri="mysql://%s:%s@%s/%s" % (dbuser, dbpass, dbhost, dbname)
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())

# DB class 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  db_uri
app.config['SQLALCHEMY_POOL_RECYCLE'] = 30
db = SQLAlchemy(app)
 
# DB classess 
class HP(db.Model):
    __tablename__ = 'hp'
    id = db.Column('id', Integer, primary_key=True)
    serial_no = db.Column('serial_no', String(20), unique=True)
    server_name = db.Column('server_name', String(120), unique=True)
    ilo_version = db.Column('ilo_version', String(60))
    product_name = db.Column('product_name', String(60))
    system_rom_version = db.Column('system_rom_version', String(60))
    last_updated = db.Column('mysql_row_updated_at', Date)
    position = db.Column('position', String(10))
    chassis = db.Column('chassis', String(60))
 
    def __init__(self, serial_no, server_name, ilo_version, product_name, system_rom_version, position, chassis):
        self.serial_no = serial_no
        self.server_name = server_name
        self.ilo_version = ilo_version
        self.product_name = product_name 
        self.system_rom_version = system_rom_version
        self.position = position
        self.chassis = chassis

    def __repr__(self):
        return '<HP %s - %s - (%s) - (%s) - (%s) - (%s@%s)>' % (self.server_name, self.serial_no, self.product_name, self.ilo_version, self.system_rom_version, self.chassis, self.position)
    
    def __str__(self):
        return '<HP %s - %s - (%s) - (%s) - (%s) - (%s@%s)>' % (self.server_name, self.serial_no, self.product_name, self.ilo_version, self.system_rom_version, self.chassis, self.position)

