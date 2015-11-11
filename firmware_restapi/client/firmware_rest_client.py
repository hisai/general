#!/usr/bin/env blue-python3.4
'''
This script read the HPSUM_InstallDetails.xml for firwmware update info and dmidecode for other system info
Then update the firmware info by calling the firmware REST API.
'''
from lxml import etree
import sys
import os
import subprocess
import requests
import json
import re

# This is the default location where HPSUM installattion xml log located
_rest_url = 'http://myserver.example.com/firmware'
_hpsum_xmlfile = '/var/hp/log/localhost/HPSUM_InstallDetails.xml'
_headers = { 'Content-Type': 'application/json' }
_proxies = { "http": "", "https": "" }

def _rest_get(url):
    ''' 
    Function that make HTTP GET REST call and return dict
    '''
    try:
        response = requests.get(url, headers=_headers, proxies=_proxies)
    except:
        e = sys.exc_info()
        print("Can't connect to api endpoint: %s : %s" % (url, e))
    else:
        return response.json()

def _rest_post(url, payload):
    ''' 
    Function that make HTTP POST REST call and return dict
    '''
    try:
        response = requests.post(url, data=json.dumps(payload), headers=_headers, proxies=_proxies)
    except:
        e = sys.exc_info()
        print("Can't connect to api endpoint: %s : %s" % (url, e))
    else:
        return response.json()

def _rest_put(url, payload):
    ''' 
    Function that make HTTP PUT REST call and return dict
    '''
    try:
        response = requests.put(url, data=json.dumps(payload), headers=_headers, proxies=_proxies)
    except:
        e = sys.exc_info()
        print("Can't connect to api endpoint: %s : %s" % (url, e))
    else:
        return response.json()

def _parse_xml(_hpsum_xmlfile):
    ''' 
    Function that parse xml file and return data in list format
    '''
    try:
        tree = etree.parse(_hpsum_xmlfile)
        root = tree.getroot()
        items = root.findall('ComponentResults')[0].getchildren()
        items_list =[]

        for item in items:
            item_dict ={}
            for child in item.getchildren():
                item_dict[child.tag] = child.text
            #print(item_dict)
            items_list.append(item_dict)
        return items_list
    except:
        e = sys.exc_info()
        print("Can't read the content of xml file: %s " % (_hpsum_xmlfile))
        print(e)
        sys.exit(1)

def _get_hardware_info():
    '''
    Function collect system info (i.e serial_no etc) from dmidecode and return a dictionary data
    '''
    p = subprocess.Popen('dmidecode', stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    out = p.communicate()[0].decode('utf-8')
    _hw_info={}
    for line in out.split('\n'):
        if 'Product Name:' in line.strip():
            _hw_info['product_name'] = line.replace('Product Name: ','').strip()
        if 'Enclosure Name:' in line.strip():
            _hw_info['chassis'] = line.replace('Enclosure Name: ','').strip()
        if 'Server Bay:' in line.strip():
            _hw_info['position'] = line.replace('Server Bay: ','').strip()
            break

    for line in out.split('\n'):
        if re.search(r'[\A-Z0-9]{10}', line.strip()):
            _hw_info['serial_no'] = re.search(r'[\A-Z0-9]{10}', line).group()
            break
    _hw_info['server_name'] = os.uname()[1]
    return _hw_info


def _read_xml(_xml_file):
    ''' 
    Right now we only care about ilo and system rom info
    May expand to grab more data in the future
    Sample data to constrct
    {
    "ilo_version": "2.20 May 20 2015",
    "serial_no": "CZ3530WS1E",
    "system_rom_version": "I36 05/06/2015"
    }
    ''' 
    _xml_data = _parse_xml(_xml_file)
    _payload = _get_hardware_info()
    
    for item in _xml_data:
        '''
        Sample data for ilo
        {'ComponentName': 'hp-firmware-ilo4-2.30-1.1.i386.rpm', 
        'ResultCode': '0', 'InstalledVersion': '2.30', 
        'PreviousVersion': '2.20', 
        'ComponentReturnCode': 'Success', 
        'ComponentDescription': 'Firmware CD Supplemental Update / Online ROM Flash Component for Linux - 
        HP Integrated Lights-Out 4(hp-firmware-ilo4-2.30-1.1.i386)', 
        'IsComponentSuccess': 'true'}
        '''
        if 'ilo' in item['ComponentName']:
            _payload['ilo_version'] = item['InstalledVersion']

        if 'hp-firmware-system' in item['ComponentName']:
            # to extract "I31 01/06/2015"  from hp-firmware-system-i31-2015.06.01-1.1.i386.rpm
            # let's hope that HP doesn't change this format again
            rpm_name = item['ComponentName']
            temp_list = rpm_name.split('-')
            # ['hp', 'firmware', 'system', 'i31', '2015.06.01', '1.1.i386.rpm']
            version = temp_list[3].upper()
            year, month, day = temp_list[4].split('.')
            _payload['system_rom_version'] = version + " " + day + "/" + month + "/" + year  
            
    return(_payload)        

def main():
    blade_info = _read_xml(_hpsum_xmlfile)
    serial_no = blade_info['serial_no']
    # If there is ilo or system_rom firmware updated by HPSUM, we will call rest api to update its updated info
    if blade_info.get('ilo_version') or blade_info.get('system_rom_version'):
        # Check if the blade exist already or not in hte inventory db
        end_point = _rest_url + 'hp_server/serial_no/' + serial_no
        rep = _rest_get(end_point)
        if (rep['status_code'] == '200') and (rep['data']['serial_no'] == serial_no):
            # If server info already exists, do an update
            print("%s exists in firmware inventory system. Updating the firmware info now." % (blade_info['server_name']))
            end_point = _rest_url + 'hp_server/update'
            print(_rest_put(end_point, blade_info))
        else:
            # Create new entry if it doesn't yet exist in the inventory db
            print("%s doesn't exist in firmware inventory system. Adding the firmware info now." % (blade_info['server_name']))
            end_point = _rest_url + 'hp_server/new'
            print(_rest_post(end_point, blade_info))
    else:
        print("No ILO or System ROM firmware have been updated. It seems that this system already have latest firmware")

if __name__ == '__main__':
    main()
