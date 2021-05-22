#! /usr/bin/python3

import json
import os
import re
import requests
import time
import yaml
import logging
from retry import retry

def getFromCategory(idCat, cookies, catList, domainName):
    if int(idCat) in catList:
        prefixType = "cat"
    else :
        prefixType = "subcat"
    url = "https://" + domainName + "/rss?action=generate&type=" + prefixType + "&id=" + idCat + "&passkey=TNdVQssYfP3GTDoB3ijgE37c8MVvkASH"
    logging.debug(f"Url {url}")
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    return (requests.get(url, cookies=cookies, headers=headers, timeout=25)).text


def ManageTorrents(rssData, CFcookies, idCat, categories, domainName):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    # check if rss file for category requested is available and remove old torrents
    if os.path.exists(f"blackhole/rss/{idCat}.xml") and (int(idCat) not in categories):
        with open(f"blackhole/rss/{idCat}.xml", "r") as oldRss:
            oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRss)
        for oldIdTorrent in oldRssTorrentsListId:
            if oldIdTorrent not in rssTorrentsListId:
                oldId = re.split("=", oldIdTorrent)[1]
                if os.path.exists(f"blackhole/torrents/{oldId}.torrent"):
                    os.remove(f"blackhole/torrents/{oldId}.torrent")
                    logging.info(f"removing --> {oldId}.torrent")

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for fullTorrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through Flaresolverr
        torrentId = re.split("=", fullTorrentId)[1]
        if not os.path.exists(f"blackhole/torrents/{torrentId}.torrent"):
            url = f"https://{domainName}/rss/download?id={torrentId}&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
            # Timeout with flarrsolver ??
            r = requests.get(url, cookies=CFcookies, headers=headers, stream=True, timeout=25)
            with open(f"blackhole/torrents/{torrentId}.torrent", "wb") as torrentFile:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        torrentFile.write(chunk)
            logging.info("download torrent --> " + str(re.split("=", torrentId)[1]))
            time.sleep(0.5)

def getCookies(url, domainName):
    payload = json.dumps({
        "cmd": "request.get",
        "url": "https://" + domainName,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "maxTimeout": 60000,
    })
    headers = {
        'Content-Type': 'application/json'
    }
    cookies = dict()
    logging.debug(url + payload)
    for i in json.loads((requests.request("POST", url + "/v1", headers=headers, data=payload)).text).get(
            'solution').get('cookies'):
        cookies[i.get('name')] = i.get('value')
    return cookies

def changeDownloadUrl(rssFeed, serverURL, domainName):
    return re.sub(f"https://{domainName}/rss/", f"{serverURL}/", rssFeed)

def changeTitleRss(idCat, rssString):
    catNum = serverConfiguration["sub-Categories"]["id"] + serverConfiguration["Categories"]["id"]
    catNames = serverConfiguration["sub-Categories"]["idLabel"] + serverConfiguration["Categories"]["idLabel"]
    index = catNum.index(idCat)
    catTitle = catNames[index]
    return re.sub("YggTorrent Tracker BitTorrent Francophone - Flux RSS", f"Yggnode RSS : {catTitle}", rssString)

# Return rssString, renew cookies if time out error

@retry(tries=5, delay=60, jitter=10, logger=logging)
def get_Rss_Feed(cookies):
    try:
        return getFromCategory(str(idCat), cookies, catList, serverConfiguration["yggDomainName"])
    except (ConnectionError, requests.exceptions.RequestException) as e:
        logging.warning(
            f"Connection fails try fix : {e}")
        cookies = getCookies(FlaresolverrPath, serverConfiguration["yggDomainName"])
        logging.info(
            f"New cookies : {str(cookies)} ")
        raise


if __name__ == '__main__':
    
    with open('config/annexes.yml', 'r') as yamlfile:
        serverConfiguration = yaml.load(yamlfile, Loader=yaml.FullLoader)

    os.makedirs("logs", exist_ok=True)
    os.makedirs("blackhole/torrents/temp", exist_ok=True)
    os.makedirs("blackhole/rss", exist_ok=True)

    logging.basicConfig(
        format='%(levelname)s - %(asctime)s ::   %(message)s', 
        datefmt='%d/%m/%Y %H:%M:%S', 
        level=logging.DEBUG, 
        filename="logs/yggnode-resync.log")


    # construct string containing ip and port server
    FlaresolverrPath = "http://" + str(serverConfiguration["flaresolverr"]["ipAdress"]) + ":" + \
                       str(serverConfiguration["flaresolverr"]["port"])
    # FlaresolverrPath = "http://flaresolverr:8191"

    nodeURL = serverConfiguration["node"]["protocol"] + "://" + str(
        serverConfiguration["node"]["ipAdress"]) + ":" + str(serverConfiguration["node"]["port"])
    logging.info(
        f"Server URL : {nodeURL}")
    # read category to be syncing on this node.
    catList = serverConfiguration["Categories"]["id"]
    subCatList = serverConfiguration["sub-Categories"]["id"]
    domainName = serverConfiguration["yggDomainName"]
    logging.info("Successfully load categories to sync")
    # infinite loop to resync every X seconds
    while True:
        response = requests.get(f"https://{str(domainName)}", timeout=10)
        logging.debug(
            f" Response : {str(response)} ")
        if not response.ok:
            cookies = getCookies(FlaresolverrPath, serverConfiguration["yggDomainName"])
            logging.info(
                f" Flaresolverr cookies : {str(cookies)} ")
        else:
            cookies = dict()
            logging.info(
                f" No cookies = not hungry /. event that's not gonna happend ")        
        for idCat in subCatList + catList:
            logging.info(
                f"Process category : {str(idCat)}")
            # get rss feed from idCat and renew cookie if needed
            rssString = get_Rss_Feed(cookies)
            if rssString.find("<!DOCTYPE HTML>") == -1:
                logging.info("rssString Correct response")
                # download new torrents
                if idCat not in catList:
                    logging.info("Process torrent management")
                    ManageTorrents(rssString, cookies, str(idCat), catList, serverConfiguration["yggDomainName"])
                # write rss feed and erasing old xml file
                rssString = changeDownloadUrl(rssString, nodeURL, serverConfiguration["yggDomainName"])
                rssString = changeTitleRss(idCat, rssString)
                with open(f"blackhole/rss/{str(idCat)}.xml", "w") as file:
                    file.write(rssString)
                logging.info("RSS feed correctly received and analyzed - sleep 5 seconds -")
                time.sleep(3)
            else:
                logging.info("Incorrect response : possible cloudfare captcha or new DNS")
        logging.info("Resync terminated : next in 5 mins")
        time.sleep(300)
