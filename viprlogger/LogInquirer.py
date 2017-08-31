#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import logging
from operator import attrgetter
import collections
import re

from MetaDB import MetaDB
from DataManager import DataManager
from FileManager import FileManager
import json
import datetime

__author__ = "Priya Periaswamy"

"""
    LogInquirer class investgates the metaDB and the order info passed and gets the log output for the order
"""


class LogInquirer(object):

    def __init__(self, appConfig,  fileMgr, dataMgr, lmLgr):

        self.dataManager = dataMgr
        self.fileManager = fileMgr
        self.metaDB = self.dataManager.getMetaDB()
        self.finalKeyWordQueue = []
        self.uniqueOrderIdAndTasks = []
        self.lmLogger = lmLgr
        self.kwTree = {}

    def getUniqueOrderIdAndTasks(self):
        return self.uniqueOrderIdAndTasks


    """
    addFinalKeyWord function saves the keyword to the queue
    keyword - keyword to save to the queue
    """

    def addFinalKeyWord(self, keyword):
        if (keyword not in self.finalKeyWordQueue):
            self.lmLogger.debug("Adding keyword "+keyword)
            self.finalKeyWordQueue.append(keyword)

    """
    getIndexFromKeywordDict function gets the index from the dictionary for the keyword
    keywordDict - keyword dictionary
    keyword - keyword for which index is requested
    """

    def getIndexFromKeywordDict(self, keywordDict, keyword):
        return keywordDict.get(keyword)

    """
    getKeywordFromIndex function gets the keyword from the metaDB for the index passes
    metaDBList - metaDB list
    index - index for the keyword requested
    """

    def getKeywordFromIndex(self, metaDBList, index):
        return metaDBList[index]

    """
    checkExclusionKeyword function checks if the keyword that is currently investigated should be excluded
    exclusionList - exclusion list from config file
    keyword - keyword investigated
    """

    def checkExclusionKeyword(self, keyword, exclusionList):
        for eachExclusionKeyword in exclusionList:
            if (eachExclusionKeyword in keyword):
                return True
        else:
            return False

    """
    addAssociatedKeywords function adds the associated keywords for the keyword that is investigated
    keyword - keyword to save to the queue
    passNum - passNum requested
    """

    def addAssociatedKeywords(self, keyword, passNum_exclusionList):
        indxList = self.dataManager.keywordDict.get(keyword)
        for eachIndexVal in indxList:
            metaRow = self.metaDB.tagsList[eachIndexVal]
            keywordListFromIndex = metaRow.keywords
            if(metaRow.negateAssociationFlag):
                # no need to investigate this row since it might lead to wrong associations
                continue

            for eachKeywordFromIndex in keywordListFromIndex:
                if eachKeywordFromIndex in self.finalKeyWordQueue:
                    # if the keyword is already in the final list then continue, no need to check for exlcusion list
                    continue
                # check that the exclusionList is not empty and
                # if the investigated keyword is in the exclusion list that is passed
                if passNum_exclusionList and self.checkExclusionKeyword(eachKeywordFromIndex,
                                                                        tuple(passNum_exclusionList)):
                    pass
                else:
                    self.addFinalKeyWord(eachKeywordFromIndex)

    """
    fetchLogData function fetches the log information for the saved keywords
    """

    def fetchLogData(self, passNum, searchString):
        logIndex = set([])
        logData = []

        for eachKeyword in self.finalKeyWordQueue:
            indxList = self.dataManager.keywordDict.get(eachKeyword)
            logIndex |= set(indxList)
        for eachIndex in logIndex:
            metaRow = self.metaDB.tagsList[eachIndex]
            logData.append(metaRow)
        # This is the only place where we sort. We do not need to sort the input since for building the
        #  associations there is no  need to sort and get the relationship.
        logData = sorted(logData, key=attrgetter("timestamp"))
        #self.fileManager.writeMetaRowToFile(logData, passNum, True)
        outputFile = self.fileManager.writeLogInfoToOutput(logData, passNum, searchString)
        return outputFile

    """
    getAssociatedResource function gets the assocaited orderNum for the passed orderId, taskId for the passed orderId etc.,

    investigatedId - the id for which the resource should be identified
    asociatedResource - the resource such as orderNum or taskId
    """

    def getAssociatedResource(self, investigatedId, asociatedResourceRegex):
        investgId_indxlist = self.dataManager.keywordDict.get(investigatedId)
        idList = []
        mostCommonId = None

        for eachIndexVal in investgId_indxlist:
            metaRow = self.metaDB.tagsList[eachIndexVal]
            if(not metaRow.negateAssociationFlag):
                keywordListFromIndex = metaRow.keywords

                keywordListFromIndex_string = str(keywordListFromIndex)

                id_re_list=list(set(re.findall(asociatedResourceRegex, keywordListFromIndex_string)))
                if(len(id_re_list) == 1 ):
                     idList.extend(id_re_list)

        counter=collections.Counter(idList)

        commonIdList = counter.most_common()

        if(len(commonIdList) > 0):
            mostCommonId = commonIdList[0][0]

        return mostCommonId

    """
    """
    def getUniqueRootIds(self):
        parent = "root"
        self.uniqueOrderIdAndTasks =[]
        self.kwTree = {}

        num_orderId_occurence = [i for i, x in enumerate(self.finalKeyWordQueue) if
                                       "urn:storageos:Order:".lower() in x.lower()]
        for i in range(len(num_orderId_occurence)):
            orderNum = self.getAssociatedResource(self.finalKeyWordQueue[num_orderId_occurence[i]], "vipr:orderNumber=[\\w]*")
            if not orderNum:
                orderNum = "OrderNumber"
            self.uniqueOrderIdAndTasks.append(self.finalKeyWordQueue[num_orderId_occurence[i]])
            self.kwTree.setdefault(parent, list()).append((orderNum, self.finalKeyWordQueue[num_orderId_occurence[i]]))


        num_taskId_occurence = [i for i, x in enumerate(self.finalKeyWordQueue) if
                                       "urn:storageos:Task:".lower() in x.lower()]

        for i in range(len(num_taskId_occurence)):
            treeAdd_flag = True
            # get the orderId for this taskId
            orderId = self.getAssociatedResource(self.finalKeyWordQueue[num_taskId_occurence[i]], "urn:storageos:Order:[\\w-]*:[\\w]*")
            op_id = self.getAssociatedResource(self.finalKeyWordQueue[num_taskId_occurence[i]], "(?<!:|\\w)[\\w]{8}-[\\w]*-[\\w]*-[\\w]*-[\\w]{12}(?!:|\\w)")
            """
                There is a situation where the same op-id is mapped to more than one task.
                In this scenario, we should make a tuple in such a way that task and opid are all related. rather than printing in seperate blocks
            """

            #if(op_id in self.kwTree.values())

            for keys in self.kwTree:
                kwTreeValues = self.kwTree[keys]
                for kwtreeIndex in range(len(kwTreeValues)):
                    tupleVal = kwTreeValues[kwtreeIndex]
                    if(op_id in tupleVal):
                        treeAdd_flag = False
                        kwTreeValues[kwtreeIndex] = kwTreeValues[kwtreeIndex] + (self.finalKeyWordQueue[num_taskId_occurence[i]],)

            # if there is a orderId assocaited with this task then this is not the root
            if(not orderId):
                parent = "root"
                self.uniqueOrderIdAndTasks.append(self.finalKeyWordQueue[num_taskId_occurence[i]])
                if(treeAdd_flag):
                    self.kwTree.setdefault(parent, list()).append((self.finalKeyWordQueue[num_taskId_occurence[i]], op_id))
            else:
                parent = orderId
                if(treeAdd_flag):
                    self.kwTree.setdefault(parent, list()).append((self.finalKeyWordQueue[num_taskId_occurence[i]], op_id))

    """
        This is a convinience method to remove all the thread ids after using them to print in the output. Since the keywordQueue will be used while building the tree.
        It would be unneccary to have the threadId data.

    """
    def cleanUpKeyWordQueue(self):
        self.finalKeyWordQueue = [eachElement for eachElement in self.finalKeyWordQueue if
                                       "lm_thrdIdKw_".lower() not in eachElement.lower()]

        self.lmLogger.debug("the keywords are:")
        self.lmLogger.debug(self.finalKeyWordQueue)



    """
    getLogData function fetches the log information for the orderInfo
    searchString - the orderInfo such as orderNum / order ID / task ID
    passNum - the pass number passed in the input
    """

    def getLogData(self, orderInfoValuesList, writeInSingleFile, outFileNameAppendString, passNum, exclusionList):
        self.finalKeyWordQueue = []
        self.uniqueOrderIdAndTasks =[]
        self.kwTree = {}
        responseDict = {}
        inquiryList = []

        for i in range(len(orderInfoValuesList)):
            inputSearchString = orderInfoValuesList[i]
            if (inputSearchString.isdigit()):
                searchString = "vipr:orderNumber=" + str(inputSearchString)

            else:
                searchString = inputSearchString

            if (searchString in self.dataManager.keywordDict.keys()):
                self.lmLogger.info("Input keyword " + searchString +" present")
                responseDict.setdefault(searchString,"Success. Check the output for order related logs.")
                inquiryList.append(searchString)
            else:
                self.lmLogger.info("Input keyword " + searchString +" NOT present. Verify the order input.")
                responseDict.setdefault(searchString,"Failure. The input keyword " + searchString + " passed is not found in the input file. Verify and try again.")


        if (not exclusionList):
            self.lmLogger.debug("Running the Log Manager without exclusion list")
        # else:
        #     self.lmLogger.info("Running the Log Manager for the pass number " + passNum)

        if(len(inquiryList) == 0):
            outputFile=None
            return responseDict, outputFile, outFileNameAppendString


        self.lmLogger.info("Starting association inquiry for the input order info")
        self.lmLogger.info(inquiryList)


        for index in range(len(inquiryList)):
            self.addFinalKeyWord(inquiryList[index])

        queuePointer = 0
        while (True):
            if (len(self.finalKeyWordQueue) >= 1):
                if (queuePointer <= len(self.finalKeyWordQueue) - 1):
                    self.addAssociatedKeywords(self.finalKeyWordQueue[queuePointer], exclusionList)
                if (queuePointer != 0 and queuePointer >= len(self.finalKeyWordQueue) - 1):
                    # all the keywords have been investigated
                    break
                else:
                    # increment queuePointer to investigate all the keywords
                    queuePointer += 1

        self.lmLogger.info("\n\nLog Manager has analyzed the logs for the input information passed. Writing the analyzed log output to the file.\n\n")

        if(not writeInSingleFile):
            outFileNameAppendString = searchString

        if(not outFileNameAppendString):
            if(writeInSingleFile):
                dateTime_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                # the append string is not passed. Put the default date/time since more than one orders are investigated
                if(len(inquiryList) == 1):
                    outFileNameAppendString = searchString
                else:
                    outFileNameAppendString = dateTime_str
                pass
            else:
                outFileNameAppendString = searchString

        outputFile = self.fetchLogData(passNum, outFileNameAppendString)

        # remove the thread id names before building the tree
        self.cleanUpKeyWordQueue()

        #Get the unique root ids such as order for provisioning order / task for discovery task
        self.getUniqueRootIds()

        # Write the unique order/ task to a output file

        return responseDict, outputFile, outFileNameAppendString
