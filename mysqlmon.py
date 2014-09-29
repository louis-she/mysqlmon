#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import os
import time
import sys
import pycurl

SLAVES = [
    {
    "host":"115.28.6.205",
    "port":3312,
    "user":"test",
    "passwd":"2503",
    },
    {
    "host":"115.28.6.205",
    "port":3313,
    "user":"test",
    "passwd":"2503",
    },
]

MASTER = {
    "host":"115.28.6.205",
    "port":3311,
    "user":"test",
    "passwd":"2503",
}

def alert(msg, type):
    print msg
    log(msg)

def do(func, params, repeat_times = 0, exit = True):
    repeat_times += 1
    error = ""
    ret = ""
    while repeat_times:
        repeat_times -= 1
        try:
            ret = func(**params)
        except Exception, e:
            error = e.args[0]
            continue
        break

    if error != "": 
        if repeat_times != 0:
            type = "mail"
        else:
            type = "sms"
        alert(error, type)
        if type == "sms" and exit == True:
            sys.exit(0)

    return ret

def check_process():
    pass

def change_master_routine(change_info):
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("change master to master_host='%s', master_user='repl', master_password='louispass', master_port=%s, master_log_file='%s', master_log_pos=%s;" % (change_info["master_host"], change_info["master_port"], change_info["master_logfile"], change_info["master_logpos"]))
    return True

def iosql_thread(slavedb):
    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("show slave status")
    ret = cursor.fetchall()[0]
    sqlt_status = ret["Slave_SQL_Running"]
    iot_status = ret["Slave_IO_Running"]
    if sqlt_status != "Yes":
        raise Exception("slave sql thread is not yes")
    if iot_status != "Yes":
        raise Exception("slave io thread is not yes")
    return True

def repl_delay(slavedb):
    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("show slave status")
    ret = cursor.fetchall()[0]
    read_master_log_pos = ret["Read_Master_Log_Pos"]
    exec_master_log_pos = ret["Exec_Master_Log_Pos"]
    if read_master_log_pos != exec_master_log_pos:
        raise Exception("sql delay")
    return exec_master_log_pos

def same_logfile(db):
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    ret = cursor.execute("show slave status")[0]
    master_log_file = ret["Master_Log_File"]
    relay_master_log_file = ret["Relay_Master_Log_File"]
    if master_log_file != relay_master_log_file:
        raise Exception("replay_master_log_file is not the same as master_log_file")
    return master_log_file

def log(msg):
    nowtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    fh = open("./logfile", "a")
    fh.write("[%s] %s" % (nowtime, msg))

def change_master(slaves):
    changeinfo = {}
    for slave in slaves:
        # 1. connect to any slaves that belongs to the master
        slavedb = do(connect, slave, 3, False)
        if slavedb == False:
            continue
        # 2. check if it is the same logfile
        logfile = do(same_logfile, slavedb, 3, False)
        if logfile == False:
            continue
        # 3. check if it is relay, give it 5 chances to be synced
        logpos  = do(repl_delay, slavedb, 5, False)
        if logpos == False:
            continue
        
        if "logpos" not in changeinfo or toppos["logpos"] < logpos:
            changeinfo = {
                "master_host":     slave["host"],
                "master_port":     slave["port"],
                "master_logfile":  logfile,
                "master_logpos" :  logpos,
            }

    change_master_routine(changeinfo)

def connect(host, user, passwd, port):
    try:
        db = MySQLdb.connect(host=host, user=user, passwd=passwd, port=port)
    except Exception, e:
        raise Exception(e.args[1])
    return db

def slave_routine(slave):
    slavedb = do(connect, slave, 5)
    do(iosql_thread, {"slavedb": slavedb})
    do(repl_delay, {"slavedb": slavedb})

def master_routine(master):
    db = do(connect, master, 5)
    if not db:
        change_master([SLAVE])

if __name__ == "__main__":

    master_routine(MASTER)
    for slave in SLAVES:
        slave_routine(slave)
