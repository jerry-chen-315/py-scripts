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
        #response = requests.get('http://kafka.apache.org/documentation.html', headers={'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0"})
        #if response.status_code == 200:
        #    raw = filter(lambda x: 'Mbean' in str(x), bs(response.content, "lxml").find_all('table', 'data-table'))[0].find_all('tr')[1: -1]
        #    self.mbeanName = map(lambda x2: x2[1].text, map(lambda x1: x1.find_all('td'), raw))


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
        #try:
        name = javax.management.ObjectName(rawname)
        info = self.mbeanConnection.getMBeanInfo(name)
        for attr in info.getAttributes():
            if self._isNum(self.mbeanConnection.getAttribute(name, str(attr.getName()))):
                attrs.append(attr.getName())
        #except e:
        #    print 'fetchAttrs exception---   %s' % rawname
        #    print '%s \n' % sys.exc_info()
        return attrs


    def fetchAttr(self, rawname, attrName):
        name = javax.management.ObjectName(rawname)
        metric = self.mbeanConnection.getAttribute(name, attrName)
        if 'value' in dir(metric):
            return metric.value
        elif 'contents' in dir(metric):
            values=str(metric.contents)
            values=re.sub('[{|}]','',values)
            values_dict=dict(item.split("=") for item in values.split(","))
            return values_dict

def load_JVM():
    jpype.startJVM(jpype.getDefaultJVMPath())
    java.lang.System.out.println("JVM load OK ...")


def table(mbeanName):
    return re.findall(r'name=\w+$', str(mbeanName))[0].split('=')[-1]


def tables(mbeanSet):
    tables = {}
    for mbean in mbeanSet:
        tables[str(mbean.name)] = table(mbean.name)
    return tables

def writeES(metric_doc,section):
    esnode=json.loads(pars.get(section,"esnode"))
    es = Elasticsearch(esnode,sniff_on_start=True,sniff_on_connection_fail=True,sniffer_timeout=60)
    day=datetime.today().strftime('%Y.%m.%d')
    index_name='jmx'+'-'+datetime.today().strftime('%Y.%m.%d')
    for doc in metric_doc:
        es.index(index=index_name,doc_type=section,body=doc)
    es.indices.refresh(index=index_name)
    return

def loop(interval,hosts,port,mbean_dict,section):
    while(True):
        result_list = []
        metric_dict = {}
        timestamp=datetime.now()
        for host in hosts:
            jconn = Jmxes(host,port)
            for rawname in mbean_dict:
                for attrname in mbean_dict[rawname]:
                    tmp_name=re.sub(r"[.|:]","_",rawname)
                    metric_dict=dict(item.split("=") for item in tmp_name.split(","))
                    metric_dict[attrname]=jconn.fetchAttr(rawname, attrname)
                    metric_dict['hostname']=host
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
        loop(interval,hosts,port,mbean_dict,section)
    else:
        print "Please edit parameter file 'jmx_pars.ini'"
