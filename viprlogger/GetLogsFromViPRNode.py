#!/usr/bin/python

"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import calendar
import random
import string

import datetime
import sys


__author__ = "Priya Periaswamy"

import requests


def downloadLogs(viprHost, user, pwd, downloadDirectory):

    #Create session
    # requests.packages.urllib3.disable_warnings()
    session = requests.Session()

    #Login Request
    hostUrl = "https://" + viprHost + ":4443/login"
    # print(hostUrl)
    request = session.get(hostUrl, auth=(user, pwd), verify=False)
    if(request.status_code != 200):
        print("Unable to login to the ViPR node and get token. Verify the credentials passed / if the ViPR is accessible")
        exit(0)

    #Get Token
    token = request.headers['x-sds-auth-token']
    randStr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

    make_dwnFileName = "downloadLogFile_" + randStr + ".zip"


    downloadFileName = downloadDirectory + "/" + make_dwnFileName

    startTime, endTime = getStartAndEndDates()

    print("starting download from ViPR " + viprHost)
    logRequest = "https://" + viprHost +"/system/download?startTime=" + str(startTime*1000) + "&endTime=" + str(endTime*1000) + "&severity=7&service=apisvc&service=authsvc&service=controllersvc&service=coordinatorsvc&service=dbsvc&service=geodbsvc&service=geosvc&service=messages&service=nginx_access&service=nginx_error&service=portalsvc&service=sasvc&service=syssvc&service=systemevents&service=vasasvc"

    logDownloadRequest =  session.get(logRequest, verify=False, headers={'x-sds-auth-token': token, 'Accept': 'application/zip', 'Accept-Charset': 'utf-8'})
    if(request.status_code != 200):
        print("Unable to download the logs. Network glitch maybe. Verify the ViPR logs for the cause.")
        exit(0)
    with open(downloadFileName, 'wb') as f:
        for chunk in logDownloadRequest.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush()
    # print("Download complete.")
    print("Download complete. The downloaded log zip file is " + downloadFileName)
    #Logout Request

    response = session.get("https://" + viprHost + ":4443/logout", verify=False, headers={'x-sds-auth-token': token, 'Accept': 'application/json'})

    return downloadFileName

def getStartAndEndDates():
    print("Enter the start and time when you want the logs to be downloaded (UTC time) format %Y/%m/%d %H:%M:%S:")
    print("Example time format 2016/04/27 15:00:00")

    print("Start time:")

    startTime = sys.stdin.readline()
    startTime_ms =  getTimeinMilliSecs(startTime.strip())

    # print("Start time " + str(startTime_ms))

    print("End time:")
    endTime = sys.stdin.readline()
    endTime_ms =  getTimeinMilliSecs(endTime.strip())
    return startTime_ms, endTime_ms

def getTimeinMilliSecs(dateToConvert):
    try:
        dateFormat = '%Y/%m/%d %H:%M:%S %Z'
        dateToConvert = dateToConvert + " UTC"

        d = datetime.datetime.strptime(dateToConvert, dateFormat)
        # time_ms = time.mktime(d.timetuple())
        # print(time.mktime(d.timetuple()))
        #http://stackoverflow.com/questions/2956886/python-calendar-timegm-vs-time-mktime
        ts = calendar.timegm(d.timetuple())
        return ts
    except ValueError:
            print("Date format is not of type %Y/%m/%d %H:%M:%S %Z")
            print("Example time format 2016/04/27 15:00:00")
            exit(0)



def getLogs(downloadDirectory):
    print("User has requested LogManager to download the log file. Ensure that network configuration is available for "
          "LogManager to connect to ViPR and download logs.")
    print("Enter the ViPR VIP where you want the logs to be downloaded:")
    viprVIP = sys.stdin.readline()
    print("ViPR Username:")
    userName = sys.stdin.readline()
    print("ViPR Password:")
    password = sys.stdin.readline()

    return downloadLogs(viprVIP.strip(), userName.strip(), password.strip(), downloadDirectory)

if __name__ == "__main__":
    getLogs("Data")





