#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Write by yskang(kys061@gmail.com)

from saisei.saisei_api import saisei_api
import subprocess
import time
from logging.handlers import RotatingFileHandler
import logging
import sys
import re
import csv, json
import os
from pprint import pprint
from time import sleep

stm_ver=r'7.3'
id=r'cli_admin'
passwd=r'cli_admin'
host=r'localhost'
port=r'5000'
rest_basic_path=r'configurations/running/'
rest_interface_path=r'interfaces/'
rest_token=r'1'
rest_order=r'>interface_id'
rest_start=r'0'
rest_limit=r'10'
LOG_FILENAME=r'/var/log/stm_bypass.log'

stm_status=False
link_type=r'copper'
interface_size=0
segment_size=0
segment_state=[]
bump_status=False
board = 'COSD304'
logger = None

err_lists = ['Cannot connect to server', 'does not exist', 'no matching objects', 'waiting for server']


def make_logger():
    global logger
    try:
        logger = logging.getLogger('saisei.bypass_portwell_monitor')
        fh = RotatingFileHandler(LOG_FILENAME, 'a', 50 * 1024 * 1024, 4)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print('cannot make logger, please check system, {}'.format(e))
    else:
        logger.info("***** logger starting %s *****" % (sys.argv[0]))

def subprocess_open(command, timeout):
    try:
        p_open = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except Exception as e:
        logger.error("subprocess_open() cannot be executed, {}".format(e))
        pass
    else:
        for t in xrange(timeout):
            sleep(1)
            if p_open.poll() is not None:
                (stdout_data, stderr_data) = p_open.communicate()
                return stdout_data, stderr_data
            if t == timeout-1:
                p_open.kill()
                return False, 'error'

def logging_line():
    logger.info("=================================")


def get_rest_url(_select_attrs, _with_attr=[], _with_arg=[]):
    # print(_with_arg)
    if len(_with_attr) < 1:
        return "{}{}{}".format(rest_basic_path, rest_interface_path, _select_attrs)

    if len(_with_attr) > 1:
        return "{}{}?token={}&order={}&start={}&limit={}&select={}&with={}={},{}={}".format(
            rest_basic_path, rest_interface_path, rest_token, rest_order, rest_start, rest_limit, _select_attrs, _with_attr[0], _with_arg[0], _with_attr[1], _with_arg[1])
    else:
        return "{}{}?token={}&order={}&start={}&limit={}&select={}&with={}={}".format(
            rest_basic_path, rest_interface_path, rest_token, rest_order, rest_start, rest_limit, _select_attrs, _with_attr[0], _with_arg[0])


def check_segment_state(select_attrs):
    '''
        세그먼트 상태, 인터페이스 상태 up의 조건
        1. adminstatus
        2. enabled
        3. link_type
        4. model_type
        5. interface thread status
    '''
    global segment_state, stm_status, bump_status
    res = api.rest.get(get_rest_url(select_attrs, ["type","actual_direction"], ["ethernet","external"]))
    enabled_size = 0
    # pprint(res["collection"])
    for i, interface in enumerate(res["collection"]):
        if (i==0 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            peer_status = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]['admin_status']
            if peer_status == "up":
                enabled_size += 1
                name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": True,
                    "bump": name,
                })
            else:
                name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })
        elif (i==1 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            peer_status = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]['admin_status']
            if peer_status == "up":
                enabled_size += 1
                name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": True,
                    "bump": name,
                })
            else:
                name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })
        elif (i==2 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            peer_status = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]['admin_status']
            if peer_status == "up":
                enabled_size += 1
                name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": True,
                    "bump": name,
                })
            else:
                name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })
        elif (i==3 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            peer_status = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]['admin_status']
            if peer_status == "up":
                enabled_size += 1
                name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": True,
                    "bump": name,
                })
            else:
                name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })                                
        else:
            enabled_size += 0
            peer_status = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]['admin_status']
            if peer_status == "up":
                enabled_size += 1
                name = "{}:down-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })
            else:
                name = "{}:down-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": False,
                    "bump": name,
                })
    pprint(segment_state)
    print(enabled_size)
    if interface_size == enabled_size:
        stm_status = True
        bump_status = True

make_logger()
try:
    api = saisei_api(server=host, port=port, user=id, password=passwd)
except Exception as e:
    logger.error('api: {}'.format(e))
    pass


def main():
    global stm_status, link_type, interface_size, segment_size
    # check if stm is alive, 
    while not stm_status:    
        logging_line()
        interface_attrs=[
            "name",
            "actual_direction",
            "state",
            "admin_status",
            "pci_address",
            "interface_id",
            "type",
            "peer"
        ]
        select_attrs = ",".join(interface_attrs)
        with_attr=["type"]
        with_arg=["ethernet"]
        response = api.rest.get(get_rest_url(select_attrs, with_attr, with_arg))
        # print(response["size"])
        if response['size'] > 1:
            stm_status=True

    interface_size=response['size']
    segment_size = int(interface_size)/2
    
    lspci = subprocess_open("lspci -m |grep Ether", 10)
    # devices = subprocess_open("cat /etc/stm/devices.csv", 10)
    collection=response['collection']

    # api.rest.get(get_rest_url(select_attrs, "pci_address", ""))
    # print(collection)
    lspci_header = ["pci_address", "controller", "factory", "link_type", "oem", "link_type2"]
    lspci_data_tmp = []
    for interface in lspci[0].split("\n"):
        # print(zip(lspci_header, interface.split(' "')))
        lspci_data_tmp.append(zip(lspci_header, interface.split(' "')))
        # lspci_data.append(interface.split(' "'))
        # pprint(interface.split(' "'))
        # lspci_data_row=""
        # for col in interface.split(' "'):
        #     col += " | "
        #     print(col)
        # lspci_data.append()
            
            # print(re.sub('"', '', col))
    # print(lspci[0].split("\n"))
    # print(lspci[0])
    lspci_data=[]
    for data in lspci_data_tmp:
        lspci_data.append(dict(data))

    
    # pprint(lspci_data)
    # pprint(lspci)
    devices=[]
    with open('/etc/stm/devices.csv', 'r') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            # print(row)
            devices.append(row)
            # jsonfile.write('\n')
        # print(devices[0].)
    
    # get link type
    for interface in collection:
        # if device['pci_address'] == interface['pci_address']:
        for data in lspci_data:
            if re.sub("0000:", "", interface['pci_address']) == data['pci_address']:
                # print(data['pci_address'])
                print(data['link_type'])
                if ('fiber' or 'SFP') in data['link_type']:
                    # if 'SFP' in data['link_type']:
                    print("fiber")
                    link_type = r'fiber'
                else:
                    link_type = r'copper'
            # print(re.sub("0000:", "", interface['pci_address']), data['pci_address'])
            # if interface['pci_address'] == lspci_data['pci_address']
        
    # pprint(devices)

    if not stm_status:
        # TODO: check bump and stm status
        print("check bump and stm status")
    else:
        # TODO: check bump and if is down enable bypass, else disable bypass
        print("# TODO: check bump and if is down enable bypass, else disable bypass")
        check_segment_state(select_attrs)
        for i, seg_state in enumerate(segment_state):
            if (i==0 and seg_state["state"]):
                print("disable seg1 bypass!")
                print(link_type)
                if link_type == "copper":
                    lsmod = subprocess_open("/sbin/lsmod | grep \"caswell_bpgen3\"", 10)
                    if lsmod[0] is "":
                        subprocess_open("insmod /opt/stm/bypass_drivers/portwell_kr/src/driver/caswell_bpgen3.ko board={}".format(board), 10)
                    bypass_state = subprocess_open('cat /sys/class/bypass/g3bp0/bypass', 10)
                    # print(bypass_state[0].strip('\n'))
                    if bypass_state[0].strip('\n') is not "n":
                        subprocess_open("echo 1 > /sys/class/bypass/g3bp0/func", 10)
                        subprocess_open("echo n > /sys/class/bypass/g3bp0/bypass", 10)
                        print("disable seg1 copper bypass!")
                else:
                    print("disable seg1 fiber bypass")
            if (i==1 and seg_state["state"]):
                print("disable seg2 bypass!")
            if (i==2 and seg_state["state"]):
                print("disable seg3 bypass!")                
            if (i==3 and seg_state["state"]):
                print("disable seg4 bypass!")                

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("The script is terminated by interrupt!")
        print("\r\nThe script is terminated by user interrupt!")
        print("Bye!!")
        sys.exit()
    except Exception as e:
        logger.error("main() cannot be running by some error, {}".format(e))
        print("{}".format(e))
        pass
