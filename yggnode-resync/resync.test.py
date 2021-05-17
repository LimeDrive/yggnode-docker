#! /usr/bin/python3

import json
import os
import re
import requests
import time
import yaml
import logging
from retry import retry

def getFromCategory(idCat, CFcookies, catList, domainName, logger):
    if int(idCat) in catList:
        prefixType = "cat"
    else :
        prefixType = "subcat"
    url = "https://" + domainName + "/rss?action=generate&type=" + prefixType + "&id=" + idCat + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
    print(url)
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    if not response.ok:
        return requests.get(url, cookies=CFcookies, headers=headers, timeout=25)
    return requests.get(url, headers=headers, timeout=25)


def ManageTorrents(rssData, CFcookies, idCat, categories, domainName, logger):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    # check if rss file for category requested is available
    if os.path.isfile(os.getcwd() + "/blackhole/rss/" + idCat + ".xml") and (int(idCat) not in categories):
        oldRssFile = open(os.getcwd() + "/blackhole/rss/" + idCat + ".xml", "r")
        oldRssString = oldRssFile.read()
        oldRssFile.close()
        oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRssString)
        for oldIdTorrent in oldRssTorrentsListId:
            if (oldIdTorrent not in rssTorrentsListId) and (os.path.isfile("/blackhole/torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")):
                print("removing --> " + (re.split("=", oldIdTorrent)[1]))
                os.remove(os.getcwd() + "/blackhole/torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for torrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through Flaresolverr
        if not (os.path.exists(os.getcwd() + "/blackhole/torrents/" + str(re.split("=", torrentId)[1]) + ".torrent")):
            url = f"https://{domainName}/rss/download?id={str(re.split('=', torrentId)[1])}&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
            #######  A VOIR SI SA CRASH ICI ######
            if not response.ok:
                r = requests.get(url, cookies=CFcookies, headers=headers, stream=True, timeout=25)
            else:
                r = requests.get(url, headers=headers, stream=True, timeout=25)
            #######################################
            torrentFile = open(os.getcwd() + "/blackhole/torrents/" + str(re.split("=", torrentId)[1]) + ".torrent", "wb")
            for chunk in r.iter_content(chunk_size=8192):
                torrentFile.write(chunk)
            torrentFile.close()
            print("download torrent --> " + str(re.split("=", torrentId)[1]))
            time.sleep(1)

def getCookies(url, domainName, logger):
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
    print(url, payload)
    for i in json.loads((requests.request("POST", url + "/v1", headers=headers, data=payload)).text).get(
            'solution').get('cookies'):
        cookies[i.get('name')] = i.get('value')
    return cookies

def changeDownloadUrl(rssFeed, serverURL, domainName, logger):
    return re.sub("https://" + domainName + "/rss/", serverURL + "/", rssFeed)

## Return rssString, renew cookies if time out error

@retry(tries=5, delay=30, jitter=10, logger=logging.WARNING)
def get_Rss_Feed(cookies):
    try:
        rssString = getFromCategory(str(idCat), cookies, catList, serverConfiguration["yggDomainName"], logging)
        rssString.raise_for_status()
        return rssString.text
    except (ConnectionError, requests.exceptions.RequestException) as e:
        logging.warning(
            f"Connection fails try fix : {e}")
        cookies = getCookies(FlaresolverrPath, serverConfiguration["yggDomainName"], logging)
        logging.info(
            f"New cookies : {str(cookies)} ")
        raise


if __name__ == '__main__':
    
    with open('config/annexes.yml', 'r') as yamlfile:
        serverConfiguration = yaml.load(yamlfile, Loader=yaml.FullLoader)

    if not (os.path.exists(os.getcwd() + "logs/")):
        os.mkdir(os.getcwd() + 'logs')

    logging.basicConfig(
        format='%(levelname)s - %(asctime)s ::   %(message)s', 
        datefmt='%d/%m/%Y %I:%M:%S', 
        level=logging.INFO, 
        filename=os.getcwd() + "/logs/yggnode-resync.log")


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
        response = requests.get(f"https://{str(domainName)}", timeout=2.5)
        print(str(response))
        if not response.ok:
            cookies = getCookies(FlaresolverrPath, serverConfiguration["yggDomainName"], logging)
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
                    ManageTorrents(rssString, cookies, str(idCat), catList, serverConfiguration["yggDomainName"], logging)
                # write rss feed and erasing old xml file
                rssString = (changeDownloadUrl(rssString, nodeURL, serverConfiguration["yggDomainName"], logging))
                file = open(os.getcwd() + "/blackhole/rss/" + str(idCat) + ".xml", "w")
                file.write(rssString)
                file.close()
                logging.info("RSS feed correctly received and analyzed - sleep 5 seconds -")
                time.sleep(5)
            else:
                logging.info("Incorrect response : possible cloudfare captcha or new DNS")
        logging.info("Resync terminated : next in 5 mins")
        time.sleep(300)
