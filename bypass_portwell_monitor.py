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
rest_order=r'<name'
rest_start=r'0'
rest_limit=r'10'
LOG_FILENAME=r'/var/log/stm_bypass.log'
stm_status=False


logger = None

err_lists = ['Cannot connect to server', 'does not exist', 'no matching objects', 'waiting for server']


def make_logger():
    global logger
    try:
        logger = logging.getLogger('saisei.thread_monitor')
        fh = RotatingFileHandler(LOG_FILENAME, 'a', 50 * 1024 * 1024, 4)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print('cannot make logger, please check system, {}'.format(e))
    else:
        logger.info("***** logger starting %s *****" % (sys.argv[0]))


def logging_line():
    logger.info("=================================")


def get_rest_url(_select_attrs, _with_attr, _with_arg):
    return "{}{}?token={}&order={}&start={}&limit={}&select={}&with={}={}".format(
        rest_basic_path, rest_interface_path, rest_token, rest_order, rest_start, rest_limit, _select_attrs, _with_attr, _with_arg)


make_logger()
try:
    api = saisei_api(server=host, port=port, user=id, password=passwd)
except Exception as e:
    logger.error('api: {}'.format(e))
    pass


def main():
    logging_line()
    interface_attrs=[
        "name",
        "actual_direction",
        "state",
        "admin_status",
    ]
    select_attrs = ",".join(interface_attrs)
    with_attr="type"
    with_arg="ethernet"
    response = api.rest.get(get_rest_url(select_attrs, with_attr, with_arg))
    collection = response['collection']
    print(response['size'])
    for interface in collection:
        print(interface['state'])


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
        pass
