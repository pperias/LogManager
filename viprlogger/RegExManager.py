#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""

import re
import logging
import os
import fileinput
import time
import collections
__author__ = "Priya Periaswamy"

"""
    RegExManager class consists of all the functions responsible for data access
"""

class RegExManager(object):
    """
    Constructor which reads the regex pattern that is referred in the config file
    """
    def __init__(self, appConfig, lmLgr):
        self.lmLogger = lmLgr
        self.date_regex = appConfig['date_regex']
        self.urn_regex = appConfig['urn_regex']
        self.orderNumber_regex = appConfig['orderNumber_regex']
        self.opId_regex = appConfig['opId_regex']
        self.stepId_regex = appConfig['stepId_regex']
        self.relationshipKw_regex = appConfig['queued_state_regex']
        self.orderNumber_anomaly_regex1 = appConfig['orderNumber_anomaly_regex_1']
        self.orderNumber_anomaly_regex2 = appConfig['orderNumber_anomaly_regex_2']
        self.mapReqResponse = appConfig['map_request_response']

    def checkResources(self, resourceList):
        urnregex = "(urn:storageos:)([\\w]*)(?!:|\\w-)*"
        resource=[]
        for eachKw in resourceList:
            res = re.findall(urnregex, eachKw)
            if res:
                convertTupleToList = list(res[0])
                resource.append(convertTupleToList[1])

        #having got all the resource names, find how many times it occurs in this line.

        counter=collections.Counter(resource)
        # If it occurs more than one then neglect this line for relationship
        if(max(counter.values()) > 1):
            return True
        else:
            return False


    """
    getapiReqRespUniqueThreadId function gets the unique theread id, name for the API request / response. WIll look for only POST / GET/ PUT request.
    input - the inputLine that is parsed to build the metaDB
    """

    def getapiReqRespUniqueThreadId(self, input):
        log_thread_id__regex= "(?<=LoggingFilter.java\s\(line\s)([\d]*\)\s)([\d]*)(?=\s>\sGET|\s>\sPOST|\s>\sPUT|\s<\s[\d]*)"
        log_thread_name_regex = "(?<=\s\[)([\w-]*)(?=\]\s\sINFO\s\sLoggingFilter.java \(line\s[\d]*)"

        threadId_name_keyword = None

        lm_threadValue_id = re.search(log_thread_id__regex, input)
        lm_threadValue_name = re.search(log_thread_name_regex, input)
        nodeId , serviceName = self.getNodeAndServiceNameFromLine(input)
        if(lm_threadValue_id and lm_threadValue_name and serviceName):

            thread_id = lm_threadValue_id.groups()[1]

            thread_name = lm_threadValue_name.group()

            threadId_name_keyword = "_".join(("lm_thrdIdKw", nodeId, serviceName, thread_name, thread_id))

        return threadId_name_keyword



    """
    getKeywordsForLine function gets the keywords of the line in the log file that is currently parsed
    input - the inputLine that is parsed to build the metaDB
    """
    # @profile
    def getKeywordsForLine(self, input):
        # if the input line is a xml element, it comes from portal or svc logs. There can be many reason to lead to wrong associations.
        # so set a flag here if any resource is returned more than once in a xml
        # scenario: get all hosts / get all orders.
        # not doing this for non-xml lines since in controller svc, two steps can occur in the same line
        # the flag will help us to negate the associations but gather the place where it occurs in the log files
        keywords=[]
        negateAssocaitionFlag = False
        xmlLine=re.search("<\?xml.*\?>", input)
        if(xmlLine):
            xmlL = True
        else:
            xmlL = False

        # The following regex is for urn
        urn = list(set(re.findall(self.urn_regex, input)))
        if(len(urn) != 0 ):
            keywords.extend(urn)
            if(len(urn) > 1):
                negateAssocaitionFlag = self.checkResources(urn)

        #The following regex is for orderNumber
        orderNumber = list(set(re.findall(self.orderNumber_regex, input)))
        if(len(orderNumber) != 0 ):
            keywords.extend(orderNumber)
            if(len(orderNumber) > 1):
                negateAssocaitionFlag = True

        #The following regex is for op_id
        op_id = list(set(re.findall(self.opId_regex, input)))
        if(len(op_id) != 0 ):
            keywords.extend(op_id)
            if(xmlL and len(op_id) > 1):
                negateAssocaitionFlag = True

        step_id = list(set(re.findall(self.stepId_regex, input)))
        if(len(step_id) != 0 ):
            keywords.extend(step_id)
            if(xmlL and len(step_id) > 1):
                negateAssocaitionFlag = True


        # This is to handle the special case where the step id/op id  that created another step id occurs in seperate step.
        # In BuildOrderTree class, the parent-child relationship is based on the string 'queued state'. refer to the class for more detailed explanation.
        # we can check the allowable states such as Queued, ready etc., but I guess this would solve the case.
        # checkInput = re.search(self.relationshipKw_regex, input)
        # if(checkInput):
        #     joinLineFlag = True
        # else:
        #     joinLineFlag = False

        # map order number
        checkIfOrderNumberExist = re.search(self.orderNumber_anomaly_regex1, input)
        if(checkIfOrderNumberExist):
            orderNumber = re.search(self.orderNumber_anomaly_regex2, checkIfOrderNumberExist.group())
            if(orderNumber):
                vOrderNumber = "vipr:orderNumber=" + orderNumber.group().strip()
                keywords.append(vOrderNumber)
        # if(mapReqResponse):
        # map the threadId in the GET / POST/ PUT request. So that the request and response are mapped
        # uniqueThreadId = self.getapiReqRespUniqueThreadId(input)
        # if(uniqueThreadId):
        #     keywords.append(uniqueThreadId)

        # return keywords, negateAssocaitionFlag, joinLineFlag
        return keywords, negateAssocaitionFlag

    """
    getDateFromLine function gets the date of the line in the log file that is currently parsed
    input - the inputLine that is parsed to build the metaDB
    """
    def getDateFromLine(self, inputLine):
        # Time Stamp
        lnDate = re.search(self.date_regex, inputLine)
        if(lnDate):
            dateValue=lnDate.group()
            if(inputLine.startswith(dateValue) or " " + dateValue in inputLine):
                return dateValue.strip()
            else:
                print("invalid date" + inputLine)
                dateValue = ""
        else:
            dateValue = ""
        return dateValue.strip()

    """
    getServiceNameFromLine function gets the service name of the line in the log file that is currently parsed
    input - the inputLine that is parsed to build the metaDB
    """
    # @profile
    def getNodeAndServiceNameFromLine(self, input):
        # Time Stamp
        nodeId = ""
        serviceName = ""
        node_serviceName_regex = "^.*(?=" + self.date_regex +")"
        node_serviceName = re.search(node_serviceName_regex, input)
        if(node_serviceName):
            node_serviceNameValue=node_serviceName.group()

            if(not node_serviceNameValue.strip()):
                return nodeId, serviceName

            namelist = node_serviceNameValue.strip().split(" ")
            # For darth nodeid was also added
            # <node id> <node name> <service name> <time stamp> <followed by the log detail>

            if(len(namelist) == 3):
                nodeId = namelist[0]
                nodeName = namelist[1]
                serviceName = namelist[2]
            else:
                nodeId = namelist[0]
                serviceName = namelist[1]
        else:
            return nodeId, serviceName
            node_serviceNameValue = ""
        return nodeId.strip(), serviceName.strip()

    """
    replaceSpecialCharacters function checks if the string has special characters and replaces with '_'
    input - the input that needs to be evaluated
    """

    def replaceSpecialCharacters(self, input):
        replacedString = re.sub(r'[^a-zA-Z0-9_-]',r'_',input)
        return replacedString

    def checkdRegex(self, regex, input):
        regex_result = re.search(regex, input)
        if(regex_result):
            retValue=regex_result.group()
        else:
            retValue = ""
        return retValue.strip()

    def checkopIdOrStepIdExists(self, input):
        opIdValue = self.checkdRegex(self.opId_regex, input)
        stepIdValue = self.checkdRegex(self.stepId_regex, input)

        if opIdValue or stepIdValue:
            return True
        else:
            return False

