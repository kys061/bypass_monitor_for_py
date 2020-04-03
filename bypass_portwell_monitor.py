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
logger = None
# err_lists = ['Cannot connect to server', 'does not exist', 'no matching objects', 'waiting for server']
# logging_temp = `{0:16}{1:8}{2:16}{3:16}{4:16}{5:16}{6:16}{7:16}{8:16}`

class Segment(object):
    def __init__(self):
        self.__name, self.__bypass_state, self.__segment_state = None, None, None
        self.__ext_name, self.__ext_state, self.__ext_admin_status = None, None, None
        self.__peer_name, self.__peer_state, self.__peer_admin_status = None, None, None
        self.__slot = None
        
    def __str__(self):
        return "(segment: {})".format(self.name)

    def log_segment_state(self):
        logger.info("{0:7}{1:13}{2:13}{3:15}{4:15}{5:13}{6:13}{7:15}{8:13}{9:13}".format(
            self.slot, self.name, self.segment_state, 
            self.ext_name, self.ext_state, self.ext_admin_status,
            self.peer_name, self.peer_state, self.peer_admin_status,
            self.bypass_state
            ))

    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, val):
        self.__name = "segment" + val

    @property
    def bypass_state(self):
        return self.__bypass_state
        
    @bypass_state.setter
    def bypass_state(self, val):
        self.__bypass_state = val
    
    @property
    def segment_state(self):
        return self.__segment_state
    
    @segment_state.setter
    def segment_state(self, val):
        # print(val)
        if val:
            self.__segment_state = "True"
        else:
            self.__segment_state = "False"        

    @property
    def ext_name(self):
        return self.__ext_name
    
    @ext_name.setter
    def ext_name(self, val):
        self.__ext_name = val

    @property
    def ext_state(self):
        return self.__ext_state
    
    @ext_state.setter
    def ext_state(self, val):
        self.__ext_state = val

    @property
    def ext_admin_status(self):
        return self.__ext_admin_status
    
    @ext_admin_status.setter
    def ext_admin_status(self, val):
        self.__ext_admin_status = val                

    @property
    def peer_name(self):
        return self.__peer_name
    
    @peer_name.setter
    def peer_name(self, val):
        self.__peer_name = val
    
    @property
    def peer_state(self):
        return self.__peer_state
    
    @peer_state.setter
    def peer_state(self, val):
        self.__peer_state = val

    @property
    def peer_admin_status(self):
        return self.__peer_admin_status
    
    @peer_admin_status.setter
    def peer_admin_status(self, val):
        self.__peer_admin_status = val

    @property
    def slot(self):
        return self.__slot
        
    @slot.setter
    def slot(self, val):
        self.__slot = val        

    # def add_bypass_state(self, bypass_state):
    #     self.bypass_state = bypass_state

    # def update_segment_state(self, segment_state):
    #     self.segment_state = segment_state

    # def get_segment_state(self):
    #     return self.segment_state

    # def get_attr(self, attr_name):
    #     if "link_type" == attr_name:
    #         return self.link_type
    #     else:
    #         return None


class G(object):
    __instance = None
    _segment = list()
        
    stm_status=False

    userid=r'cli_admin'
    passwd=r'cli_admin'
    host=r'localhost'
    port=r'5000'

    rest_basic_path=r'configurations/running/'
    rest_token=r'1'
    rest_order=r'>interface_id'
    rest_start=r'0'
    rest_limit=r'10'
    
    link_type=r'copper'
    model_type=r'small'
    cores_per_interface=0 # small,
    interface_size=0
    segment_size=0
    board = 'COSD304'

    fiber_seg_slot_number=[]
    is_same_slot_number=[]
    segment_state=[]

    segment1 = Segment()
    segment2 = Segment()
    segment3 = Segment()
    segment4 = Segment()

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance

    @classmethod
    def append_segment_data(cls, data):
        cls._segment.append(data)


class Resturl():
    def __init__(self, saisei_class, select_attrs, with_attrs=[], with_vals=[]):
        if len(with_attrs) >= 2:
            self.select_attrs = ",".join(select_attrs)
            with_patterns = []
            for i, attr in enumerate(with_attrs):
                for j, val in enumerate(with_vals):
                    if i==j:
                        with_pattern = "%s=%s" % (attr, val)
                        with_patterns.append(with_pattern)
            with_patterns = ",".join(with_patterns)
            self.rest_url = '%s%s?token=%s&order=%s&start=%s&limit=%s&select=%s&with=%s' \
            % ( G.rest_basic_path, 
                saisei_class, 
                G.rest_token, 
                G.rest_order, 
                G.rest_start, 
                G.rest_limit, 
                self.select_attrs, with_patterns)
        elif len(with_attrs) == 1:
            self.select_attrs = ",".join(select_attrs)
            with_pattern = None
            for i, attr in enumerate(with_attrs):
                for j, val in enumerate(with_vals):
                    if i==j:
                        with_pattern = "%s=%s" % (attr, val)
            self.rest_url = '%s%s?token=%s&order=%s&start=%s&limit=%s&select=%s&with=%s' \
            % ( G.rest_basic_path, 
                saisei_class, 
                G.rest_token, 
                G.rest_order, 
                G.rest_start, 
                G.rest_limit, 
                self.select_attrs, with_pattern)
        else:
            self.select_attrs = select_attrs
            self.rest_url = '%s%s%s' \
            % ( G.rest_basic_path, 
                saisei_class,  
                self.select_attrs)

    def __str__(self):
        return "RestUrl: %s" % (self.rest_url)

    def get_rest_url(self):
        return self.rest_url


def timer(func):
    def wrapper():
        before = time()
        func()
        print("main() took {} seconds".format(time()- before))
        logger.info("main() took {} seconds".format(time()- before))
    return wrapper


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
        sys.exit()
    else:
        logger.info("***** logger starting %s *****" % (sys.argv[0]))


make_logger()
try:
    api = saisei_api(server=G.host, port=G.port, user=G.userid, password=G.passwd)
except Exception as e:
    logger.error('api: {}'.format(e))
    pass


class Timeout(Exception):
    '''쉘에서 정상적인 반환을 안하는 경우 발생 '''


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
                logger.error("timout while running subprocess()")


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
                if G.link_type == "fiber":
                    G.segment1.slot = row.split(":")[1].strip()
                else:
                    G.segment1.slot = "None"

            if 'segment2' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg2_slot_number": row.split(":")[1].strip()
                })
                if G.link_type == "fiber":
                    G.segment2.slot = row.split(":")[1].strip()
                else:
                    G.segment2.slot = "None"

            if 'segment3' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg3_slot_number": row.split(":")[1].strip()
                })
                if G.link_type == "fiber":
                    G.segment3.slot = row.split(":")[1].strip()
                else:
                    G.segment3.slot = "None"

            if 'segment4' in row:
                G.fiber_seg_slot_number.append({
                    "fiber_seg4_slot_number": row.split(":")[1].strip()
                })
                if G.link_type == "fiber":
                    G.segment4.slot = row.split(":")[1].strip()
                else:
                    G.segment4.slot = "None"

    if (G.fiber_seg_slot_number[0]["fiber_seg1_slot_number"] == G.fiber_seg_slot_number[1]["fiber_seg2_slot_number"]):
        G.is_same_slot_number.append({"seg1_seg2": True})
    else:
        G.is_same_slot_number.append({"seg1_seg2": False})

    if (G.fiber_seg_slot_number[2]["fiber_seg3_slot_number"] == G.fiber_seg_slot_number[3]["fiber_seg4_slot_number"]):
        G.is_same_slot_number.append({"seg3_seg4": True})
    else:
        G.is_same_slot_number.append({"seg3_seg4": False})        


def set_link_type():
    cmd = r'/etc/stmfiles/files/scripts/dpdk_nic_bind.py -s |grep -B 15 "Network devices using kernel driver" |grep 0000'
    nic_bind, _ = subprocess_open(cmd, 10)
    try:
        nic_bind = nic_bind.strip().split('\n')
    except Exception as e:
        logger.error(e)
        pass
    nic_data=[]
    for nic in nic_bind:
        nic_data.append({
            "pci_address": re.findall(r"0000:[0-9A-Za-z][0-9A-Za-z]:00.[0-9]", nic)[0].replace("0000:", ""),
            "link_type": re.findall(r"\'[0-9A-Za-z ]*\'", nic)[0].replace(" ", "")
        })
    for data in nic_data:
        if ('Fiber' or 'SFP') in data['link_type']:
            # G.segment1.update_attrs(link_type="fiber")
            G.link_type = r'fiber'
        else:
            # G.segment1.update_attrs(link_type="copper")
            G.link_type = r'copper'


def get_interface_info(saisei_class, select_attrs, with_attrs, with_vals):
    rest_url = Resturl(
                saisei_class,
                select_attrs,
                with_attrs,
                with_vals
            )
    response = api.rest.get(rest_url.get_rest_url())
    return response


def get_peer_interface_info(peer_name):
    rest_url = Resturl("interfaces/", "{}?level=detail&format=human&link=expand&time=utc".format(peer_name))
    peer_int = api.rest.get(rest_url.get_rest_url())['collection'][0]
    return peer_int



def set_segment_state(segment_number, peer_status, enabled_size, int_thread_state, interface, peer_int, segment):
    name = interface["name"]
    actual_direction = interface["actual_direction"]
    peer_name = interface["peer"]["link"]["name"]
    admin_status = interface["admin_status"]
    if peer_status == "up":
        enabled_size += 1
        if (int_thread_state.strip() == interface["name"]):
            if G.cores_per_interface >= 1:
                int_peer_thread_state, _ = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(peer_int["name"], "{print $15}"), 10)
                if int_peer_thread_state.strip() == peer_int["name"]:
                    # segment.update_segment_state(True)
                    segment.segment_state = True
                    G.segment_state.append(segment)
                    return enabled_size
                else:
                    # segment.update_segment_state(False)
                    segment.segment_state = False
                    G.segment_state.append(segment)
                    
                    return enabled_size
            else:
                # segment.update_segment_state(True)
                segment.segment_state = True
                G.segment_state.append(segment)
                return enabled_size
    else:
        # segment.update_segment_state(False)
        segment.segment_state = False
        G.segment_state.append(segment)
        return enabled_size


def set_parameter_info(attr="cores_per_interface"):
    parameter_url = Resturl(
    "parameters?",
    "level=full&format=human&link=expand&time=utc")
    G.cores_per_interface = api.rest.get(parameter_url.get_rest_url())['collection'][0][attr] 


def set_segment_obj(seg_num, interface, peer_int):
    for i, seg in enumerate([G.segment1, G.segment2, G.segment3, G.segment4], 1):
        if seg_num == i:
            seg.name = str(seg_num)
            seg.ext_name = interface["name"]
            seg.ext_admin_status = interface["admin_status"]
            seg.ext_state = interface["state"]
            seg.peer_name = peer_int["name"]
            seg.peer_admin_status = peer_int["admin_status"]
            seg.peer_state = peer_int["state"]


def check_segment_state():
    '''
        세그먼트 상태, 인터페이스 상태 up의 조건
        1. adminstatus
        2. enabled
        3. link_type
        4. model_type
        5. interface thread status
    '''
    G.segment_state=[]    # init
    saisei_class = "interfaces/"
    select_attrs = ["name", "actual_direction", "state", "admin_status", "pci_address", "interface_id", "type", "peer"]
    with_attrs = ["type", "actual_direction"]
    with_vals = ["ethernet", "external"]

    external_interfaces = get_interface_info(saisei_class, select_attrs, with_attrs, with_vals)
    set_parameter_info(attr="cores_per_interface")
    enabled_size = 0    
    for i, interface in enumerate(external_interfaces["collection"], 1):
        # in case, segment 1
        if (i==1 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state, _ = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = get_peer_interface_info(interface["peer"]["link"]["name"])
            peer_status = peer_int['admin_status']
            set_segment_obj(i, interface, peer_int)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int, G.segment1)
        # in case, segment 2
        elif (i==2 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state, _ = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = get_peer_interface_info(interface["peer"]["link"]["name"])
            peer_status = peer_int['admin_status']
            set_segment_obj(i, interface, peer_int)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int, G.segment2)
        # in case, segment 3
        elif (i==3 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state, _ = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = get_peer_interface_info(interface["peer"]["link"]["name"])
            peer_status = peer_int['admin_status']
            set_segment_obj(i, interface, peer_int)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int, G.segment3)            
        # in case, segment 4
        elif (i==4 and interface["state"] == "enabled" and interface["admin_status"] == "up"):
            enabled_size += 1
            int_thread_state, _ = subprocess_open(r"ps -elL |grep {} |awk '{}'".format(interface["name"], "{print $15}"), 10)
            peer_int = get_peer_interface_info(interface["peer"]["link"]["name"])
            peer_status = peer_int['admin_status']
            set_segment_obj(i, interface, peer_int)
            enabled_size = set_segment_state(i, peer_status, enabled_size, int_thread_state, interface, peer_int, G.segment4)        
        else:
            enabled_size += 0
            logger.error("There is no Segment.")
    if G.interface_size == enabled_size:
        G.stm_status = True
    else:
        G.stm_status = False

def do_copper_bypass(seg_number, action="disable"):
    bypass_state, _ = subprocess_open('cat /sys/class/bypass/g3bp{}/bypass'.format(seg_number), 10)
    try:
        if seg_number == 0:
            G.segment1.bypass_state = bypass_state.strip('\n')
        if seg_number == 1:
            G.segment2.bypass_state = bypass_state.strip('\n')
        if seg_number == 2:
            G.segment3.bypass_state = bypass_state.strip('\n')
        if seg_number == 3:
            G.segment4.bypass_state = bypass_state.strip('\n')

        if bypass_state.strip('\n') is not "n" and action == "disable":
        # if True:
            subprocess_open("echo 1 > /sys/class/bypass/g3bp{}/func".format(seg_number), 10)
            subprocess_open("echo n > /sys/class/bypass/g3bp{}/bypass".format(seg_number), 10)
            logger.info("disable seg{} copper bypass!".format(int(seg_number)+1))

        elif bypass_state.strip('\n') is not "b" and action == "enable":
            subprocess_open("echo 1 > /sys/class/bypass/g3bp{}/func".format(seg_number), 10)
            subprocess_open("echo n > /sys/class/bypass/g3bp{}/bypass".format(seg_number), 10)
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
                G.segment1.bypass_state = bypass_state.strip('\n')
            if seg_number == 1:
                G.segment2.bypass_state = bypass_state.strip('\n')
            if seg_number == 2:
                G.segment3.bypass_state = bypass_state.strip('\n')
            if seg_number == 3:
                G.segment4.bypass_state = bypass_state.strip('\n')
            # if True:
            if bypass_state.strip() is not "0" and action == "disable":
                subprocess_open("echo 0 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
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
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass1".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass1 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
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
            elif bypass_state.strip() is not "2" and action == "enable":
                subprocess_open("echo 2 > /sys/class/misc/caswell_bpgen2/{}/bypass0".format(G.fiber_seg_slot_number), 10)
                logger.info("disable seg{} fiber bypass0 in {}!".format(int(seg_number)+1, G.fiber_seg_slot_number))
            else:
                pass                
        except Exception as e:
            logger.error(e)
            pass


def bypass_action(seg_number, action):

    if G.link_type == "copper":
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
            subprocess_open("insmod /opt/stm/bypass_drivers/portwell_fiber/driver/network-bypass.ko board={}".format(G.board), 10)  

        do_fiber_bypass(seg_number)



def bypass(action="disable"):
    for i, segment in enumerate(G.segment_state):
        # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 같을 경우 처리로직 추가 필요
        # TODO: 1번과 2번 세그먼트의 슬롯 넘버가 다를 경우 처리로직 추가 필요
        # 최대 4개의 세그먼트가 구성된다고 가정시, 
        # 1. 4개의 슬롯 - 각 슬롯별 1개의 세그먼트
        # 2. 2개의 슬롯 - 각 슬롯별 2개의 세그먼트
        # 1번 세그먼트
        # 반드시 segment 항목이 존재해야함.
        if (i==0 and segment.segment_state):
            bypass_action(i, action)
        # 2번 세그먼트
        if (i==1 and segment.segment_state):
            bypass_action(i, action)
        # 3번 세그먼트
        if (i==2 and segment.segment_state):
            bypass_action(i, action)
        # 4번 세그먼트
        if (i==3 and segment.segment_state):
            bypass_action(i, action)


def logging_state():
    logger.info("{0:7}{1:13}{2:13}{3:15}{4:15}{5:13}{6:13}{7:15}{8:13}{9:13}".format(
    "[slot]", "[seg_name]", "[seg_state]", "[ext_int_name]", "[ext_state]", "[ext_admin]", "[peer]", "[peer_state]", "[peer_admin]", "[bypass_state]"
    ))
    G.segment1.log_segment_state()
    G.segment2.log_segment_state()
    logger.info("{0:16}{1:16}{2:16}".format("[link_type]", "[model_type]", "[cores_per_interface]"))
    logger.info("{0:16}{1:16}{2:16}".format(G.link_type, G.model_type, G.cores_per_interface))
    logging_line()



# @timer
def main():
    saisei_class = "interfaces/"
    select_attrs = ["name", "actual_direction", "state", "admin_status", "pci_address", "interface_id", "type", "peer"]
    with_attrs = ["type"]
    with_vals = ["ethernet"]
    while not G.stm_status:
        response = get_interface_info(saisei_class, select_attrs, with_attrs, with_vals)
        if response['size'] > 1:
            G.stm_status = True
        else:
            G.stm_status = False      
  
    while True:
        response = get_interface_info(saisei_class, select_attrs, with_attrs, with_vals)
        try:
            G.interface_size = response['size']
            G.interface_size = int(G.interface_size)
            G.segment_size = int(G.interface_size)/2
        except Exception as e:
            logger.info(e)
            G.segment_size = 0
            pass

        get_fiber_slot()
        set_link_type()
    
        if not G.stm_status:
            # TODO: check bump and stm status[*]
            # TODO: add enable-bypass[*]
            check_segment_state()
            bypass("enable")
            logging_state()
        else:
            # TODO: check bump and if is down enable bypass, else disable bypass[*]
            # TODO: 파라미터에서 cores per interface 갯수 가지고 와서 스레드 체크하는 방식 개선하기[*]
            # TODO: check_segment_state 함수 class를 이용해서 개선하기[?]
            check_segment_state()
            bypass("disable")
            # pdb.set_trace()
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
