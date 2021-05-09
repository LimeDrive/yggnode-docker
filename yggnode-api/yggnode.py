#! /usr/bin/python3
import os
import re
import time

import yaml
from flask import Flask, request, send_file, Response, render_template
from torrentool.api import Torrent

# server passkey which has not to bee a validated passkey
# but valid in means of length and format for getting RSS Feed and .torrent files
USER_PASSKEY = "ijnXPgYNat3VMnCsqofjUsU5zePmZr9C"

app = Flask(__name__)

# init config file:
with open('config/annexes.yml', 'r') as ymlfile:
    confFile = yaml.load(ymlfile, Loader=yaml.FullLoader)



@app.route('/')
def index():
    # confFile = open(os.getcwd() + "/config/annexes.yml", 'r')
    # confFile = yaml.safe_load(confFile)
    # confFile.close()
    return "USE : <br> \
           /download?id={torrent_id}&passkey={your_passkey}<br> \
           /rss?id={category id}&passkey={your_passkey}<br><br> \
           Categories List available <a href=" + str(confFile["node"]["protocol"])\
           + "://" + str(confFile["node"]["ipAdress"]) + ":" + str(confFile["node"]["port"]) + "/links><strong>Here</strong></a>"+ \
           "<br><br><a href=" + str(confFile["node"]["protocol"]) + "://" + str(confFile["node"]["ipAdress"]) + ":"\
                             + str(confFile["node"]["port"]) + "/status>Server last time resynchronization</a>"


@app.route('/download', methods=['GET'])
def generatingTorrent():
    remoteTempTorrent()
    if not (os.path.isfile(os.getcwd() + "/blackhole/torrents/" + request.args.get("id") + ".torrent")):
        return "torrent unavailable"
    # grab torrent file matching id provided
    my_torrent = Torrent.from_file(os.getcwd() + "/blackhole/torrents/" + request.args.get("id") + ".torrent")
    # changing passkey for one transmitted as parameter by user
    newUrlTracker = re.sub("[a-zA-Z0-9]{32}", request.args.get("passkey"), ((my_torrent.announce_urls[0])[0]))
    my_torrent.announce_urls = newUrlTracker
    # write it in temp dir for more clarity
    my_torrent.to_file(os.getcwd() + "/blackhole/torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent")
    # send torrent file
    return send_file(os.getcwd() + "/blackhole/torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent",
                     as_attachment=True,
                     attachment_filename=(my_torrent.name + ".torrent"),
                     mimetype='application/x-bittorrent')


@app.route('/rss', methods=['GET'])
def generatingRSS():
    remoteTempTorrent()
    # check if category id is provided and valid
    if request.args.get("id") is None or int(request.args.get("id")) < 2139 \
            or int(request.args.get("id")) == 2146 \
            or int(request.args.get("id")) > 2187:
        return "bad category requested"
    # check if passkey with valid format is provided
    if request.args.get("passkey") is None:
        return "passkey not provided : please send one as parameter 'passkey'"

    if not (os.path.isfile(os.getcwd() + "/blackhole/rss/" + request.args.get("id") + ".xml")):
        return "rss file unavailable for this category at the moment"

    # opens last updated rss file corresponding to the category called
    rssFile = open(os.getcwd() + "/blackhole/rss/" + request.args.get("id") + ".xml", "r")
    txt = rssFile.read()
    rssFile.close()
    # create a temp rss generated file with both category and passkey as name to avoid potential simultaneous access
    # replace original passkey by the one provided by the user
    user = request.args.get("user")
    psw = request.args.get("psw")
    passkey = request.args.get("passkey")
    ipA = confFile["node"]["ipAdress"]
    # txt = re.sub("passkey=[a-zA-Z0-9]{32}", f"passkey={passkey}", txt)
    # txt = re.sub(ipA, f"{user}:{psw}@{ipA}", txt)
    txt = re.sub(ipA, f"{user}:{psw}@{ipA}", re.sub("passkey=[a-zA-Z0-9]{32}", f"passkey={passkey}", txt))
    return Response(txt, mimetype='text/xml')


def remoteTempTorrent():
    now = time.time()
    # browses all files and delete every having more than 5 secs of existence
    for torrentFile in os.listdir(os.getcwd() + "/blackhole/torrents/tmp/"):
        if os.stat(os.getcwd() + "/blackhole/torrents/tmp/" + torrentFile).st_mtime < now:
            os.remove(os.getcwd() + "/blackhole/torrents/tmp/" + torrentFile)

@app.route('/links', methods=['GET'])
def generateLinks():
    if request.args.get("passkey") == None or len(request.args.get("passkey")) != 32:
        return render_template('form.html')
    elif not request.args.get("user"):
        return render_template('form.html')
    elif not request.args.get("psw"):
        return render_template('form.html')
    else:
        url_prot = str(confFile["node"]["protocol"])
        ipA = str(confFile["node"]["ipAdress"])
        port = str(confFile["node"]["port"]) # not realy needed
        CatID = confFile["Categories"]["id"]
        subCatID = confFile["sub-Categories"]["id"]
        CatID_label = confFile["Categories"]["idLabel"]
        subCatID_label = confFile["sub-Categories"]["idLabel"]
        passkey = str(request.args.get("passkey"))
        user = str(request.args.get("user"))
        psw = str(request.args.get("psw"))        
        renderTxt = "Flux généralistes : <br>"
        for index in range(len(CatID)):
            renderTxt += f"<strong>{str(CatID_label[index])} :</strong><br>{url_prot}://{user}:{psw}@{ipA}:{port}/rss?id={str(CatID[index])}&passkey={passkey}&user={user}&psw={psw}<br>"
        renderTxt += "<br><br><br>Flux détaillés : <br>"
        for index in range(len(subCatID)):
            renderTxt += f"<strong>{str(subCatID_label[index])} :</strong><br>{url_prot}://{user}:{psw}@{ipA}:{port}/rss?id={str(subCatID[index])}&passkey={passkey}&user={user}&psw={psw}<br>"

    return renderTxt

@app.route('/status', methods=['GET'])
def getStatus():
    # confFile = open(os.getcwd() + '/config/annexes.yml', 'r')
    # confFile = yaml.safe_load(confFile)
    # confFile.close()
    now = time.time()
    renderTxt = ""
    for index in range(len(confFile["Categories"]["id"])):
        renderTxt += "<strong>" + confFile["Categories"]["idLabel"][index] + "</strong> : " + str(time.ctime(os.stat(os.getcwd() + "/blackhole/rss/" + str(confFile["Categories"]["id"][index]) + ".xml").st_mtime)) + "<br>"
    renderTxt += "<br><br>"
    for index in range(len(confFile["sub-Categories"]["id"])):
        renderTxt += "<strong>" + confFile["sub-Categories"]["idLabel"][index] + "</strong> : " + str(time.ctime(os.stat(os.getcwd() + "/blackhole/rss/" + str(confFile["sub-Categories"]["id"][index]) + ".xml").st_mtime)) + "<br>"

    return renderTxt

if __name__ == '__main__':
    # initialize working environment for python server
    if not (os.path.exists(os.getcwd() + "/blackhole/rss/")):
        os.mkdir(os.getcwd() + '/blackhole/rss')
    if not (os.path.exists(os.getcwd() + "/blackhole/torrents/")):
        os.mkdir(os.getcwd() + '/blackhole/torrents')
    if not (os.path.exists(os.getcwd() + "/blackhole/torrents/tmp")):
        os.mkdir(os.getcwd() + '/blackhole/torrents/tmp')
    
    app.run(host='0.0.0.0', port=5000)
