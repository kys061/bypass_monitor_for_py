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
import pdb

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
model_type=r'small'
cores_per_interface=0 # small,
interface_size=0
segment_size=0
segment_state=[]
bump_status=False
board = 'COSD304'
fiber_seg_slot_number=[]
is_same_slot_number=[]

g_interface_attrs=[
    "name",
    "actual_direction",
    "state",
    "admin_status",
    "pci_address",
    "interface_id",
    "type",
    "peer"
]
g_select_attrs = ",".join(g_interface_attrs)
g_with_attr=["type"]
g_with_arg=["ethernet"]


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


make_logger()
try:
    api = saisei_api(server=host, port=port, user=id, password=passwd)
except Exception as e:
    logger.error('api: {}'.format(e))
    pass


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


class segment:
    def __init__(self):
        pass


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


def get_cores_per_interface():
    return int(api.rest.get("{}parameters?level=full&format=human&link=expand&time=utc".format(rest_basic_path))['collection'][0]['cores_per_interface'])



def set_segment_state(peer_status, enabled_size, int_thread_state, interface, peer_int):
    global segment_state
    if peer_status == "up":
        enabled_size += 1
        if (int_thread_state[0].strip() == interface["name"]):
            if cores_per_interface >= 1:
            # if model_type is not "small":
                int_peer_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(peer_int["name"], "{print $15}"), 10)
                if int_peer_thread_state[0].strip() == peer_int["name"]:
                    name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                    segment_state.append({
                        "state": True,
                        "bump": name,
                    })
                    return enabled_size
                else:
                    name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
                    segment_state.append({
                        "state": False,
                        "bump": name,
                    })
                    return enabled_size
            else:
                name = "{}:up-{}:up".format(interface["name"], interface["peer"]["link"]["name"])
                segment_state.append({
                    "state": True,
                    "bump": name,
                })
                return enabled_size
    else:
        name = "{}:up-{}:down".format(interface["name"], interface["peer"]["link"]["name"])
        segment_state.append({
            "state": False,
            "bump": name,
        })
        return enabled_size


def check_segment_state():
    '''
        세그먼트 상태, 인터페이스 상태 up의 조건
        1. adminstatus
        2. enabled
        3. link_type
        4. model_type
        5. interface thread status
    '''
    global segment_state, stm_status, bump_status
    global g_select_attrs, cores_per_interface

    external_interfaces = api.rest.get(get_rest_url(g_select_attrs, ["type","actual_direction"], ["ethernet","external"]))
    cores_per_interface = get_cores_per_interface()
    enabled_size = 0    
    
    for i, interface in enumerate(external_interfaces["collection"]):
        # in case, extnernal1
        if (i==0 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            print("ps -elL |grep {0}".format(interface["name"]))
            pprint(interface['name'])
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]
            peer_status = peer_int['admin_status']
            enabled_size = set_segment_state(peer_status, enabled_size, int_thread_state, interface, peer_int)
        # in case, external2
        elif (i==1 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            # print(interface["peer"]["link"]["name"])
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]
            peer_status = peer_int['admin_status']
            enabled_size = set_segment_state(peer_status, enabled_size, int_thread_state, interface, peer_int)
        # in case, external3
        elif (i==2 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]
            peer_status = peer_int['admin_status']
            enabled_size = set_segment_state(peer_status, enabled_size, int_thread_state, interface, peer_int)            
        # in case, external4
        elif (i==3 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = api.rest.get(get_rest_url(
                "{}?level=detail&format=human&link=expand&time=utc".format(
                    interface["peer"]["link"]["name"]
                    )
                ))['collection'][0]
            peer_status = peer_int['admin_status']
            enabled_size = set_segment_state(peer_status, enabled_size, int_thread_state, interface, peer_int)        
        else:
            enabled_size += 0
            name = "{}:down-{}:down".format("None", "None")
            segment_state.append({
                "state": False,
                "bump": name,
            })
    pprint(enabled_size)
    if interface_size == enabled_size:
        stm_status = True
        bump_status = True




def disable_bypass(seg_number, fiber_seg_slot_number, is_same_slot_number):
    global link_type
    if link_type == "copper":
        lsmod = subprocess_open("/sbin/lsmod | grep \"caswell_bpgen3\"", 10)
        if lsmod[0] is "":
            subprocess_open("insmod /opt/stm/bypass_drivers/portwell_kr/src/driver/caswell_bpgen3.ko", 10)
            logger.info("insert module caswell_bpgen3.ko for copper")
        bypass_state = subprocess_open('cat /sys/class/bypass/g3bp{}/bypass'.format(seg_number), 10)
        if bypass_state[0].strip('\n') is not "n":
        # if True:
            subprocess_open("echo 1 > /sys/class/bypass/g3bp{}/func".format(seg_number), 10)
            subprocess_open("echo n > /sys/class/bypass/g3bp{}/bypass".format(seg_number), 10)
            logger.info("disable seg1 copper bypass!")
            print("disable seg{} copper bypass!".format(int(seg_number)+1))
    # fiber 인 경우
    else:
        # TODO: 해당 폴더가 존재하는 검사할것
        fiber_module=subprocess_open("lsmod | grep network_bypass | awk '{ print $1 }'", 10)
        i2c_module=subprocess_open("lsmod | grep i2c_i801 | awk '{ print $1 }'", 10)
        if i2c_module[0] is "":
            subprocess_open("modprobe i2c-i801", 10)
        if fiber_module[0] is "":
            subprocess_open("insmod /opt/stm/bypass_drivers/portwell_fiber/driver/network-bypass.ko board={}".format(board), 10)
        
        # 세그먼트 1번 2번인 경우
        if (seg_number == 0 or seg_number == 1):
            if is_same_slot_number:
                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))

                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass1".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass1".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, fiber_seg_slot_number))
            else:
                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
        # 세그먼트 3번 4번인 경우
        else:
            if is_same_slot_number:
                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
                
                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass1".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass1".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, fiber_seg_slot_number))
            else:
                bypass_state = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                # if True:
                if bypass_state[0].strip() is not "0":
                    subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(fiber_seg_slot_number), 10)
                    logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))
                    print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, fiber_seg_slot_number))


def get_fiber_slot():
    # get fiber slot and bypass position()
    # 파일내에 반드시 segment1-4까지의 항목이 명시되어 있어야함.
    with open('/etc/stmfiles/files/scripts/deployconfig.txt', 'r') as f:
        rows = []
        for row in f:
            if 'segment' in row:
                rows.append(row)
        
        for row in rows:
            if 'segment1' in row:
                fiber_seg_slot_number.append({
                    "fiber_seg1_slot_number": row.split(":")[1].strip()
                })

            if 'segment2' in row:
                fiber_seg_slot_number.append({
                    "fiber_seg2_slot_number": row.split(":")[1].strip()
                })

            if 'segment3' in row:
                fiber_seg_slot_number.append({
                    "fiber_seg3_slot_number": row.split(":")[1].strip()
                })

            if 'segment4' in row:
                fiber_seg_slot_number.append({
                    "fiber_seg4_slot_number": row.split(":")[1].strip()
                })

    if (fiber_seg_slot_number[0]["fiber_seg1_slot_number"] == fiber_seg_slot_number[1]["fiber_seg2_slot_number"]):
        is_same_slot_number.append({"seg1_seg2": True})
    else:
        is_same_slot_number.append({"seg1_seg2": False})

    if (fiber_seg_slot_number[2]["fiber_seg3_slot_number"] == fiber_seg_slot_number[3]["fiber_seg4_slot_number"]):
        is_same_slot_number.append({"seg3_seg4": True})
    else:
        is_same_slot_number.append({"seg3_seg4": False})        


def get_link_type():
    global link_type
    cmd = r'/etc/stmfiles/files/scripts/dpdk_nic_bind.py -s |grep -B 15 "Network devices using kernel driver" |grep 0000'
    nic_bind=subprocess_open(cmd, 10)
    nic_bind = nic_bind[0].strip().split('\n')
    nic_data=[]
    for nic in nic_bind:
        nic_data.append({
            "pci_address": re.findall(r"0000:[0-9A-Za-z][0-9A-Za-z]:00.[0-9]", nic)[0].replace("0000:", ""),
            "link_type": re.findall(r"\'[0-9A-Za-z ]*\'", nic)[0].replace(" ", "")
        })
    
    for data in nic_data:
        if ('Fiber' or 'SFP') in data['link_type']:
            link_type = r'fiber'
        else:
            link_type = r'copper'
            # link_type = r'fiber'


def do_disable_bypass():
    # global segment_state
    pprint(segment_state)
    for i, seg_state in enumerate(segment_state):
            # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 같을 경우 처리로직 추가 필요
            # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 다를 경우 처리로직 추가 필요
            # 최대 4개의 세그먼트가 구성된다고 가정시, 
            # 1. 4개의 슬롯 - 각 슬롯별 1개의 세그먼트
            # 2. 2개의 슬롯 - 각 슬롯별 2개의 세그먼트
            # 1번 세그먼트
            # 반드시 segment 항목이 존재해야함.
            if (i==0 and seg_state["state"]):
                print("disable seg1 bypass!")
                disable_bypass(
                    i, 
                    fiber_seg_slot_number[0]["fiber_seg1_slot_number"], 
                    is_same_slot_number[0]["seg1_seg2"]
                )
            # 2번 세그먼트
            if (i==1 and seg_state["state"]):
                print("disable seg2 bypass!")
                if is_same_slot_number[0]["seg1_seg2"] == False:
                    disable_bypass(
                        i, 
                        fiber_seg_slot_number[1]["fiber_seg2_slot_number"], 
                        is_same_slot_number[0]["seg1_seg2"]
                    )
            # 3번 세그먼트
            if (i==2 and seg_state["state"]):
                print("disable seg3 bypass!")                
                disable_bypass(
                    i, 
                    fiber_seg_slot_number[2]["fiber_seg3_slot_number"], 
                    is_same_slot_number[1]["seg3_seg4"]
                )
            # 4번 세그먼트
            if (i==3 and seg_state["state"]):
                print("disable seg4 bypass!")                
                if is_same_slot_number[1]["seg3_seg4"] == False:
                    disable_bypass(
                        i, 
                        fiber_seg_slot_number[3]["fiber_seg4_slot_number"], 
                        is_same_slot_number[1]["seg3_seg4"]
                    )


def main():
    global stm_status, link_type, interface_size, segment_size, board
    global fiber_seg_slot_number, is_same_slot_number
    global g_select_attrs, g_with_attr, g_with_arg
    # check if stm is alive, 
    while not stm_status:    
        logging_line()
        response = api.rest.get(get_rest_url(g_select_attrs, g_with_attr, g_with_arg))
        if response['size'] > 1:
            stm_status=True

    interface_size=response['size']
    segment_size = int(interface_size)/2

    get_fiber_slot()
    get_link_type()
   
    if not stm_status:
        # TODO: check bump and stm status[*]
        print("check bump and stm status")
    else:
        # TODO: check bump and if is down enable bypass, else disable bypass[/]
        # TODO: 파라미터에서 interfaces per cores 갯수 가지고 와서 스레드 체크하는 방식 개선하기[?]
        print("# TODO: check bump and if is down enable bypass, else disable bypass")
        check_segment_state()
        do_disable_bypass()

        # TODO: add enable-bypass[?]
        

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
        # pass
