#!/usr/bin/env python
# _*_ coding:utf-8 _*_


import configparser
from base import setting


def get_config_value(group, key):
    con = configparser.ConfigParser()
    con.read(setting.CONFIG_DIR, encoding="utf-8")
    return con.get(group, key)
