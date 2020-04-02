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
from time import sleep, time
import pdb

stm_ver=r'7.3'

# root = r'rest/stm/'
# suffix=r'configurations/running/users/?limit=0&with=last_traffic_time>'

LOG_FILENAME=r'/var/log/test_bypass.log'

stm_status=False
link_type=r'copper'
model_type=r'small'
cores_per_interface=0 # small,
interface_size=0
segment_size=0
segment_state=[]
bump_status=False
board = 'COSD304'
logger = None

err_lists = ['Cannot connect to server', 'does not exist', 'no matching objects', 'waiting for server']

class G(object):
    userid=r'cli_admin'
    passwd=r'cli_admin'
    host=r'localhost'
    port=r'5000'

    rest_basic_path=r'configurations/running/'
    rest_interface_path=r'interfaces/'
    rest_token=r'1'
    rest_order=r'>interface_id'
    rest_start=r'0'
    rest_limit=r'10'
    
    fiber_seg_slot_number=[]
    is_same_slot_number=[]

    segment1 = object()
    segment2 = object()
    segment3 = object()
    segment4 = object()
    # def __init__(self, rest_basic_path):
    #     self.rest_url = '%s' % (rest_basic_path)

    # def __str__(self):
    #     print("rest_url : ".format(self.rest_url))
    #     # pass

    # def get_rest_url(self):
    #     return self.rest_url

def timer(func):
    def wrapper():
        before = time()
        func()
        print("main() took {} seconds".format(time()- before))
        logger.info("main() took {} seconds".format(time()- before))
    return wrapper


class Resturl(G):
    def __init__(self, suffix, select_attrs, with_attr=[], with_val=[]):
        if len(with_attr) >= 2:
            self.select_attrs = ",".join(select_attrs)
            self.rest_url = '%s%s?token=%s&order=%s&start=%s&limit=%s&select=%s&with=%s=%s,%s=%s' \
            % ( G.rest_basic_path, 
                suffix, 
                G.rest_token, 
                G.rest_order, 
                G.rest_start, 
                G.rest_limit, 
                self.select_attrs, with_attr[0], with_val[0], with_attr[1], with_val[1])
        elif len(with_attr) == 1:
            self.select_attrs = ",".join(select_attrs)
            self.rest_url = '%s%s?token=%s&order=%s&start=%s&limit=%s&select=%s&with=%s=%s' \
            % ( G.rest_basic_path, 
                suffix, 
                G.rest_token, 
                G.rest_order, 
                G.rest_start, 
                G.rest_limit, 
                self.select_attrs, with_attr[0], with_val[0])
        else:
            self.select_attrs = select_attrs
            self.rest_url = '%s%s%s' \
            % ( G.rest_basic_path, 
                suffix,  
                self.select_attrs)
        # super(Restinterfaceurl, self).__init__(rest_basic_path)

    def __str__(self):
        return "RestUrl: %s" % (self.rest_url)

    def get_rest_url(self):
        return self.rest_url

    
# class Segment():

#     def __init__(self, interface):
#         self.interface = interface

    # def __str__(self):
    #     return "(name: {}, state: {}, admin_status: {})".format(self.int_name, self.state, self.admin_status)

    # def __repr__(self):
    #     return "Segment({})".format(self.name)


class Segment():

    def __init__(self, segment_number, ext_name, peer_name, ext_state, peer_state, ext_admin_status, peer_admin_status):
        self.name = "segment{}".format(segment_number)
        self.ext_name = ext_name
        self.peer_name = peer_name
        self.ext_state = ext_state
        self.peer_state = peer_state
        self.ext_admin_status = ext_admin_status
        self.peer_admin_status = peer_admin_status
        self.bypass_state = ""

    def __str__(self):
        return "(segment: {})".format(self.name)

    def log_state(self):
        logger.info("{0:22}{1:12}{2:12}{3:12}{4:12}{5:12}{6:15}{7:13}".format(
            self.name, 
            self.ext_name,
            self.ext_state, 
            self.ext_admin_status,
            self.peer_name, 
            self.peer_state,
            self.peer_admin_status,
            self.bypass_state
            ))

    def add_bypass_state(self, bypass_state):
        self.bypass_state = bypass_state


class Parameter(object):

    def __init__(self, cores_per_interface):
        self.cores_per_interface = cores_per_interface

    def get_parameter(self):
        return {"cores_per_interface": self.cores_per_interface}


# make_url = lambda suffix : 'http://%s:%d/%s%s' % (host, port, root, suffix)

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
    api = saisei_api(server=G.host, port=G.port, user=G.userid, password=G.passwd)
except Exception as e:
    logger.error('api: {}'.format(e))
    pass


class Timeout(Exception):
    '''subprocess 사용시 정상적인 반환을 안하는 경우 발생 '''

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
            try:
                if t == timeout-1:
                    p_open.kill()
                    raise Timeout
            except Timeout:
                logger.error("timout for running subprocess()")
                print("timout for running subprocess()")

def logging_line():
    logger.info("="*70)


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
                G.fiber_seg_slot_number.append({
                    "fiber_seg1_slot_number": row.split(":")[1].strip()
                })

            if 'segment2' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg2_slot_number": row.split(":")[1].strip()
                })

            if 'segment3' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg3_slot_number": row.split(":")[1].strip()
                })

            if 'segment4' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg4_slot_number": row.split(":")[1].strip()
                })

    if (G.fiber_seg_slot_number[0]["fiber_seg1_slot_number"] == G.fiber_seg_slot_number[1]["fiber_seg2_slot_number"]):
        G.is_same_slot_number.append({"seg1_seg2": True})
    else:
        G.is_same_slot_number.append({"seg1_seg2": False})

    if (G.fiber_seg_slot_number[2]["fiber_seg3_slot_number"] == G.fiber_seg_slot_number[3]["fiber_seg4_slot_number"]):
        G.is_same_slot_number.append({"seg3_seg4": True})
    else:
        G.is_same_slot_number.append({"seg3_seg4": False})        


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

# def get_rest_url(_select_attrs, _with_attr=[], _with_arg=[]):
#     # print(_with_arg)
#     if len(_with_attr) < 1:
#         return "{}{}{}".format(rest_basic_path, rest_interface_path, _select_attrs)

#     if len(_with_attr) > 1:
#         return "{}{}?token={}&order={}&start={}&limit={}&select={}&with={}={},{}={}".format(
#             rest_basic_path, rest_interface_path, rest_token, rest_order, rest_start, rest_limit, _select_attrs, _with_attr[0], _with_arg[0], _with_attr[1], _with_arg[1])
#     else:
#         return "{}{}?token={}&order={}&start={}&limit={}&select={}&with={}={}".format(
#             rest_basic_path, rest_interface_path, rest_token, rest_order, rest_start, rest_limit, _select_attrs, _with_attr[0], _with_arg[0])


# def get_cores_per_interface():
#     return int(api.rest.get("{}parameters?level=full&format=human&link=expand&time=utc".format(G.rest_basic_path))['collection'][0]['cores_per_interface'])


def set_segment_state(segment_number, peer_status, enabled_size, int_thread_state, interface, peer_int):
    global segment_state
    name = interface["name"]
    actual_direction = interface["actual_direction"]
    peer_name = interface["peer"]["link"]["name"]
    admin_status = interface["admin_status"]
    # pdb.set_trace()
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
    global cores_per_interface
    segment_state=[]    # init
    rest_url = Resturl(
            "interfaces/",
            ["name",
            "actual_direction",
            "state",
            "admin_status",
            "pci_address",
            "interface_id",
            "type",
            "peer"],
            ["type","actual_direction"],
            ["ethernet","external"])
    
    external_interfaces = api.rest.get(rest_url.get_rest_url())
    parameter_url = Resturl(
        "parameters?",
        "level=full&format=human&link=expand&time=utc")
    cores_per_interface = api.rest.get(parameter_url.get_rest_url())['collection'][0]["cores_per_interface"]
    enabled_size = 0    
    for i, interface in enumerate(external_interfaces["collection"], 1):
        # in case, segment 1
        if (i==1 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            rest_url = Resturl(
                "interfaces/",
                "{}?level=detail&format=human&link=expand&time=utc".format(interface["peer"]["link"]["name"]))
            peer_int = api.rest.get(rest_url.get_rest_url())['collection'][0]
            peer_status = peer_int['admin_status']
            G.segment1 = Segment(
                i, 
                interface["name"], 
                peer_int["name"], 
                interface["state"], 
                peer_int["state"], 
                interface["admin_status"], 
                peer_int["admin_status"])
            # print(G.segment1)  
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int)
        # in case, segment 2
        elif (i==2 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            rest_url = Resturl(
                "interfaces/",
                "{}?level=detail&format=human&link=expand&time=utc".format(interface["peer"]["link"]["name"]))
            peer_int = api.rest.get(rest_url.get_rest_url())['collection'][0]
            peer_status = peer_int['admin_status']
            G.segment2 = Segment(
                i, 
                interface["name"], 
                peer_int["name"], 
                interface["state"], 
                peer_int["state"], 
                interface["admin_status"], 
                peer_int["admin_status"])
            # print(G.segment2)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int)
        # in case, segment 3
        elif (i==3 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            rest_url = Resturl(
                "interfaces/",
                "{}?level=detail&format=human&link=expand&time=utc".format(interface["peer"]["link"]["name"]))
            peer_int = api.rest.get(rest_url.get_rest_url())['collection'][0]
            peer_status = peer_int['admin_status']
            G.segment3 = Segment(
                i, 
                interface["name"], 
                peer_int["name"], 
                interface["state"], 
                peer_int["state"], 
                interface["admin_status"], 
                peer_int["admin_status"])
            # print(G.segment3)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int)            
        # in case, segment 4
        elif (i==4 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            rest_url = Resturl(
                "interfaces/",
                "{}?level=detail&format=human&link=expand&time=utc".format(interface["peer"]["link"]["name"]))
            peer_int = api.rest.get(rest_url.get_rest_url())['collection'][0]
            peer_status = peer_int['admin_status']
            G.segment4 = Segment(
                i, 
                interface["name"], 
                peer_int["name"], 
                interface["state"], 
                peer_int["state"], 
                interface["admin_status"], 
                peer_int["admin_status"])
            # print(G.segment4)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int)        
        else:
            enabled_size += 0
            logger.error("There is no Segment.")
    if interface_size == enabled_size:
        stm_status = True
        bump_status = True
    else:
        stm_status = False
        bump_status = False

def do_copper_bypass(seg_number, action="disable"):
    bypass_state, _ = subprocess_open('cat /sys/class/bypass/g3bp{}/bypass'.format(seg_number), 10)
    try:
        # pdb.set_trace()
        if seg_number == 0:
            G.segment1.add_bypass_state(bypass_state.strip('\n'))
        if seg_number == 1:
            G.segment2.add_bypass_state(bypass_state.strip('\n'))
        if seg_number == 2:
            G.segment3.add_bypass_state(bypass_state.strip('\n'))
        if seg_number == 3:
            G.segment4.add_bypass_state(bypass_state.strip('\n'))

        if bypass_state.strip('\n') is not "n" and action == "disable":
        # if True:
            subprocess_open("echo 1 > /sys/class/bypass/g3bp{}/func".format(seg_number), 10)
            subprocess_open("echo n > /sys/class/bypass/g3bp{}/bypass".format(seg_number), 10)
            # logger.info("disable seg1 copper bypass!")
            logger.info("disable seg{} copper bypass!".format(int(seg_number)+1))

        elif bypass_state.strip('\n') is not "b" and action == "enable":
            subprocess_open("echo 1 > /sys/class/bypass/g3bp{}/func".format(seg_number), 10)
            subprocess_open("echo n > /sys/class/bypass/g3bp{}/bypass".format(seg_number), 10)
            # logger.info("disable seg1 copper bypass!")
            logger.info("enable seg{} copper bypass!".format(int(seg_number)+1))
        else:
            pass

    except Exception as e:
        logger.error(e)
        pass


def do_fiber_bypass(seg_number, action="disable"):
    if G.is_same_slot_number:
        bypass_state, _ = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
        try:
            if seg_number == 0:
                G.segment1.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 1:
                G.segment2.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 2:
                G.segment3.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 3:
                G.segment4.add_bypass_state(bypass_state.strip('\n'))
            # if True:
            if bypass_state.strip() is not "0" and action == "disable":
                subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            else:
                pass
        except Exception as e:
            logger.error(e)
            pass

        bypass_state, _ = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass1".format(G.fiber_seg_slot_number), 10)
        try:
            # if True:
            if bypass_state.strip() is not "0" and action == "disable":
                subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass1".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+2, G.fiber_seg_slot_number))
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass1".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            else:
                pass                   
        except Exception as e:
            logger.error(e)
            pass

    else:
        bypass_state, _ = subprocess_open("cat /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
        try:
            if seg_number == 0:
                G.segment1.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 1:
                G.segment2.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 2:
                G.segment3.add_bypass_state(bypass_state.strip('\n'))
            if seg_number == 3:
                G.segment4.add_bypass_state(bypass_state.strip('\n'))            
            # if True:
            if bypass_state.strip() is not "0":
                subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
                # print("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            else:
                pass                
        except Exception as e:
            logger.error(e)
            pass


# def disable_bypass(seg_number, fiber_seg_slot_number, is_same_slot_number):
def bypass_action(seg_number, action):
    global link_type
    if link_type == "copper":
        lsmod, _ = subprocess_open("/sbin/lsmod | grep \"caswell_bpgen3\"", 10)
        if lsmod is "":
                subprocess_open("insmod /opt/stm/bypass_drivers/portwell_kr/src/driver/caswell_bpgen3.ko", 10)
                logger.info("insert module caswell_bpgen3.ko for copper")
        do_copper_bypass(seg_number)

    # fiber 인 경우
    else:
        # TODO: 해당 폴더가 존재하는 검사할것
        fiber_module, _ =subprocess_open("lsmod | grep network_bypass | awk '{ print $1 }'", 10)
        i2c_module, _ =subprocess_open("lsmod | grep i2c_i801 | awk '{ print $1 }'", 10)
        if i2c_module is "":
            subprocess_open("modprobe i2c-i801", 10)
        if fiber_module is "":
            subprocess_open("insmod /opt/stm/bypass_drivers/portwell_fiber/driver/network-bypass.ko board={}".format(board), 10)  

        do_fiber_bypass(seg_number)



def bypass(action="disable"):
    global segment_state
    for i, seg_state in enumerate(segment_state):
        # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 같을 경우 처리로직 추가 필요
        # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 다를 경우 처리로직 추가 필요
        # 최대 4개의 세그먼트가 구성된다고 가정시, 
        # 1. 4개의 슬롯 - 각 슬롯별 1개의 세그먼트
        # 2. 2개의 슬롯 - 각 슬롯별 2개의 세그먼트
        # 1번 세그먼트
        # 반드시 segment 항목이 존재해야함.
        if (i==0 and seg_state["state"]):
            bypass_action(i, action)
        # 2번 세그먼트
        if (i==1 and seg_state["state"]):
            # if G.is_same_slot_number[0]["seg1_seg2"] == False:
            bypass_action(i, action)
        # 3번 세그먼트
        if (i==2 and seg_state["state"]):
            bypass_action(i, action)
        # 4번 세그먼트
        if (i==3 and seg_state["state"]):
            # if G.is_same_slot_number[1]["seg3_seg4"] == False:
            bypass_action(i, action)


def logging_state():
    logger.info("{0:22}{1:12}{2:12}{3:12}{4:12}{5:12}{6:15}{7:13}".format(
    "segment_name", "ext", "ext_state", "ext_admin", "peer", "peer_state", "peer_admin", "bypass_state"
    ))
    G.segment1.log_state()
    G.segment2.log_state()
    logger.info("link_type: {}, model_type: {}, cores_per_interface: {}".format(
        link_type, 
        model_type, 
        cores_per_interface))
    logging_line()


# @timer
def main():
    global stm_status, link_type, interface_size, segment_size, board
    # check if stm is alive, 
    while not stm_status:    
        rest_url = Resturl(
            "interfaces/",
            ["name",
            "actual_direction",
            "state",
            "admin_status",
            "pci_address",
            "interface_id",
            "type",
            "peer"],
            ["type"],
            ["ethernet"]
        )
        # print(rest_url)
        # url = Resturl("interfaces/")
        response = api.rest.get(rest_url.get_rest_url())
        if response['size'] > 1:
            stm_status=True

    while True:
        response = api.rest.get(rest_url.get_rest_url())
        try:
            interface_size = response['size']
            interface_size = int(interface_size)
            segment_size = int(interface_size)/2
        except Exception as e:
            logger.info(e)
            segment_size = 0
            pass

        get_fiber_slot()
        get_link_type()
    
        if not stm_status:
            # TODO: check bump and stm status[*]
            # TODO: add enable-bypass[*]
            check_segment_state()
            bypass("enable")
            # logger.info("{0:22}{1:12}{2:12}{3:12}{4:12}{5:12}{6:15}{7:13}".format(
            # "segment_name", "ext", "ext_state", "ext_admin", "peer", "peer_state", "peer_admin", "bypass_state"
            # ))
            logging_state()
        else:
            # TODO: check bump and if is down enable bypass, else disable bypass[*]
            # TODO: 파라미터에서 cores per interface 갯수 가지고 와서 스레드 체크하는 방식 개선하기[*]
            # TODO: check_segment_state 함수 class를 이용해서 개선하기[?]
            check_segment_state()
            bypass("disable")
            # G.segment1.add_bypass_state("n")
            # G.segment2.add_bypass_state("n")
            # logger.info("{0:22}{1:12}{2:12}{3:12}{4:12}{5:12}{6:15}{7:13}".format(
            # "segment_name", "ext", "ext_state", "ext_admin", "peer", "peer_state", "peer_admin", "bypass_state"
            # ))
            logging_state()
        # sleep(2)

if __name__ == "__main__":
    try:        
        main()
    except KeyboardInterrupt:
        logger.info("The script is terminated by interrupt!")
        print("\r\nThe script is terminated by user interrupt!")
        print("Bye!!")
        sys.exit()
    # except Exception as e:
    #     _, _ , tb = sys.exc_info()    # tb  ->  traceback
    #     print("{} : {}".format(e.message, tb.tb_lineno))
    #     logger.error("main() cannot be running by some error, {}".format(e))
    #     # sys.exit()
    #     pass
