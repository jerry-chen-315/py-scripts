#!/usr/local/bin/python
# -*- coding: utf-8 -*-
## description   :vcenter event ETL
## author        :chenhao 
## created       :2018-09-26
# record file: {"HXQ": {"id": 1, "cid": 110906735}, "DMZ": {"id": 1, "cid": 582737}, "LAB": {"id": 1, "cid": 2544189}, "QZQ": {"id": 1, "cid": 275351}}

import json
import os
import pyodbc
from datetime import datetime, timedelta
from kafka import KafkaProducer
import logging
import pprint
import psycopg2


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='log.vcenter_event',filemode='a',level=logging.INFO)

def handle_event(event_result,producer):
    try:
        msg = {}
        buffer_events = []
        keys_before = ['chain_id','event_type','@timestamp','username','vm_id','vm_name','from_host','from_ds','area']
        keys_after = ['chain_id','event_type','@timestamp','username','vm_id','vm_name','to_host','to_ds','area']
        clone_after = ['chain_id','event_type','@timestamp','username','to_vm_id','to_vm_name','to_host','to_ds','area']
        for line in event_result:
            chain_id = line[0]
            vm_id = line[4]
            if line[1] == 'VmBeingRelocatedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and event[1]['vm_id'] == vm_id and 'to_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:        
                    buffer_events.append(dict(zip(keys_before,line)))
                elif len(exist_event) == 1:
                    idx = exist_event[0][0]
                    #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['@timestamp'] = line[2]
                    tmp_msg['from_host'] = line[6]
                    tmp_msg['from_ds'] = line[7]
                    msg = format_msg(1,'relocate',tmp_msg)
                    producer.send('vcenter-event',value=msg)        
            elif line[1] == 'VmRelocatedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and event[1]['vm_id'] == vm_id and 'from_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:
                    buffer_events.append(dict(zip(keys_after,line)))
                elif len(exist_event) == 1:
                    idx=exist_event[0][0]
                 #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['to_host'] = line[6]
                    tmp_msg['to_ds'] = line[7]
                    msg = format_msg(1,'relocate',tmp_msg)
                    producer.send('vcenter-event',value=msg)        
            elif line[1] == 'VmBeingHotMigratedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and event[1]['vm_id'] == vm_id and 'to_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:
                    buffer_events.append(dict(zip(keys_before,line)))
                elif len(exist_event) == 1:
                    idx=exist_event[0][0]
                 #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['@timestamp'] = line[2]
                    tmp_msg['from_host'] = line[6]
                    tmp_msg['from_ds'] = line[7]
                    msg = format_msg(1,'migrate',tmp_msg)
                    producer.send('vcenter-event',value=msg)        
            elif line[1] == 'VmMigratedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and event[1]['vm_id'] == vm_id and 'from_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:
                    buffer_events.append(dict(zip(keys_after,line)))
                elif len(exist_event) == 1:
                    idx=exist_event[0][0]
                 #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['to_host'] = line[6]
                    tmp_msg['to_ds'] = line[7]
                    msg = format_msg(1,'migrate',tmp_msg)
                    producer.send('vcenter-event',value=msg) 
            ###########################################################
            elif line[1] == 'VmBeingClonedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and 'to_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:
                    buffer_events.append(dict(zip(keys_before,line)))
                elif len(exist_event) == 1:
                    idx=exist_event[0][0]
                 #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['@timestamp'] = line[2]
                    tmp_msg['from_host'] = line[6]
                    tmp_msg['from_ds'] = line[7]
                    msg = format_msg(1,'clone',tmp_msg)
                    producer.send('vcenter-event',value=msg)        
            elif line[1] == 'VmClonedEvent':
                exist_event = list(filter(lambda event: event[1]['chain_id'] == chain_id and 'from_host' in event[1],enumerate(buffer_events)))
                if len(exist_event) == 0:
                    buffer_events.append(dict(zip(clone_after,line)))
                elif len(exist_event) == 1:
                    idx=exist_event[0][0]
                 #  delete entry from buffer_events
                    tmp_msg = buffer_events.pop(idx)
                    tmp_msg['to_vm_name'] = line[5]
                    tmp_msg['to_host'] = line[6]
                    tmp_msg['to_ds'] = line[7]
                    msg = format_msg(1,'clone',tmp_msg)
                    producer.send('vcenter-event',value=msg)  
            ##########################################################            
            elif line[1] == 'VmGuestRebootEvent' or line[1] == 'VmResettingEvent':
                tmp_msg = dict(zip(keys_after,line))
                msg = format_msg(1,'reboot',tmp_msg)
                producer.send('vcenter-event',value=msg)        
            elif line[1] == 'VmPoweredOffEvent' or line[1] == 'VmGuestShutdownEvent':
                tmp_msg = dict(zip(keys_after,line))
                msg = format_msg(1,'shutdown',tmp_msg)
                producer.send('vcenter-event',value=msg)        
            elif line[1] == 'DrsVmPoweredOnEvent' or line[1] == 'VmPoweredOnEvent':
                tmp_msg = dict(zip(keys_after,line))
                msg = format_msg(1,'poweron',tmp_msg)
                producer.send('vcenter-event',value=msg)        
            else:
                logging.warning(line)         
        return
    except Exception as err:
        logging.error(err)
        logging.info(line)
    return

def handle_dml(dml_result,producer):
    try:
        dml_keys = ['id','vm_id','vm_name','ip_addr','event_type','hd_type','old_value','new_value','@timestamp','desc','area']
        for line in dml_result:
            #if line[5] == 'disk_space':
            #    line[6] = round(line[6] / 1024.0, 2)
            #    line[7] = round(line[7] / 1024.0, 2)
            #print line
            msg = dict(zip(dml_keys,line))
            msg['@timestamp'] = msg['@timestamp'].strftime('%Y-%m-%dT%H:%M:%S')
            msg = json.dumps(msg)
            producer.send('vcenter-event',value=msg)
        return
    except Exception as err:
        logging.error(err)
    
    
def format_msg(handle_type,event_type,tmp_msg):
    #  handle_type: 1 = handle_event, 2 = handle_dml
    #  dml_msg format: 
        #  id: **,
        #  vm_id: **,        
        #  vm_name: **,
        #  ip_addr: **, 
        #  event_type: **,(update,insert,delete)
        #  hd_type: **,
        #  old_value: **,
        #  new_value: **,
        #  event_time: **,
        #  desc : comment,
        #  area: **    
    #  event format: 
        #  desc : vm_name relocate from ** to **, vm_name reboot,
        #  vm_name: **,
        #  username : **, 
        #  event_time:**,
        #  chain_id:**,
        #  vm_id:**,
        #  event_type:**, (relocate,migrate,reboot,shutdown,poweron)
        #  area: **
    try:
        if handle_type == 1:        
            desc = ''
            entries = ('from_host','from_ds','to_host','to_ds')
            tmp_msg['event_type'] = event_type
            if event_type == 'relocate':
                desc = ('virtual machine %s %s from %s,%s to %s,%s' % (tmp_msg['vm_name'],tmp_msg['event_type'],tmp_msg['from_host'],tmp_msg['from_ds'],tmp_msg['to_host'],tmp_msg['to_ds']))                 
            elif event_type == 'migrate':
                if tmp_msg['from_host'] != tmp_msg['to_host']:
                    desc = ('virtual machine %s %s from %s to %s' % (tmp_msg['vm_name'],tmp_msg['event_type'],tmp_msg['from_host'],tmp_msg['to_host']))
                elif tmp_msg['from_ds'] != tmp_msg['to_ds']:
                    desc = ('virtual machine %s %s from %s to %s' % (tmp_msg['vm_name'],tmp_msg['event_type'],tmp_msg['from_ds'],tmp_msg['to_ds']))
            ######################################################################
            elif event_type == 'clone':
                desc = ('virtual machine %s from %s,%s to %s,%s' % (tmp_msg['event_type'],tmp_msg['vm_name'],tmp_msg['from_host'],tmp_msg['to_vm_name'],tmp_msg['to_host'])) 
            ######################################################################
            elif event_type == 'reboot' or event_type == 'shutdown' or event_type == 'poweron':
                desc = ('virtual machine %s %s' % (tmp_msg['vm_name'],tmp_msg['event_type']))
            tmp_msg['desc'] = desc
            tmp_msg['@timestamp'] = tmp_msg['@timestamp'].strftime('%Y-%m-%dT%H:%M:%S')
            #logging.info(tmp_msg)
            for key in entries:
                tmp_msg.pop(key,None)
            return (json.dumps(tmp_msg))
        else:
            logging.warning('mark func format_msg.')
            return
    except Exception as err:
        logging.error(err)

def conn_to_mssql(dsn_name,id,cid):
    try:
        conn_name = ('DSN=%s;UID=monitor;PWD=monitor' % dsn_name)
        conn = pyodbc.connect(conn_name)
        cursor1 = conn.cursor()
        sql_ip = """
        update e
        set e.ip_addr = s.ip_addr
        from t_vm_event e
        join t_log_vm_state s on e.vm_id = s.vm_id
        where e.ip_addr = '-1' or e.ip_addr != s.ip_addr
        """
        #######################
        sql_event = """
        select   CHAIN_ID,
                 SUBSTRING(EVENT_TYPE,11,50) EVENT_TYPE,
                 dateadd(HOUR, 8, CREATE_TIME) event_time,
                 case
                   when username is Null then 'None'
                   else username
                 end username,
                 VM_ID,
                 VM_NAME,
                 case
                   when host_name is null then 'None'
                   else host_name
                 end host_name,
                 case
                   when datastore_name is null then 'None'
                   else datastore_name
                 end datastore_name,
                 ? area
        from VPX_EVENT 
        where chain_id > ?
        and EVENT_TYPE in ('vim.event.VmBeingRelocatedEvent','vim.event.VmRelocatedEvent'
                           ,'vim.event.VmBeingHotMigratedEvent','vim.event.VmMigratedEvent'
                           ,'vim.event.VmGuestRebootEvent','vim.event.VmResettingEvent'
                           ,'vim.event.VmPoweredOffEvent','vim.event.VmGuestShutdownEvent'
                           ,'vim.event.DrsVmPoweredOnEvent','vim.event.VmPoweredOnEvent'
                           ,'vim.event.VmBeingClonedEvent','vim.event.VmClonedEvent'
                           )
        order by event_id
        """
        ########################
        sql_dml = """
         select   id
         ,e.vm_id
         ,e.vm_name
         ,e.ip_addr
         ,case e.op_type 
            when 1 then 'update'
            when 2 then 'insert'
            when 3 then 'delete'
          end event_type
         ,e.hd_type
         ,case
            when e.old_value is Null then 0
            when e.hd_type = 'disk_space' and exists(select 1 
                                                     from (select c.vm_id,c.update_key
                                                           from T_VM_EVENT c,
                                                           (select d.lun_uuid,max(d.vm_id) vm_id
                                                             from T_VM_EVENT d
                                                             where d.lun_uuid is not null
                                                             group by d.lun_uuid having count(*) >1) b
                                                           where c.vm_id = b.vm_id 
                                                           and c.lun_uuid = b.lun_uuid 
                                                           ) w
                                                     where w.vm_id = e.vm_id and w.update_key = e.update_key
                                                     ) then 0
            when e.hd_type = 'disk_space' then old_value/1024/1024
            when e.hd_type = 'mem' then old_value/1024
            else e.old_value
          end old_value
         ,case
            when e.new_value is Null then 0
            when e.hd_type = 'disk_space' and exists(select 1 
                                                     from (select c.vm_id,c.update_key
                                                           from T_VM_EVENT c,
                                                           (select d.lun_uuid,max(d.vm_id) vm_id
                                                             from T_VM_EVENT d
                                                             where d.lun_uuid is not null
                                                             group by d.lun_uuid having count(*) >1) b
                                                           where c.vm_id = b.vm_id 
                                                           and c.lun_uuid = b.lun_uuid 
                                                           ) w
                                                     where w.vm_id = e.vm_id and w.update_key = e.update_key
                                                     ) then 0
            when e.hd_type = 'disk_space' then new_value/1024/1024
            when e.hd_type = 'mem' then new_value/1024
            else e.new_value
          end as new_value
         ,dateadd(HOUR, 8, e.event_time) event_time
         ,case
            when comment is Null then 'None'
            else comment
          end comment                
         ,? area
         from t_vm_event e
         where e.id > ?
         order by e.id
        """ 
        cursor1.execute(sql_ip)       
        cursor1.execute(sql_event,dsn_name,cid)
        event_result = cursor1.fetchall()
        cursor1.execute(sql_dml,dsn_name,id)
        dml_result = cursor1.fetchall()
        cursor1.close()
        conn.close()
        return event_result,dml_result
    except Exception as err:
        logging.error(err)
    
def conn_to_pg(dsn_name,id,cid):
    try:
        conn_name = ('host = %s, database = VCDB, user = monitor, password = monitor' % dsn_name)
        conn = pyodbc.connect(conn_name)
        cursor1 = conn.cursor()
        sql_ip = """
        update vc."t_vm_event" e
        set ip_addr = s.ip_addr
        from vc."t_log_vm_state" s
        where e.vm_id = s.vm_id
        and e.ip_addr = '-1' or e.ip_addr != s.ip_addr
        """
        #######################
        sql_event = """
        select   CHAIN_ID,
                 SUBSTRING(EVENT_TYPE,11,50) EVENT_TYPE,
                 CREATE_TIME + interval '8 hour' event_time,
                 case
                   when username is Null then 'None'
                   else username
                 end username,
                 VM_ID,
                 VM_NAME,
                 case
                   when host_name is null then 'None'
                   else host_name
                 end host_name,
                 case
                   when datastore_name is null then 'None'
                   else datastore_name
                 end datastore_name,
                 %s area
        from VPX_EVENT 
        where chain_id > %s
        and EVENT_TYPE in ('vim.event.VmBeingRelocatedEvent','vim.event.VmRelocatedEvent'
                           ,'vim.event.VmBeingHotMigratedEvent','vim.event.VmMigratedEvent'
                           ,'vim.event.VmGuestRebootEvent','vim.event.VmResettingEvent'
                           ,'vim.event.VmPoweredOffEvent','vim.event.VmGuestShutdownEvent'
                           ,'vim.event.DrsVmPoweredOnEvent','vim.event.VmPoweredOnEvent'
                           ,'vim.event.VmBeingClonedEvent','vim.event.VmClonedEvent'
                           )
        order by event_id
        """
        ########################
		sql_dml = """
        select   id
         ,e.vm_id
         ,e.vm_name
         ,e.ip_addr
         ,case e.op_type 
            when 1 then 'update'
            when 2 then 'insert'
            when 3 then 'delete'
          end event_type
         ,e.hd_type
         ,case
            when e.old_value is Null then 0
            when e.hd_type = 'disk_space' and exists(select 1 
                                                     from (select c.vm_id,c.update_key
                                                           from T_VM_EVENT c,
                                                           (select d.lun_uuid,max(d.vm_id) vm_id
                                                             from T_VM_EVENT d
                                                             where d.lun_uuid is not null
                                                             group by d.lun_uuid having count(*) >1) b
                                                           where c.vm_id = b.vm_id 
                                                           and c.lun_uuid = b.lun_uuid 
                                                           ) w
                                                     where w.vm_id = e.vm_id and w.update_key = e.update_key
                                                     ) then 0
            when e.hd_type = 'disk_space' then old_value/1024/1024
            when e.hd_type = 'mem' then old_value/1024
            else e.old_value
          end old_value
         ,case
            when e.new_value is Null then 0
            when e.hd_type = 'disk_space' and exists(select 1 
                                                     from (select c.vm_id,c.update_key
                                                           from T_VM_EVENT c,
                                                           (select d.lun_uuid,max(d.vm_id) vm_id
                                                             from T_VM_EVENT d
                                                             where d.lun_uuid is not null
                                                             group by d.lun_uuid having count(*) >1) b
                                                           where c.vm_id = b.vm_id 
                                                           and c.lun_uuid = b.lun_uuid 
                                                           ) w
                                                     where w.vm_id = e.vm_id and w.update_key = e.update_key
                                                     ) then 0
            when e.hd_type = 'disk_space' then new_value/1024/1024
            when e.hd_type = 'mem' then new_value/1024
            else e.new_value
          end as new_value
         ,e.event_time + interval '8 hour' event_time
         ,case
            when comment is Null then 'None'
            else comment
          end as comment               
         ,%s area
         from t_vm_event e
         where e.id > %s
         order by e.id
        """ 
        cursor1.execute(sql_ip)       
        cursor1.execute(sql_event, [dsn_name, cid])
        event_result = cursor1.fetchall()
        cursor1.execute(sql_dml, [dsn_name, id])
        dml_result = cursor1.fetchall()
        cursor1.close()
        conn.close()
        return event_result,dml_result
    except Exception as err:
        logging.error(err)
    
if __name__ == '__main__':
    print ('mark test')
    start_time = datetime.strftime(datetime.now() - timedelta(hours=390), "%Y-%m-%d %H:00")
    end_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:00")
    #  connect to kafka
    producer = KafkaProducer(bootstrap_servers = ["162.30.10.211","162.30.10.212","162.30.10.213","162.30.10.214","162.30.10.215"], linger_ms = 10)
    #area_list = ['HXQ']
    win_area_list = ['HXQ', 'DMZ', 'LAB']
	vcsa_area_list = ['QZQ']
    record_file = '/pyworkspace/vcenter_event/record.txt'
    if os.path.isfile(record_file):
        with open(record_file, 'r') as f:
            id_record = json.load(f)
    else:
       id_record = {}
       for area in area_list:
         id_record[area] = {"id": 0, "cid": 0}
    #  get event result from mssql
    for dsn_name in win_area_list:
        event_result, dml_result = conn_to_mssql(dsn_name,id_record[dsn_name]['id'],id_record[dsn_name]['cid'])
        if len(event_result) > 0:
            handle_event(event_result,producer)
            event_cid = [e[0] for e in event_result]
            id_record[dsn_name]['cid'] = max(event_cid)        
        if len(dml_result) > 0:
            handle_dml(dml_result,producer)
            dml_id = [e[0] for e in dml_result]
            id_record[dsn_name]['id'] = max(dml_id)
	for dsn_name in vcsa_area_list:
        event_result, dml_result = conn_to_pg(dsn_name,id_record[dsn_name]['id'],id_record[dsn_name]['cid'])
        if len(event_result) > 0:
            handle_event(event_result,producer)
            event_cid = [e[0] for e in event_result]
            id_record[dsn_name]['cid'] = max(event_cid)        
        if len(dml_result) > 0:
            handle_dml(dml_result,producer)
            dml_id = [e[0] for e in dml_result]
            id_record[dsn_name]['id'] = max(dml_id)
    with open('record.txt', 'w') as f:
       f.write(json.dumps(id_record))
    print ('end')
    producer.close()
