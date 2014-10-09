#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb
import os
import time
import sys
import pycurl
import threading
import ConfigParser
from warnings import filterwarnings

class Single(threading.Thread):

    def __init__(self, routine, suit = {}):
        threading.Thread.__init__(self)
        self._routine = routine
        self._suit = suit

    def run(self):
        tglobal.dbconns = []
        tglobal.suit = self._suit
        self._routine()
        call_hook_func("after_thread_ended", {"suit": self._suit})

def do(func, params, repeat_times=0, doalert=True, span=1):
    time.sleep(span)
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
            level = 2
        else:
            level = 1
        if doalert:
            call_hook_func("alert", {"msg": error, "level": level})
        return False
    return ret

def call_hook_func(funcname, param):
    func = getattr(hookmodule, funcname, None)
    if func:
        try:
            ret = func(**param)
        except Exception, e:
            print funcname
            log("call hook function {funcname} failed: {error}"
            .format(funcname=funcname, error=str(e)))
    else:
        return False

def slave_change_master(slavedb, master_host, master_port, 
        master_logfile, master_logpos, master_user, master_password):
    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("stop slave;")
    cursor.execute("change master to master_host='{host}', master_user='{user}',\
master_password='{password}', master_port={port}, master_log_file='{logfile}', \
master_log_pos={logpos};".format(host=master_host, user=master_user, \
    password=master_password, port=master_port,logfile=master_logfile,\
    logpos=master_logpos))
    cursor.execute("start slave;")
    return True

def slave_become_master(slavedb):
    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("stop slave;")
    cursor.execute("reset master;")
    cursor.execute("show master status;")
    cursor.execute("set global read-only=0;")
    ret = cursor.fetchall()[0]
    master_logfile = ret["File"]
    master_logpos = ret["Position"]
    return (master_logfile, master_logpos)

def iosql_thread(slavedb, slaveinfo = ''):
    host = slaveinfo["host"] if "host" in slaveinfo["host"] else "none"
    port = slaveinfo["port"] if "port" in slaveinfo["port"] else "none"

    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("show slave status")
    ret = cursor.fetchall()[0]
    sqlt_status = ret["Slave_SQL_Running"]
    iot_status = ret["Slave_IO_Running"]
    if sqlt_status != "Yes":
        raise Exception("{host} {port} slave sql thread is not yes"\
              .format(host=host, port=port))
    if iot_status != "Yes":
        raise Exception("{host} {port} slave io thread is not yes"\
              .format(host=host, port=port))
    return True

def repl_delay(slavedb, slaveinfo = ''):
    host = slaveinfo["host"] if "host" in slaveinfo["host"] else "none"
    port = slaveinfo["port"] if "port" in slaveinfo["port"] else "none"

    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("show slave status")
    ret = cursor.fetchall()[0]
    read_master_log_pos = ret["Read_Master_Log_Pos"]
    exec_master_log_pos = ret["Exec_Master_Log_Pos"]

    if read_master_log_pos != exec_master_log_pos:
        raise Exception("{host} {port} slave delay"\
              .format(host=port, port=port))
    return exec_master_log_pos

def same_logfile(slavedb):
    cursor = slavedb.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("show slave status")
    ret = cursor.fetchall()[0]
    master_log_file = ret["Master_Log_File"]
    relay_master_log_file = ret["Relay_Master_Log_File"]
    if master_log_file != relay_master_log_file:
        raise Exception("replay_master_log_file is not the same as master_log_file")
    return master_log_file

def log(msg):
    nowtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    fh = open(logfile, "a")
    fh.write("[%s] %s\n" % (nowtime, msg))

def change_master(slaves):
    setmaster = False
    curpos = 0

    for slave in slaves:
        # 1. connect to any slaves that belongs to the master
        slavedb = do(connect, slave, conrepeat, False, conrespan)
        if slavedb == False:
            continue
        # 2. check if it is the same logfile
        logfile = do(same_logfile, {"slavedb": slavedb}, replrepeat, 
            False, replrespan)
        if logfile == False:
            continue
        # 3. check if it is relay, give it 5 chances to be synced
        logpos = do(repl_delay, {"slavedb": slavedb}, replrepeat, 
            False, replrespan)
        if logpos == False:
            continue

        if not setmaster or curpos < logpos:
            setmaster = slave
            curpos = logpos
    if not setmaster:
        # disaster, no need to alert any more
        # raise Exception("None of the slaves can be raised as master") 
        return False
    bemasterdb = do(connect, setmaster, conrepeat, True, conrespan)
    master_logfile, master_logpos = do(slave_become_master, {"slavedb": bemasterdb})
    master_host, master_port = setmaster["host"], setmaster["port"]
    slaves.remove(setmaster)
    for slave in slaves:
        changeinfo = {
            "slavedb"        : do(connect, slave, conrepeat, True, conrespan),
            "master_host"    : master_host,
            "master_password": repluser,
            "master_user"    : replpass,
            "master_port"    : master_port,
            "master_logpos"  : master_logpos,
            "master_logfile" : master_logfile,
        }
        do(slave_change_master, changeinfo, 0, False)

def connect(host, user, passwd, port):
    try:
        db = MySQLdb.connect(host=host, user=user, passwd=passwd, 
            port=port, connect_timeout=1)
    except Exception, e:
        raise Exception("{host} {port} {sql_err}"\
        .format(host=host, port=port, sql_err=e.args[1]))
    tglobal.dbconns.append(db)
    return db

def cleardb():
    while tglobal.dbconns:
        tglobal.dbconns.pop().close()

def slave_routine(slave):
    slavedb = do(connect, slave, conrepeat, True, conrespan)
    if slavedb == False:
        call_hook_func("slave_connect_error", {"slaveinfo": slave})
        return

    ret = do(iosql_thread, {"slavedb": slavedb, "slaveinfo": slave})
    if ret == False:
        call_hook_func("slave_thread_error", {"slaveinfo": slave})
        return

    ret = do(repl_delay, {"slavedb": slavedb, "slaveinfo": slave})
    if ret == False:
        call_hook_func("slave_delay", {"slaveinfo": slave})
        return

def master_routine(master):
    db = do(connect, master, conrepeat, True, conrespan)
    if not db and autochange:
        call_hook_func("master_connect_error", {"masterinfo": master})
        do(change_master, {"slaves": tglobal.suit["slaves"]})
        

def suit_routine():
    master_routine(tglobal.suit["master"])
    for slave in tglobal.suit["slaves"]:
        slave_routine(slave)

def fork_(pid = False):
    pid = os.fork()
    if pid > 0: 
        if pid:
            fh = open(pidfile, "w")
            fh.write(str(pid))
            fh.close()
        sys.exit(0)

    if pid < 0:
        error_log("fork child process failed!")
        sys.exit(1)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print "usage: mysqlmond [configfile]"
        sys.exit(1)

    if not os.path.isfile(sys.argv[1]):
        print "not a valid config file"
        sys.exit(1)

    config = ConfigParser.ConfigParser()
    config.read(sys.argv[1])

    pidfile     = config.get("log", "pid_file")
    logfile     = config.get("log", "log_file")

    frequency   = config.getfloat("monitor", "frequency")
    hookmodule  = config.get("monitor", "hook_module")
    repluser    = config.get("monitor", "repl_user")
    replpass    = config.get("monitor", "repl_pass")
    conrepeat   = config.getint("monitor", "con_repeat")
    conrespan   = config.getfloat("monitor", "con_repeat_span")
    replrepeat  = config.getint("monitor", "rel_repeat")
    replrespan  = config.getfloat("monitor", "rel_repeat_span")
    autochange  = config.getint("monitor", "auto_change")

    hookmodule = __import__(hookmodule)
    if not getattr(hookmodule, "get_suit", None):
        print "There is no get_suit function in hook module"
        sys.exit(1)

    fork_()
    os.setsid()
    fork_(True)

    filterwarnings('ignore', category = MySQLdb.Warning)
    tglobal = threading.local()
    thread_list = []

    while True:
        time.sleep(frequency)
        call_hook_func("before_monitor_started", {})
        suits = hookmodule.get_suit()
        for suit in suits:
            thread = Single(suit_routine, suit)
            thread_list.append(thread)
            thread.start()
        for thread in thread_list:
            thread.join()
        call_hook_func("after_monitor_ended", {"suits": suits})
