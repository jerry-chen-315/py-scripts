#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
## description   :check oracle tablepsace usage
## author        :chenhao 
## created       :2015-12-8
##
## last modified :2015-12-16 add monitor session wait
##                2015-12-14 add monitor asm diskgroup
##                2015-12-11 add monitor archive 

import cx_Oracle
import sys
import os
import decimal

#v_tnsname=sys.argv[1]
#v_user=sys.argv[2]
#v_pass=sys.argv[3]
#v_warning=sys.argv[4]
#v_critical=sys.argv[5]
#v_mode=sys.argv[6]

os.environ["ORACLE_HOME"] = "/oracle/app/oracle/product/12.2.0/client_1"

# ***************************
# function: get tablespace usage
def func_tbs_usage(v_tnsname,v_user,v_pass,v_warning,v_critical):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_tbs="""
         select f.tablespace_name,
         round(d.total_size)  as totalsize,
         round((d.total_size - f.free_size) / d.total_size,4)*100 util,
         round(f.free_size,2)  as freesize
         from
          (select tablespace_name,sum(bytes) / (1024 * 1024) free_size
           FROM DBA_FREE_SPACE
           GROUP BY TABLESPACE_NAME) F,
          (SELECT DD.TABLESPACE_NAME,
           SUM(DD.BYTES) / (1024 * 1024) TOTAL_SIZE
           FROM SYS.DBA_DATA_FILES DD
           GROUP BY DD.TABLESPACE_NAME) D
         where d.tablespace_name=f.tablespace_name 
         and d.tablespace_name not like 'UNDO%'
         and round((d.total_size - f.free_size) / d.total_size,4)*100 > :warning
         order by util desc
         """
        cursor1.execute(sql_tbs,warning=float(v_warning))
        l_info =cursor1.fetchall()
        cursor1.close
        db.close
        ## check tbs usage whether warning or critical
        s_result=''
        i_w_num=0
        i_c_num=0
        if len(l_info) > 0:
            for t_i in l_info:
                s_result = s_result+t_i[0]+' usage is '+("%.2f" % t_i[2])+'%;size '+str(t_i[1])+'MB, '
                if t_i[2] > float(v_warning):
                    i_w_num+=1
                if t_i[2] > float(v_critical):
                    i_c_num+=1
            if i_c_num > 0:
                print ('CRITICAL:'+s_result)
                return 2
            elif i_w_num >0 :
                print ('WARNING:'+s_result)
                return 1
        else:
            print ('OK: Tablespace usage is OK')
            return 0
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2            		
# ***************************

def func_tbs_size(v_tnsname,v_user,v_pass,v_minsize):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_tbs="""
          select f.tablespace_name,
                 (d.total_size - f.free_size) used_size
          from
           (SELECT tablespace_name,round(sum(bytes) / (1024 * 1024 * 1024)) free_size
            FROM DBA_FREE_SPACE
            GROUP BY TABLESPACE_NAME) F,
           (SELECT DD.TABLESPACE_NAME,
            ROUND(SUM(DD.BYTES) / (1024 * 1024 * 1024)) TOTAL_SIZE
            FROM SYS.DBA_DATA_FILES DD
            GROUP BY DD.TABLESPACE_NAME) D
            where d.tablespace_name=f.tablespace_name 
            and d.TOTAL_SIZE - F.FREE_SIZE >= :minsize
            order by 2 desc
         """
        cursor1.execute(sql_tbs,minsize=int(v_minsize))
        l_info =cursor1.fetchall()
        cursor1.close
        db.close
        perf=''
        if len(l_info) > 0:
            for line in l_info:
                perf=('%s=%d %s' % (line[0],line[1],perf))
            print ('OK: running ok |'+perf)
            return 0
        else:
            print ('no tablespace size greater than %d GB' % 'int(v_minsize)')
            return 1
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2


# ***************************	
# function:get archive dest usage
#def func_arch_usage(v_tnsname,v_user,v_pass,v_warning,v_critical):
#    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
#    cursor1=db.cursor()
#	# check archivelog destination is recovery_dest or ASM_DISKGROUP
#    sql_arch_dest="""
#     select UPPER(ltrim(DESTINATION,'+'))
#     from v$archive_dest
#     where STATUS='VALID'
#    """
#	
#    sql_arch_usage="""
#    select t.NAME,t.TOTAL_MB,t.FREE_MB,round((t.TOTAL_MB-t.FREE_MB)/t.total_mb,4)*100 util
#    from sys.v_$asm_diskgroup t
#    where t.name=:D
#    """
#    cursor1.execute(sql_arch_dest)
#    
#    l_arch_name=cursor1.fetchone()
#    if l_arch_name[0] != 'USE_DB_RECOVERY_FILE_DEST':
#       # l_name=list(l_arch_name[1:])
#        cursor1.execute(sql_arch_usage,l_arch_name)
#        l_info=cursor1.fetchall()
#        t_info=l_info[0]
#    else:
#       #get RECOVERY_DEST's asm_diskgroup name
#        l_recov_name=cursor1.execute("select upper(substr(name,2)) from v$recovery_file_dest t").fetchone()
#        cursor1.execute(sql_arch_usage,l_recov_name)
#        l_info=cursor1.fetchall()	
#        t_info=l_info[0]
#    cursor1.close
#    db.close
#    s_result='Archive dest name: "'+t_info[0]+'" ,usage:'+('%.2f' % t_info[3])+'% |name='+t_info[0]+' total='+str(t_info[1])+' free='+str(t_info[2])
#    if t_info[3] > float(v_critical):
#	    print ('CRITICAL: '+s_result)
#	    return 2
#    if t_info[3] > float(v_warning):
#	    print ('WARNING: '+s_result)
#	    return 1
#    else:
#	    print ('OK: '+s_result)
#	    return 0
# ***************************

# ***************************
# function:get asm diskgroup usage
def func_asm_usage(v_tnsname,v_user,v_pass,v_warning,v_critical):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_asm_usage="""
        select t.NAME,floor(t.TOTAL_MB/1024) total_gb,t.FREE_MB,round((t.TOTAL_MB-t.FREE_MB)/t.total_mb,4)*100 util,floor((t.TOTAL_MB-t.FREE_MB)/1024) USED_GB
        from sys.v_$asm_diskgroup t
        """
        cursor1.execute(sql_asm_usage)
        l_asm_info=cursor1.fetchall()
        cursor1.close
        db.close
        s_result=''
        s_chart=''
        s_text=''
        i_w_num=0
        i_c_num=0
        for t_info in l_asm_info:
            s_text=s_text+'ASM diskgroup: "'+t_info[0]+'" ,usage:'+('%.0f' % t_info[3])+'%, '
            s_chart=s_chart+("inst%s=%.2f;80;90 %s(GB)=%d TOTAL_%s=%d " %  (t_info[0],t_info[3],t_info[0],t_info[4],t_info[0],t_info[1]))
#        s_chart=s_chart+("t_info[0]+'='+('%.2f' % t_info[3])+'%;80;90; ')
            if t_info[3] > float(v_critical):
                i_c_num+=1
            if t_info[3] > float(v_warning):
                i_w_num+=1
        s_result=s_text+'|'+s_chart
        if i_c_num >0:
            print ('CRITICAL: '+s_result)
            return 2
        if i_w_num >0:
            print ('WARNING: '+s_result)
            return 1
        else:
            print ('OK: '+s_result)
            return 0
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2
# ***************************

# ***************************
# function get session wait
def func_sess_wait1(v_tnsname,v_user,v_pass,v_warning,v_critical):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_sess_wait="""
        select s.inst_id, s.WAIT_CLASS,count(*)
        from  gv$session s
        where s.WAIT_CLASS !='Idle'
        and s.STATUS='ACTIVE'
        group by s.inst_id,s.wait_class
        """
        cursor1.execute(sql_sess_wait)
        l_wait_info=cursor1.fetchall()
        cursor1.close()
        db.close()
        s_result1=' inst_id=1 '
        s_result2=' inst_id=2 '
        i_w_num=0
        i_c_num=0
        for t_info in l_wait_info:
            if t_info[0] == 1:
                s_result1=s_result1+"'"+t_info[1]+"' = "+str(t_info[2])+' ; '
            else:
                s_result2=s_result2+"'"+t_info[1]+"' = "+str(t_info[2])+' ; '
            if t_info[2]>int(v_critical):
                i_c_num+=1
            elif t_info[2]>int(v_warning):
                i_w_num+=1
        s_result=s_result1+'\n'+s_result2
        if i_c_num >0:
            print ('CRITICAL - Wait Class:'+s_result)
            return 2
        if i_w_num >0:
            print ('WARNING - Wait Class:'+s_result)
            return 1
        else:
            print ('OK - Wait Class:'+s_result)
            return 0
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2
##################################################
        
def func_sess_wait(v_tnsname,v_user,v_pass,v_warning,v_critical):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_sess_wait="""
        select decode(grouping(s.event#),1,'Total',s.EVENT#) event, count(*) event_num
        from  gv$session s
        where s.WAIT_CLASS !='Idle'
        and s.STATUS='ACTIVE'
        group by rollup(s.event#)
        """
        cursor1.execute(sql_sess_wait)
        l_wait_info=cursor1.fetchall()
        cursor1.close()
        db.close()
        perf=''
        flag=0
        w_flag=0
        c_flag=0
        event_num=0
        rowlock_flag=0
        rowlock_num=0
        if len(l_wait_info) > 0:
            for t_info in l_wait_info:
                if t_info[0] == 'Total':
                   if t_info[1] > int(v_critical):
                       c_flag = 4
                       event_num = t_info[1]
                       continue
                   elif t_info[1] > int(v_warning):
                       w_flag = 2
                       event_num = t_info[1]
                       continue
                perf=('%s=%d %s' % (t_info[0],t_info[1],perf) )
                # id 240 = enq: TX - row lock contention
                if t_info[0] == '240':
                    rowlock_flag = 1
                    rowlock_num = t_info[1]
        flag = c_flag + w_flag + rowlock_flag
        if flag == 5:
            print ('CRITICAL - %d session waits and %d row lock,please check.|%s' % (event_num,rowlock_num,perf))
            return 2
        elif flag == 4:
            print ('CRITICAL - %d session waits,please check.|%s' % (event_num,perf))
            return 2
        elif flag == 3:
            print ('WARNING - %d session waits and %d row lock,please check.|%s' % (event_num,rowlock_num,perf))
            return 1
        elif flag == 2:
            print ('WARNING - %d session waits,please check.|%s' % (event_num,perf))
        elif flag == 1:
            print ('WARNING - %d row lock,please check.|%s' % (rowlock_num,perf))
            return 1
        else:
            print ('OK - Session status is normal |%s' % perf)
            return 0
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2
    
# ***************************
# function get session number
def func_sess_num(v_tnsname,v_user,v_pass,v_warning,v_critical):
    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
    cursor1=db.cursor()
    sqlSessNum="""
    select inst_id,count(*) from gv$session group by inst_id
    """
    sqlSessParameter="select value from v$parameter where name='sessions'"
    cursor1.execute(sqlSessParameter)
    numMax=cursor1.fetchone()
    numMax=int(numMax[0])
    cursor1.execute(sqlSessNum)
    numCurrent=cursor1.fetchall()
    cursor1.close()
    db.close()
    c_flag=0
    w_flag=0
    perf=''
    output=''
    for sess_num in numCurrent:
       perf=('inst_%d=%d %s' % (sess_num[0],sess_num[1],perf))
       if (sess_num[1]/numMax)*100 > int(v_critical):
          c_flag=1
          output=('inst_%d session number:%d, %s' % (sess_num[0],sess_num[1],output))
       elif (sess_num[1]/numMax)*100 > int(v_warning):
          w_flag=1
          output=('inst_%d session number:%d, %s' % (sess_num[0],sess_num[1],output))
    if c_flag > 0:
       print ('CRITICAL - %s |%s' % (output,perf))
       return 2
    elif w_flag > 0:
       print ('WARNING - %s |%s' % (output,perf))
       return 1
    else:
       print ('OK - db session number is ok |%s' % perf)
       return 0

# ***************************
# function get transaction of long ops
def func_trans_longops(v_tnsname,v_user,v_pass):
    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
    cursor1=db.cursor()
    sqlTransaction="""
    select s.inst_id,
       s.sid,
       s.SERIAL#,
       s.USERNAME,
       s.SQL_ID,
       s.status,
       t.XIDUSN,
       t.START_date,
       (sysdate-t.start_date)*24*3600,
       t.USED_UBLK*(select value from v$parameter where name='db_block_size')/1024/1024 used_size
    from gv$transaction t,gv$session s
    where t.addr=s.TADDR
    and t.inst_id=s.inst_id
    and round(sysdate-t.start_date,2)>0.1
    """
    cursor1.execute(sqlTransaction)
    listTrans=cursor1.fetchall()
    if  len(listTrans) > 0:
        strInfo=''
        for tTrans in listTrans:
            strInfo=strInfo+('inst_id=%d, sid=%d, serial#=%d, status=%s, duration=%d(s);' % (tTrans[0],tTrans[
1],tTrans[2],tTrans[5],tTrans[8]))

        print ('WARNING - Longops transaction:'+strInfo)
        return 1
    else:
        print ('OK - Longops transaction: None')
        return 0

def num_of_transaction(v_tnsname,v_user,v_pass):
    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
    cursor1=db.cursor()
    sqltext="""
    select decode(grouping(instance_number),1,'total',instance_number) instance
           ,sum(transactions) transactions 
    from 
    (select st.instance_number instance_number,
     decode(max(st.value)-min(st.value),0,max(st.value), max(st.value)-min(st.value)) transactions
     from dba_hist_sysstat st,dba_hist_snapshot sn
     where st.snap_id=sn.snap_id
     and st.instance_number=sn.instance_number
     and st.stat_name like 'user commits'
     and sn.end_interval_time >= trunc(sysdate-1)+1/24 and sn.end_interval_time < trunc(sysdate)+1/24
     group by st.instance_number,to_char(sn.startup_time,'yyyy-mm-dd hh24:mi')
    )
    group by rollup(instance_number)
    """
    cursor1.execute(sqltext)
    listTrans=cursor1.fetchall()
    perf=''
    cursor1.close()
    db.close()
    if len(listTrans) > 0:
        for t_row in listTrans:
            perf=('%s=%s %s' % (t_row[0],t_row[1],perf))
        print ('OK - gahter transaction number %s|%s' % (t_row[1],perf))
        return 0
    else:
        print ("WARNING - transaction query is failed")
        return 1

def session_longops(v_tnsname,v_user,v_pass):
    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
    cursor1=db.cursor()
    sqltext="""
    select decode(grouping(inst_id),1,'total',inst_id) inst_id,
    sum(longops_6_10) lops_6_10,
    sum(longops_11_30) lops_11_30,
    sum(longops_31_60) lops_31_60,
    sum(longops_61_600) lops_61_600,
    sum(longops_601_1200) lops_601_1200,
    sum(longops_gt_1200) lops_gt_1200
    from
    (select inst_id,
       sum(case when t.ELAPSED_SECONDS between 6 and 10
             then 1
           else 0
           end) longops_6_10,
       sum(case when t.ELAPSED_SECONDS between 11 and 30
             then 1
           else 0
           end) longops_11_30,
       sum(case when t.ELAPSED_SECONDS between 31 and 60
             then 1
           else 0
           end) longops_31_60,
       sum(case when t.ELAPSED_SECONDS between 61 and 600
             then 1
           else 0
           end) longops_61_600,
       sum(case when t.ELAPSED_SECONDS between 601 and 1200
             then 1
           else 0
           end) longops_601_1200,
       sum(case when t.ELAPSED_SECONDS > 1200
             then 1
           else 0
           end) longops_gt_1200
     from gv$session_longops t
     where opname not like 'RMAN%' and opname not like 'Gather%' and opname not like 'Advisor%'
     and t.START_TIME > (sysdate-1/24)
     group by inst_id
    )
    group by rollup(inst_id)
    """
    cursor1.execute(sqltext)
    listResult=cursor1.fetchall()
    cursor1.close()
    db.close()
    if len(listResult) > 0:
        t_row=listResult[-1]
        perf=('lops_6_10=%d lops_11_30=%d lops_31_60=%d lops_61_600=%d lops_601_1200=%d lops_gt_1200=%d' % t_row[1:])
        if int(t_row[-1]) > 0:
            print ('WARNING - some session elapsed_time greater than 1200s|%s' % perf)
            return 1
        else:
            print ('OK - session elapsed_time is normal |%s' % perf)
            return 0
    else:
        print ('WARNING - no data found')
        return 0

def undostat(v_tnsname,v_user,v_pass):
    db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
    cursor1=db.cursor()
    sqltext="""
    select round(undoblks*100/(select sum(a.blocks) from dba_data_files a where a.tablespace_name = (select value from v$parameter where name ='undo_tablespace')),2) blkusage
          ,SSOLDERRCNT
          ,NOSPACEERRCNT
    from (select  max(u.UNDOBLKS) undoblks
                 ,max(u.SSOLDERRCNT) SSOLDERRCNT
                 ,max(u.NOSPACEERRCNT) NOSPACEERRCNT
          from v$undostat u
          where u.begin_time > (sysdate-1/24)
         )
    """
    cursor1.execute(sqltext)
    listResult=cursor1.fetchall()
    cursor1.close()
    db.close()
    if len(listResult) > 0:
        t_row=listResult[-1]
        print (t_row)
        perf=('blkusage=%.2f ssolderrcnt=%d nospaceerrcnt=%d' % t_row)
        if t_row[1] > 0 and t_row[2] > 0:
            print ('WARNING - ssold err:%d and nospace err:%d|%s' % (t_row[1:],perf))
            return 1
        elif t_row[1] > 0:
            print ('WARNING - ssold err:%d |%s' % (t_row[1],perf))
            return 1
        elif t_row[2] > 0:
            print ('WARNING - nospace err:%d |%s' % (t_row[2],perf))
            return 1
        elif t_row[0] > 80:
            print ('WARNING - high blkusage:%.2f |%s' % (t_row[0],perf))
            return 1
        else:
            print ('OK - undo state is normal |%s' % perf)
            return 0
    else:
        print ('WARNING - no data found')
        return 1

def archstat(v_tnsname,v_user,v_pass,v_count_warning,v_size_warning):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select count(*) cnt,nvl(round(sum(t.BLOCKS)*512/1024/1024/1024,2),0) total_size
      from v$archived_log t
      where t.FIRST_TIME between trunc(sysdate-1) and  trunc(sysdate)
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      #print (listResult)
      if len(listResult) > 0:
         perf=('number=%d size_GB=%.2f' % listResult)
         if listResult[0] > int(v_count_warning) or listResult[1] > int(v_size_warning):
            print ('WARNING - archivelog stats is abnormal|%s' % perf)
            return 1
         else:
            print ('OK - archivelog stats is normal|%s' % perf)
            return 0
      else:
          print ('WARNING - no data found')
          return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2


def func_archusage(v_tnsname,v_user,v_pass,v_warning,v_critical):
    try:
        db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
        cursor1=db.cursor()
        sql_arch_usage="""
        select sum(PERCENT_SPACE_USED) percent_usage from v$recovery_area_usage
        """
        cursor1.execute(sql_arch_usage)
        arch_info=cursor1.fetchone()
        cursor1.close()
        db.close()
        i_w_num=0
        i_c_num=0
        perf=('arch_usage=%.2f' % (arch_info[0]) )
        if arch_info[0]>int(v_critical):
            i_c_num+=1
        elif arch_info[0]>int(v_warning):
            i_w_num+=1
        if i_c_num >0:
            #print ('CRITICAL - recovery area usage=%.2f%s|%s' % (arch_info[0],'%',perf))
            print ('CRITICAL - recovery area usage %.2f|%s' % (arch_info[0],perf))
            return 2
        elif i_w_num >0:
            print ('WARNING - recovery area usage %.2f|%s' % (arch_info[0],perf))
            return 1
        else:
            print ('OK - recovery area usage %.2f|%s' % (arch_info[0],perf))
            return 0
    except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2

def user_stat(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select  decode(length(t.new_user),1,0,1) + decode(length(t.deleted_user),1,0,2)
              + decode(length(t.status_changed),1,0,4) + decode(length(t.near_expiry_date),1,0,8) err_code,
              NEW_USER,
              DELETED_USER,
              STATUS_CHANGED,
              NEAR_EXPIRY_DATE
      from t_hist_user_state t
      where t.recode_date > (sysdate - 4/24)
      order by recode_date desc
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if listResult is None:
         print ('WARNING - no data found')
         return 1
      else:
         output=('%s ; %s ; %s ; %s' % (listResult[1],listResult[2],listResult[3],listResult[4] ))
         if listResult[0] == 15:
            print ('WARNING - account status changed(%s),err_code=NDCE' % (output))
            return 1
         elif listResult[0] == 14:
            print ('WARNING - account status changed(%s),err_code=DCE' % (output))
            return 1
         elif listResult[0] == 13:
            print ('WARNING - account status changed(%s),err_code=NCE' % (output))
            return 1
         elif listResult[0] == 12:
            print ('WARNING - account status changed(%s),err_code=CE' % (output))
            return 1
         elif listResult[0] == 11:
            print ('WARNING - account status changed(%s),err_code=NDE' % (output))
            return 1
         elif listResult[0] == 10:
            print ('WARNING - account status changed(%s),err_code=DE' % (output))
            return 1
         elif listResult[0] == 9:
            print ('WARNING - account status changed(%s),err_code=NE' % (output))
            return 1
         elif listResult[0] == 8:
            print ('WARNING - account status changed(%s),err_code=E' % (output))
            return 1
         elif listResult[0] == 7:
            print ('WARNING - account status changed(%s),err_code=NDC' % (output))
            return 1
         elif listResult[0] == 6:
            print ('WARNING - account status changed(%s),err_code=DC' % (output))
            return 1
         elif listResult[0] == 5:
            print ('WARNING - account status changed(%s),err_code=NC' % (output))
            return 1
         elif listResult[0] == 4:
            print ('WARNING - account status changed(%s),err_code=C' % (output))
            return 1
         elif listResult[0] == 3:
            print ('WARNING - account status changed(%s),err_code=ND' % (output))
            return 1
         elif listResult[0] == 2:
            print ('WARNING - account status changed(%s),err_code=D' % (output))
            return 1
         elif listResult[0] == 1:
            print ('WARNING - account status changed(%s),err_code=N' % (output))
            return 1
         elif listResult[0] == 0:
            print ('OK - account status OK')
            return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def memory_hit(v_tnsname,v_user,v_pass,v_warning,v_critical):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
       SELECT inst_id,
         mem memory,
         hit_ratio
       FROM
         (
          SELECT inst_id,
            'Buffer Hit' mem,
            ROUND(((1-(SUM(DECODE(name,'physical reads', value,0))/(SUM(DECODE(name, 'db block gets', value,0))+(SUM(DECODE(name,'consistent gets', value, 0))))))*100),2) hit_ratio
          FROM gv$sysstat
          GROUP BY inst_id
          UNION
          SELECT inst_id,
            'Library Hit' mem,
            TRUNC((1-(SUM(reloads)/SUM(pins)))*100,2) hit_ratio
          FROM gv$librarycache
          GROUP BY inst_id
          UNION
          SELECT inst_id,
            'Dictionary Hit' mem,
            TRUNC((1-(SUM(getmisses)/SUM(gets)))*100,2) hit_ratio
          FROM gv$rowcache
          GROUP BY inst_id
          UNION
          SELECT inst_id,
            'PGA Hit' mem,
            value hit_ratio
          FROM gv$pgastat
          WHERE NAME = 'cache hit percentage'
          GROUP BY inst_id,
            value
          UNION
          SELECT inst_id,
             'Latch hit' mem,
          TRUNC((1 - SUM(misses)/SUM(gets))*100,2) hit_ratio
          FROM gv$latch
          GROUP BY inst_id
         )
       WHERE hit_ratio > 0
       ORDER BY 1,2
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchall()
      cursor1.close()
      db.close()
      critical_flag=0
      warning_flag=0
      output=''
      perf=''
      for line in listResult:
         perf=('inst%d_inst%s=%.2f %s' % (line[0],line[1].replace(' ','_'),line[2],perf))
         if line[2] < int(v_critical):
            critical_flag=2
            output=('inst%d_%s is %.2f, %s' % (line[0],line[1],line[2],output))
         elif line[2] < int(v_warning):
            warning_flag=1
            output=('inst%d_%s is %.2f, %s' % (line[0],line[1],line[2],output))
         else:
            flag=0
      if critical_flag == 2:
          print ('CRITICAL - %s |%s' % (output,perf))
          return 0
      elif warning_flag == 1:
          print ('WARNING - %s |%s' % (output,perf))
          return 0
      else:
          print ('OK - Memory Hit Ratio OK |%s' % (perf))
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

# function get process number
def process_num(v_tnsname,v_user,v_pass,v_warning,v_critical):
   try:
       db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
       cursor1=db.cursor()
       sql_process="""
       select inst_id,count(*)
       from gv$process
       group by inst_id
       """
       sql_parameter="select value from v$parameter where name='processes'"
       cursor1.execute(sql_parameter)
       numMax=cursor1.fetchone()
       numMax=int(numMax[0])
       cursor1.execute(sql_process)
       numCurrent=cursor1.fetchall()
       cursor1.close()
       db.close()
       c_flag=0
       w_flag=0
       perf=''
       output=''
       for process_num in numCurrent:
          perf=('inst_%d=%d %s' % (process_num[0],process_num[1],perf))
          if (process_num[1]/numMax)*100 > int(v_critical):
             c_flag=1
             output=('inst_%d process number:%d, %s' % (process_num[0],process_num[1],output))
          elif (process_num[1]/numMax)*100 > int(v_warning):
             w_flag=1
             output=('inst_%d process number:%d, %s' % (process_num[0],process_num[1],output))
       if c_flag > 0 :
          print ('CRITICAL - %s |%s' % (output,perf))
          return 2
       elif w_flag > 0:
          print ('WARNING - %s |%s' % (output,perf))
          return 1
       else:
          print ('OK - db process number is ok |%s' % perf)
          return 0
   except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2

# function get db time
def db_time(v_tnsname,v_user,v_pass,v_cpus):
   try:
       db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
       cursor1=db.cursor()
       sql_dbtime="""
       select t.instance_number,
       case
         when t.db_time_min is null then
          0
         when t.db_time_min <= 0 then
          0
         else
          t.db_time_min
       end as db_time
       from (SELECT A.INSTANCE_NUMBER,
               LAG(A.SNAP_ID) OVER(ORDER BY a.instance_number, A.SNAP_ID) BEGIN_SNAP_ID,
               A.SNAP_ID END_SNAP_ID,
               b.begin_interval_time,
               b.end_interval_time,
               ROUND((A.VALUE - LAG(A.VALUE)
                      OVER(ORDER BY A.instance_number, A.SNAP_ID)) / 1000000 / 60,
                     2) DB_TIME_MIN
          FROM DBA_HIST_SYS_TIME_MODEL A, DBA_HIST_SNAPSHOT B
         WHERE A.SNAP_ID = B.SNAP_ID
           AND A.INSTANCE_NUMBER = B.INSTANCE_NUMBER
           AND A.STAT_NAME = 'DB time'
           and b.begin_interval_time >= trunc(sysdate - 2/24, 'hh')) T
       where t.end_interval_time > trunc(sysdate, 'hh')
       """
       cursor1.execute(sql_dbtime)
       sql_result=cursor1.fetchall()
       cursor1.close()
       db.close()
       w_flag=0
       perf=''
       output=''
       for db_time in sql_result:
          perf=('inst_%d=%.2f %s' % (db_time[0],db_time[1],perf))
          if (db_time[1]/int(v_cpus)) > 60:
             w_flag=1
             output=('inst_%d db time:%.2f, %s' % (db_time[0],db_time[1],output))
       if w_flag == 1:
          print ('WARNING - %s |%s' % (output,perf))
          return 1
       else:
          print ('OK - db time is ok |%s' % perf)
          return 0
   except Exception as err:
        print ('CRITICAL - %s' % err)
        return 2


def dg_arch_gap(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select count(*) from v$archive_gap
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if listResult[0] > 0:
         #perf=('number=%d size_GB=%.2f' % listResult)
         print ('CRITICAL - find out archive log gap|gap=%d' % listResult)
         return 2
      else:
         print ('OK - no archive log gap|gap=%d' % listResult)
         return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def dg_apply_latency(v_tnsname,v_user,v_pass,v_warning,v_critical):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      SELECT DEST_ID,
       CURRENT_SCN,
       APPLIED_SCN,
       round((to_date(to_char(SCN_TO_TIMESTAMP(CURRENT_SCN),
                             'yyyy-mm-dd hh24:mi:ss'),
                     'yyyy-mm-dd hh24:mi:ss') -
             to_date(to_char(SCN_TO_TIMESTAMP(APPLIED_SCN),
                             'yyyy-mm-dd hh24:mi:ss'),
                     'yyyy-mm-dd hh24:mi:ss'))*24*60*60) second_time,
       ARCHIVER
      FROM V$ARCHIVE_DEST, V$DATABASE
      WHERE TARGET = 'STANDBY'
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if len(listResult) > 0:
         perf=('time_latency=%d' % listResult[3])
         if listResult[3] > int(v_critical):
            print ('CRITICAL - archivelog apply latency %d(s)|%s' % (listResult[3],perf))
            return 2
         elif listResult[3] > int(v_warning):
            print ('WARNING - archivelog apply latency %d(s)|%s' % (listResult[3],perf))
            return 1
         else:
            print ('OK - archivelog apply status ok|%s' % (perf))
            return 0
      else:
         print ('WARNING - no data found')
         return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def dg_arch_dest(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select t.dest_id,t.status,t.error
      from v$archive_dest_status t
      where t.type='PHYSICAL'
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if len(listResult) > 0:
         if listResult[1] != 'VALID':
            print ('CRITICAL - archive dest status error:%s|status=2' % listResult[2])
            return 2
         else:
            print ('OK - archive dest status ok|status=1')
            return 0
      else:
         print ('WARNING - no data found')
         return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def dg_pri_proc(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      SELECT PROCESS, PID, STATUS, THREAD#, SEQUENCE#
      FROM v$managed_standby t
      WHERE t.process not in ('ARCH')
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if len(listResult) > 0:
         if listResult[2] != 'WRITING':
            print ('CRITICAL - standby process abnormal:process=%s,pid=%s,status=%s,thread=%s,seq=%s|status=2' % listResult)
            return 2
         else:
            print ('OK - standby process status is %s|status=1' % listResult[2])
            return 0
      else:
         print ('WARNING - no data found')
         return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def dg_sby_proc(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      SELECT PROCESS, PID, STATUS, THREAD#, SEQUENCE#
      FROM v$managed_standby t
      WHERE t.process in ('MRP0')
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if listResult is not None:
         if listResult[2] != 'APPLYING_LOG':
            print ('CRITICAL - standby process abnormal:process=%s,pid=%s,status=%s,thread=%s,seq=%s|status=2' % listResult)
            return 2
         else:
            print ('OK - standby process status is %s|status=1' % listResult[2])
            return 0
      else:
         print ('WARNING - no data found')
         return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def dg_pri_db(v_tnsname,v_user,v_pass):
   try:
      normal=('MAXIMUM PERFORMANCE','PRIMARY','TO STANDBY','MANAGED REAL TIME APPLY','OPEN_READ-ONLY')
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select d.protection_mode,d.database_role, d.switchover_status,t.recovery_mode,t.database_mode
      from v$database d,v$archive_dest_status t
      where t.type='PHYSICAL'
      """
      cursor1.execute(sqltext)
      current=cursor1.fetchone()
      cursor1.close()
      db.close()
      #minus=set(normal) ^ set(current)
      #minus=set(current) ^ set(normal)
      output=''
      for n,c in zip(normal,current):
         if n != c:
            output=('\'%s\' changed to \'%s\',%s' % (n,c,output))
      if len(output) > 1:
         print ('CRITICAL - db status:%s' % output )
         return 2
      else:
         print ('OK - db status is ok ')
         return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def undo_used_size(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select ur undo_retention,
       dbs db_block_size,
       round(((ur * (ups * dbs)) + (dbs * 24)) / 1024 / 1024) as max_used,
       (select round(sum(a.bytes)/1024/1024) from dba_data_files a where a.tablespace_name = (select value from v$parameter where name ='undo_tablespace')) undo_size
      from (select value as ur from v$parameter where name = 'undo_retention'),
      (select (undoblks / 600) ups
      from v$undostat
      where undoblks in (select max(undoblks) from v$undostat)),
      (select value as dbs from v$parameter where name = 'db_block_size')
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchone()
      cursor1.close()
      db.close()
      if len(listResult) > 0:
         perf=('max_used(MB)=%d undo_size(MB)=%d ur=%d' % (listResult[2],listResult[3],int(listResult[0]) ))
         undo_util=listResult[2]/listResult[3]*100
         if undo_util > 90:
            print ('CRITICAL - undo max util is %.2f%% |%s' % (undo_util,perf))
            return 2
         elif undo_util > 85:
            print ('WARNING - undo max util is %.2f%% |%s' % (undo_util,perf))
            return 1
         else:
            print ('OK - undo util is normal|%s' % perf)
            return 0
      else:
          print ('WARNING - no data found')
          return 1
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_uptime(v_tnsname,v_user,v_pass,v_time):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,(sysdate - startup_time)*24*60*60 from gv$instance
      """
      cursor1.execute(sqltext)
      listResult=cursor1.fetchall()
      cursor1.close()
      db.close()
      output=''
      flag=''
      for uptime in listResult:
         if uptime[1] < int(v_time):
            output = ('%d,%s' % (uptime[0],output))
            flag=2
      if flag == 2:
         v_time=round(int(v_time)/60)
         print ('CRITICAL-instance %s reboot %d min ago' % (output,v_time))
         return 2
      else:
          print ('OK - db uptime is ok')
          return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_ash(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,round(value,2) value
      from GV$SYSMETRIC t
      where T.METRIC_NAME='Average Active Sessions'
      and T.INTSIZE_CSEC > 5000
      """
      cursor1.execute(sqltext)
      value=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in value:
         perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db active session|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def wait_class_dbtime(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select replace(c.wait_class,chr(32),'') waitclass,round(m.dbtime_in_wait,2) dbtime
      from v$waitclassmetric m,v$system_wait_class c
      where m.wait_class#=c.wait_class#
      and c.wait_class !='Idle'
      and m.dbtime_in_wait>0.1
      """
      cursor1.execute(sqltext)
      wait_dbtime=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in wait_dbtime:
          perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db wait class in dbtime|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_redo_kbps(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,round(value/1024) value
      from GV$SYSMETRIC t
      where T.METRIC_NAME='Redo Generated Per Sec'
      and T.INTSIZE_CSEC > 5000
      """
      cursor1.execute(sqltext)
      value=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in value:
         perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db redo generate kBytes/s|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_logical_reads(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,round(value) value
      from GV$SYSMETRIC t
      where T.METRIC_NAME='Logical Reads Per Sec'
      and T.INTSIZE_CSEC > 5000
      """
      cursor1.execute(sqltext)
      value=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in value:
         perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db Logical Reads Per Sec|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_physical_reads(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,round(value/1024) value
      from GV$SYSMETRIC t
      where T.METRIC_NAME='Physical Read Bytes Per Sec'
      and T.INTSIZE_CSEC > 5000
      """
      cursor1.execute(sqltext)
      value=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in value:
         perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db physical Reads KBytes Per Sec|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

def db_physical_write(v_tnsname,v_user,v_pass):
   try:
      db=cx_Oracle.connect(v_user,v_pass,v_tnsname)
      cursor1=db.cursor()
      sqltext="""
      select inst_id,round(value/1024) value
      from GV$SYSMETRIC t
      where T.METRIC_NAME='Physical Write Bytes Per Sec'
      and T.INTSIZE_CSEC > 5000
      """
      cursor1.execute(sqltext)
      value=cursor1.fetchall()
      cursor1.close()
      db.close()
      perf=''
      for line in value:
         perf=('inst%s=%.2f %s' % (line[0],float(line[1]),perf))
      print ('OK - db physical Write KBytes Per Sec|%s' % perf)
      return 0
   except Exception as err:
      print ('CRITICAL - %s' % err)
      return 2

# main program	
argv=sys.argv
if argv[-1]=='tbs_usage':
    v_result=func_tbs_usage(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='tbs_size':
    v_result=func_tbs_size(argv[1],argv[2],argv[3],argv[4])
    exit(v_result)
elif argv[-1]=='arch_usage':
    v_result=func_archusage(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='asm_usage':
    v_result=func_asm_usage(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='sess_wait':
    v_result=func_sess_wait(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='sess_num':
    v_result=func_sess_num(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='trans_ops':
    v_result=func_trans_longops(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='trans_num':
    v_result=num_of_transaction(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='longops':
    v_result=session_longops(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='undostat':
    v_result=undostat(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='archstat':
    v_result=archstat(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='user_stat':
    v_result=user_stat(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='memory_hit':
    v_result=memory_hit(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='process_num':
    v_result=process_num(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='db_time':
    v_result=db_time(argv[1],argv[2],argv[3],argv[4])
    exit(v_result)
elif argv[-1]=='dg_arch_gap':
    v_result=dg_arch_gap(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='dg_apply_latency':
    v_result=dg_apply_latency(argv[1],argv[2],argv[3],argv[4],argv[5])
    exit(v_result)
elif argv[-1]=='dg_arch_dest':
    v_result=dg_arch_dest(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='dg_pri_proc':
    v_result=dg_pri_proc(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='dg_sby_proc':
    v_result=dg_sby_proc(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='dg_pri_db':
    v_result=dg_pri_db(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='undo_used_size':
    v_result=undo_used_size(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='db_uptime':
    v_result=db_uptime(argv[1],argv[2],argv[3],argv[4])
    exit(v_result)
elif argv[-1]=='db_ash':
    v_result=db_ash(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='wait_class_dbtime':
    v_result=wait_class_dbtime(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='db_physical_write':
    v_result=db_physical_write(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='db_physical_reads':
    v_result=db_physical_reads(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='db_logical_reads':
    v_result=db_logical_reads(argv[1],argv[2],argv[3])
    exit(v_result)
elif argv[-1]=='db_redo_kbps':
    v_result=db_redo_kbps(argv[1],argv[2],argv[3])
    exit(v_result)
else:
    print ('Pleas input function name!')
    print ('func:')
    print ('     tbs_usage     tnsname username password warning critical')
    print ('     tbs_size      tnsname username password minsize')
    print ('     arch_usage    tnsname username password warning critical #arch recovery size')
    print ('     asm_usage     tnsname username password warning critical')
    print ('     sess_wait     tnsname username password warning critical')
    print ('     sess_num      tnsname username password warning critical')
    print ('     trans_ops     tnsname username password  #check long transaction')
    print ('     trans_num     tnsname username password')
    print ('     undostat      tnsname username password')
    print ('     archstat      tnsname username password warning critical')
    print ('     user_stat     tnsname username password')
    print ('     memory_hit    tnsname username password warning critical')
    print ('     process_num   tnsname username password warning critical')
    print ('     db_time       tnsname username password cpus')
    print ('     dg_arch_gap   tnsname username password')
    print ('     dg_apply_latency  tnsname username password warning critical')
    print ('     dg_arch_dest  tnsname username password')
    print ('     dg_pri_proc   tnsname username password')
    print ('     dg_sby_proc   tnsname username password')
    print ('     dg_pri_db     tnsname username password')
    print ('     undo_used_size    tnsname username password')
    print ('     db_uptime     tnsname username password v_time')
    print ('     db_ash        tnsname username password')
    print ('     wait_class_dbtime        tnsname username password')
    print ('     db_physical_write        tnsname username password')
    print ('     db_physical_reads        tnsname username password')
    print ('     db_logical_reads        tnsname username password')
    print ('     db_redo_kbps        tnsname username password')
