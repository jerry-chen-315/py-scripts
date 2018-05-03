#! /usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import with_statement
from collections import defaultdict
from multiprocessing import Process
#from bs4 import BeautifulSoup as bs
from datetime import datetime
#import requests
import argparse
from ConfigParser import ConfigParser
import json
import copy
from time import sleep
import re
import os
import sys
import jpype
from jpype import java
from jpype import javax
from elasticsearch import Elasticsearch
import pprint


class Jmxes:
    def __init__(self, host, port):
        self.mbeanConnection = self._mbean_connection(host, port)

    def _mbean_connection(self, host, port):
        jmxurl = javax.management.remote.JMXServiceURL('service:jmx:rmi:///jndi/rmi://%s:%d/jmxrmi' % (host, port))
        jhash = java.util.HashMap()
        jarray = jpype.JArray(java.lang.String)([])
        jhash.put (javax.management.remote.JMXConnector.CREDENTIALS, jarray)
        jmxsoc = javax.management.remote.JMXConnectorFactory.connect(jmxurl, jhash)
        return jmxsoc.getMBeanServerConnection()


    def queryMBeans(self, name=None, attr=None):
        resultSet = self.mbeanConnection.queryMBeans(javax.management.ObjectName(name), attr)
        return resultSet


    def _isNum(self, waited):
        result = False
        try:
            waited = waited.value
            result = isinstance(waited, int) or isinstance(waited, long) or isinstance(waited, float)
        except:
            result = False
        return result


    def fetchAttrs(self, rawname):
        attrs = []
        name = javax.management.ObjectName(rawname)
        info = self.mbeanConnection.getMBeanInfo(name)
        for attr in info.getAttributes():
            if self._isNum(self.mbeanConnection.getAttribute(name, str(attr.getName()))):
                attrs.append(attr.getName())
        return attrs


    def fetchAttr(self, rawname, attrName):
        name = javax.management.ObjectName(rawname)
        metric = self.mbeanConnection.getAttribute(name, attrName)
        if 'value' in dir(metric):
            return metric.value
        elif 'contents' in dir(metric):
            values_dict={}
            for key in metric.contents:
                values_dict[key]=metric.get(key)
            return values_dict

def load_JVM():
    jpype.startJVM(jpype.getDefaultJVMPath())
    java.lang.System.out.println("JVM load OK ...")

def writeES(metric_doc,section):
    esnode=json.loads(pars.get(section,"esnode"))
    es = Elasticsearch(esnode,sniff_on_start=True,sniff_on_connection_fail=True,sniffer_timeout=60)
    day=datetime.today().strftime('%Y.%m.%d')
    index_name='jmx'+'-'+datetime.today().strftime('%Y.%m.%d')
    for doc in metric_doc:
        es.index(index=index_name,doc_type=section,body=doc)
    es.indices.refresh(index=index_name)
    return

def loop(interval,jconn_dict,mbean_dict,section):
    while(True):
        result_list = []
        metric_dict = {}
        timestamp=datetime.utcnow()
        for hostname,jconn in jconn_dict.items():
            for rawname in mbean_dict:
                for attrname in mbean_dict[rawname]:
                    tmp_name=re.sub(r"[.|:]","_",rawname)
                    metric_dict=dict(item.split("=") for item in tmp_name.split(","))
                    metric_dict[attrname]=jconn.fetchAttr(rawname, attrname)
                    metric_dict['hostname']=hostname
                    metric_dict['timestamp']=timestamp
                    result_list.append(metric_dict)
        writeES(result_list,section)  
        sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-s', '--section', type=str, help='section name')
    args = parser.parse_args()
    section=args.section
    if section is None:
       parser.print_help()
       sys.exit(2)
    pars=ConfigParser()
    pars.read(os.getcwd()+'/parfile.ini')
    hosts=json.loads(pars.get(section,"hosts"))
    port=pars.getint(section,"port")
    interval=pars.getint(section,"interval")
    query_list = json.loads(pars.get(section,'query'))
    jconn_dict={}
    if hosts:
        try:
            load_JVM()
        except Exception as err:
            print ("failed start jvm: %s" % err)    
        mbean_dict={}
        for item in query_list:
            if '*' in  item['object_name']:
                mbeanname=item['object_name']
                jconn = Jmxes(hosts[0],port)
                mbean_set=jconn.queryMBeans(mbeanname)
                for mbean in mbean_set:
                    mbean_dict[str(mbean.name)]=item['attributes']
            else:
                mbean_dict[item['object_name']]=item['attributes']
        for host in hosts:
            jconn_dict[host]=Jmxes(host,port)
        loop(interval,jconn_dict,mbean_dict,section)
    else:
        print "Please edit parameter file 'jmx_pars.ini'"
