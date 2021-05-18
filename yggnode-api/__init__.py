#! /usr/bin/python3

from yggnode import app
import os

if __name__ == '__main__':
    # initialize working environment for python server
    
    if not (os.path.exists(os.getcwd() + "/blackhole/rss/")):
        os.mkdir(os.getcwd() + '/blackhole/rss')
    if not (os.path.exists(os.getcwd() + "/blackhole/torrents/")):
        os.mkdir(os.getcwd() + '/blackhole/torrents')
    if not (os.path.exists(os.getcwd() + "/blackhole/torrents/tmp")):
        os.mkdir(os.getcwd() + '/blackhole/torrents/tmp')

    # Start app
    app.run()
    



