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
