#!/usr/bin/env blue-python2.7
import sys
import MySQLdb as mdb
import re
import logging
import ConfigParser as configparser

# Reading config
conf_file='config.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    host=config.get('mysql', 'host')
    user=config.get('mysql', 'user')
    password=config.get('mysql', 'password')
    db=config.get('mysql', 'db')
    log_file=config.get('ilo', 'log_file')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())
    sys.exit(2)

# logging setting
logformat       = '%(asctime)s : %(message)s'
logging.basicConfig(format=logformat, filename=log_file, level=logging.WARN)


def mysql_connect(host, user, password, db):
    ''' This function connect to mysql and return cursor to caller '''
    try:
        con = mdb.connect(host, user, password, db)
    except mdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)
    else:
        return con, con.cursor()


def insert_chassis(row):
    ''' 
    This function will insert data into mysql
    sample data in dict format
    {'hostname': 'accessch-216.lhr4.lom.example.com', 'product_name': 'BladeSystem c7000 DDR2 Onboard Administrator with KVM', 'fw_version': '3.55 Mar 20 2012'}
    '''

    con, cursor = mysql_connect(host, user, password, db)
    #prepare sql statement
    try:
        cols=''
        values=''
        i=0
        keys = row.keys()
        #print "keys:", keys
        while i < len(keys) - 1:
            cols += keys[i] + ", "
            values += "'" + row[keys[i]] + "', "
            i += 1
        cols += keys[-1]
        values += "'" + row[keys[-1]] + "'"
        #print "cols:", cols
        #print "values:", values
        sql = "INSERT INTO chassis (%s) values (%s)" % (cols, values)
    except:
        print "Data input is not in the correct format"
        sys.exit(1)

    # excecute sql sqls 
    try:
        #print sql
        cursor.execute(sql)
        con.commit()
    except mdb.Error, e:
        if con:
            con.rollback()
        print "Running sql %s" % sql
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)
    finally:
        if con:
            con.close()



def insert_blades(table_name, rows):
    ''' 
    This function will insert data into mysql
    sample data in dict format
    [{'server_name': u'mc201csmail-01.lhr4.prod.example.com', 'power_mgmt_ctrl_version': u'3.2', 'serial_no': u'CZ34050759', 'ilo_version': u'2.03 Nov 07 2014', 'product_name': u'ProLiant BL460c Gen8', 'system_rom_version': u'I31 08/02/2014'}]
    '''

    con, cursor = mysql_connect(host, user, password, db)

    #prepare sql statement
    sqls=[]
    for row in rows:
        try:
            cols=''
            values=''
            i=0
            keys = row.keys()
            #print "keys:", keys
            while i < len(keys) - 1:
                cols += keys[i] + ", "
                values += "'" + row[keys[i]] + "', "
                i += 1
            cols += keys[-1]
            values += "'" + row[keys[-1]] + "'"
            #print "cols:", cols
            #print "values:", values
            sql = "INSERT INTO %s (%s) values (%s)" % (table_name, cols, values)
            sqls.append(sql)
        except:
            print "Data input is not in the correct format"
            sys.exit(1)
    # excecute sql sqls 
    for sql in sqls:
        try:
            #print sql
            cursor.execute(sql)
            con.commit()
        except mdb.Error, e:
            if con:
                con.rollback()
            #print "Running sql %s" % sql
            #print "Error %d: %s" % (e.args[0],e.args[1])
            logging.warn("[ERROR] [** %d: %s **] : [%s] " % (e.args[0],e.args[1],sql))
            #sys.exit(1)
    if con:
        con.close()


if __name__ == '__main__':
    print("This is a helper function script and shouldn't be callled on its own")
