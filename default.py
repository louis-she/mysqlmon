#!/usr/bin/python
import MySQLdb

def alert(msg, level):
    """
    alert user
    @param msg string the message to send
    @param grade int error level 1: fatal 2: warning
    @return null
    """
    pass

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
    pass

def before_monitor_started():
    """
    before every things is started
    """
    pass

def slave_connect_error(slaveinfo):
    """
    after any slave connect failed
    """
    pass
    
def slave_delay(slaveinfo):
    """
    after any slave delay
    """
    pass

def slave_thread_error(slaveinfo):
    """
    after any slave io or sql thread is not Yes
    """
    pass

def master_connect_error(masterinfo):
    """
    after master connect failed
    before change master
    """
    pass

def after_thread_ended(suit):
    """
    after one suit monitor is ended
    """
    pass

def after_monitor_ended(suits):
    """
    after all monitor thread ended
    """
    pass
