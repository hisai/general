#!/usr/bin/env blue-python2.7
'''
This script is used to connect to HP chassis and collect the firmware info of the blades and chassis.
Then import the collected data into the MySQL database
'''
import sys
import os
import re
import paramiko
from optparse import OptionParser
import ConfigParser as configparser
import logging
import dns.resolver
import mysql
from datetime import datetime
import traceback

# Reading config
conf_file='config.ini'
try:
    config = configparser.ConfigParser()
    config.read(conf_file)
    adminuser=config.get('ilo', 'adminuser')
    adminpass=config.get('ilo', 'adminpass')
    log_file=config.get('ilo', 'log_file')
except Exception as err:
    e = sys.exc_info()[0]
    print ('Error while reading configfile - %s ' % conf_file)
    print (sys.exc_info())
    sys.exit(2)

# logging setting
logformat='%(asctime)s : %(message)s'
logging.basicConfig(format=logformat, filename=log_file, level=logging.WARN)

def resolve_dns(fqdn):
    ''' This return record the A record as a list '''
    ans = dns.resolver.query(fqdn, "A")
    return [x.__str__() for x in ans]

def check_active_oa(data):
    '''
    This function check whether this is active OA (onboard administrator) or not 
    '''
    for each_line in data:
        if re.search(r'Role.*Active',each_line):
            return True

def search_and_substitube(search_str, replacement_str, line):
    regex="(%s).*: " % search_str
    p = re.compile(regex)
    return p.sub(replacement_str, line)

def filter_chassis_info(lines, chassis_host):
    """ This function collect chassis info """
    chassis={}
    for each_line in lines:
        # strip out new line and convert utf8 to ascii
        each_line = each_line.strip().encode('ascii', 'ignore')
        # Create an empty dict when reaching the each_line start with "Server Blade #"
        if "Product Name" in each_line:
            chassis['product_name']= search_and_substitube("Product Name", "", each_line)
        if "Serial Number:" in each_line:
            chassis['serial_no']= search_and_substitube("Serial Number:", "", each_line)
        if "Firmware Ver" in each_line:
            chassis['fw_version'] = search_and_substitube("Firmware Ver", "", each_line)
            chassis['hostname'] = chassis_host
    return chassis
        
def filter_blade_info(lines, chassis_host):
    """ This function collect all blades info in a chassis"""
    start="Server Blade #"
    end="Power Management Controller Version"
    blades=[]
    for each_line in lines:
        #print "each_line ==> " +  each_line
        # strip out new line and convert utf8 to ascii
        each_line = each_line.strip().encode('ascii', 'ignore')
        # Create an empty dict when reaching the each_line start with "Server Blade #"
        if start in each_line:
            blade={}
            #Lookup for 1 or more numbers  [0-9] in the line "Server Blade #1"
            blade['position'] = re.search(r'[\d]+',each_line).group()
        if "Product Name" in each_line:
            blade['product_name']= each_line.replace('Product Name: ','')
        if "Serial Number:" in each_line:
            blade['serial_no']= each_line.replace('Serial Number: ','')
        if "Server Name" in each_line:
            blade['server_name']= each_line.replace('Server Name: ','')
        if "ROM Version" in each_line:
            blade['system_rom_version']= each_line.replace('ROM Version: ','')
        if "Firmware Version" in each_line:
            blade['ilo_version']= each_line.replace('Firmware Version: ','')
        # Add the blade{} into the blades list when reaching the end of a blade
        if end in each_line :
            # Add chassis info for each blade
            blade['chassis'] = chassis_host
            blade['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            blades.append(blade)
            blade={}
    return blades

def connect(host, command="") :
    ''' This function connect to host via ssh and return output'''
    try:
        ssh = paramiko.SSHClient()
        #paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
        #paramiko.util.log_to_file("/home/stit/ssh_paramiko.log")
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=adminuser, password=adminpass, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = ssh.exec_command(command)
        return stdout.readlines()
    except:
        e = sys.exc_info()
        print(traceback.print_tb(e[2]))
        #logging.warn("[ERROR] - %s" % e)

def collect_hosts_fw(_file):
    '''
    Function collect firmwares for all hosts in the input file
    '''
    with open(_file) as fh:
        for host in fh.readlines():
            print(host.strip())
            collect_host_fw(host.strip())


def collect_host_fw(host):
    '''
    Function to collect firmware from a single chassis for both chassis and blades in that enclosure
    '''

    oa_cmd ='show oa status'
    ssh_cmd = 'show server info all'

    ips = resolve_dns(host)
    for ip in ips:
        # Connect to active oa
        if check_active_oa(connect(ip, oa_cmd)):
            logging.warn("Collecting info from chassis - %s" % host)
            logging.warn("%s is active Onboard Administrator" % ip)

            # Collect blades info
            blades = filter_blade_info(connect(ip, ssh_cmd), host)
            incomplete_blades=[]
            for blade in blades:
                # There are some foobar blades that doesn't have serial no which is really weird
                # And we will filter them out and keep them in incomplete_blades list which will
                # import into hp_incomplete table later on.
                if "Serial Number:" in blade.values():
                    logging.warn("[WARNING] [** NO SERIAL_NO **] %s" % blade)
                    blades.remove(blade)
                    incomplete_blades.append(blade)

            # Collect chassis info
            chassis = filter_chassis_info(connect(ip, 'show oa info'), host)
            
            logging.warn("Chassis info: %s" % chassis)
            logging.warn("Blades info: %s" % blades)
            print("BLADES INFO: %s " % blades)
            print("CHASSIS INFO: %s " % chassis)

            # Import data into database
            mysql.insert_chassis(chassis)
            mysql.insert_blades("hp", blades)
            if len(incomplete_blades) > 0:
                mysql.insert_blades("hp_incomplete", incomplete_blades)
            

if __name__ == '__main__':
    parser = OptionParser(usage='%prog [ --host | --file ]', version='%prog 0.0.1')
    parser.add_option("--host",
                      action="store", type="string", dest="host",
                      help="--host chassis host that you want to connect to")
    parser.add_option("--file",
                      action="store", type="string", dest="file",
                      help="--file input file that contain all the chassis hosts that you wish to collect firmwares")

(options, args) = parser.parse_args()
if options.host:
    collect_host_fw(options.host)
if options.file:
    collect_hosts_fw(options.file)
