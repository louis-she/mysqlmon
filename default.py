#!/usr/bin/python
import MySQLdb

def alert(msg, level):
    """
    alert user
    @param msg string the message to send
    @param grade int error level 1: fatal 2: warning
    @return null
    """
    fh = open("alert.log", "a")
    fh.write(msg + str(level) + "\n")
    fh.close()

def get_suit():
    """
    get the monitor suit
    @return list as
    [
        {
            "slaves": [
                #slave should be at leat 2 instance
                {
                "host":"127.0.0.1",
                "port":3312,
                "user":"test",
                "passwd":"123",
                },
                {
                "host":"127.0.0.1",
                "port":3313,
                "user":"test",
                "passwd":"123",
                },
                # add more ...
            ],
            "master": {
                "host":"127.0.0.1",
                "port":3311,
                "user":"test",
                "passwd":"123",
            }
        },
        # add more ...
    ]
    """
    ret = [
        {
            "slaves": [
                #slave should be at leat 2 instance
                {
                "host":"127.0.0.1",
                "port":3312,
                "user":"test",
                "passwd":"123",
                },
                {
                "host":"127.0.0.1",
                "port":3313,
                "user":"test",
                "passwd":"123",
                },
                # add more ...
            ],
            "master": {
                "host":"127.0.0.1",
                "port":3311,
                "user":"test",
                "passwd":"123",
            }
        },
        # add more ...
    ]
    return ret

def _wt(content):
    fh = open("test_hook", "a")
    fh.write(content + "\n")
    fh.write("===================================\n")
    fh.close()

def before_monitor_started():
    """
    before every things is started
    """
    _wt("***before_monitor_started***")

def slave_connect_error(slaveinfo):
    """
    after any slave connect failed
    """
    _wt("***slave_connect_error***")
    _wt(str(slaveinfo))
    
def slave_delay(slaveinfo):
    """
    after any slave delay
    """
    _wt("***slave_delay***")
    _wt(str(slaveinfo))

def slave_thread_error(slaveinfo):
    """
    after any slave io or sql thread is not Yes
    """
    _wt("***slave_thread_error***")
    _wt(str(slaveinfo))

def master_connect_error(masterinfo):
    """
    after master connect failed
    before change master
    """
    _wt("***master_connect_error***")
    _wt(str(masterinfo))

def after_thread_ended(suit):
    """
    after one suit monitor is ended
    """
    _wt("***after_thread_ended***")
    _wt(str(suit))

def after_monitor_ended(suits):
    """
    after all monitor thread ended
    """
    _wt("***after_monitor_ended***")
    _wt(str(suits))
