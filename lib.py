#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import time
import sys

def fork_(pidfile = False):
    pid = os.fork()
    if pid > 0: 
        if pidfile:
            fh = open(pidfile, "w")
            fh.write(str(pid))
        sys.exit(0)
    elif pid < 0:
        error_log("fork child process failed!")
        sys.exit(1)

def log(msg, logfile):
    nowtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    fh = open(logfile, "a")
    fh.write("[%s] %s\n" % (nowtime, msg))
