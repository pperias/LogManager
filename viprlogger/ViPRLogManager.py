#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""

import json
import logging
import sys
import time
import os
from DataManager import DataManager
from FileManager import FileManager
from RegExManager import RegExManager
from LogInquirer import LogInquirer
from BuildOrderTree import BuildOrderTree

__author__ = "Priya Periaswamy"

"""
    ViPRLogManager class is responsible for processing the log files and getting the log data for the order info passed
"""


class ViPRLogManager(object):
    def __init__(self):
        self.lmLogger = logging.getLogger("ViPRLogManager")
        self.analysisDir = "."
        self.lmLogger.setLevel(logging.DEBUG)
        logManagerFileName = "ViPRLogManager.log"
        logFileLocation = os.path.join(self.analysisDir, logManagerFileName)
        # create file handler which logs even debug messages
        fileHandler = logging.FileHandler(logFileLocation, mode='a')
        fileHandler.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        FORMAT = "%(asctime)s - %(name)s:%(module)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(FORMAT)
        fileHandler.setFormatter(formatter)
        consoleHandler.setFormatter(formatter)
        # add the handlers to the logger
        self.lmLogger.addHandler(fileHandler)
        self.lmLogger.propagate = False
        self.lmLogger.addHandler(consoleHandler)

        self.lmLogger.info("ViPR Log Manager 1.2")
        self.appConfig =  self.readFile("applicationConfig.json")

        self.exclusion_list = self.readFile("exclusionList.json")
        self.regexManager = RegExManager(self.appConfig, self.lmLogger)
        self.fileManager = FileManager(self.appConfig, self.regexManager, self.lmLogger)
        self.dataManager = DataManager(self.appConfig, self.fileManager, self.regexManager, self.lmLogger)
        self.logInquirer = LogInquirer(self.appConfig, self.fileManager, self.dataManager, self.lmLogger)

        self.userConfig = None


    def get_parent_dir_location(self):
        src_dir = os.path.dirname( __file__ )
        return src_dir


    def get_file_location(self, filename):
        return os.path.join(self.get_parent_dir_location(), filename)

    """
    getDownloadDirectory function gets the download directory
    """
    def getDownloadDirectory(self):
        self.fileManager.create_Download_Directory()
        return self.fileManager.getDownloadDirectory()

    """
    read_configuration function reads the jason configuration file into memory
    """

    def readFile(self, fileName):
        try:
            fileHandle = open(self.get_file_location(fileName), 'r')
            readFile_raw = fileHandle.read()
            self.lmLogger.debug(fileName + ":\n" + readFile_raw)
            fileContentsList = json.loads(readFile_raw)
        except IOError:
            self.lmLogger.error("Error: can\'t find file "+ fileName +" or read data. Make sure a valid path to the file is passed.")
        else:
            fileHandle.close()
            return fileContentsList

    def readUserConfig(self, userConfigFile):
        self.userConfig = self.readFile(userConfigFile)
        self.fileManager.setUserConfig(self.userConfig)

    """
    createAnalysis function imports the zip file passed in the function and creates a unique analysis ID
    """
    # @profile
    def createAnalysis(self, importFile):
        start_time = time.time()
        analysisID = self.fileManager.create_Analysis_Directory()  # Create directory for analysis
        #TODO: remove the following for visualizer. The output need to present in the analysis folder
        filenamepath = os.path.splitext(importFile)
        outputDir = os.path.basename(os.path.normpath(filenamepath[0]))
        self.fileManager.create_Output_Directory(outputDir + "_" + analysisID)


        self.fileManager.importZipFile(analysisID, importFile)  # Import Zip files
        logfilenames = self.fileManager.getPathToLogFiles(analysisID)  # Get log filenames

        self.dataManager.importLogFiles(analysisID,
                                        logfilenames)  # Import each file into the db manager for later analysis

        #print("Total time for running --- %s seconds ---" % round(time.time() - start_time))
        self.lmLogger.debug("total time taken for extracting the file and building association is %s seconds", round(time.time() - start_time))

        return analysisID  # return the id for the analysis for future reference.
    """
    logInquireOutputAction function investigates the output of the logInquirer.getLogData and decides whether the call was successful or not
    """

    def logInquireOutputAction(self, passNum, outputFile, outFileNameAppendString):
        # build tree for each orderInfo
        logInquireStatus = False
        numUniqueIds = len(self.logInquirer.getUniqueOrderIdAndTasks())
        if( numUniqueIds > 0 and int(passNum) == 1):
            logInquireStatus = True
            # build the tree and write to the text file
            self.lmLogger.info("Log Manager is writing the tree to the file.\n")

            treeStatus = self.buildOrderInfoTree(outputFile, outFileNameAppendString)
            if(not treeStatus):
                self.lmLogger.info("\n\nThe tree could not be build. Please check if the correct order info is passed.\n\n")

        else:
            logInquireStatus =  False
            self.lmLogger.info("\n\nThe tree could not be build. The input info is not associated with a task / order.\n\n")
            treeStatus = self.buildOrderInfoTree(outputFile, outFileNameAppendString)

        return logInquireStatus




    """
    fetchLogInfo function fetches the log info for the order info passed
    inputKeyword - order info passed such as order number/ order id / task id
    passNum - pass number
    exclusion_list - user defined exclusion list
    """

    def fetchLogInfo(self, inputOrderDict, passNum, exclusion_list):
        # Pass the orderNumber and the pass number
        passNumExist=False
        logInquireStatusFinal = True
        if(exclusion_list != "False"):
            # exclusion list is passed in the input. Use that rather than the default
            self.exclusion_list = self.readFile(exclusion_list)

        if(self.exclusion_list):
            if(passNum not in self.exclusion_list and int(passNum) != 0):
                passNum = "1"

            if(int(passNum) == 0):
                # Somebody are really serious about getting the LM run without exclusion list
                exclusion_list_to_use=[]
            else:
                exclusion_list_to_use = self.exclusion_list[passNum]

            if(inputOrderDict.get("writeInSingleFile")):
                logInquireStatusDict, outputFile_allOrders, outFileNameAppendString_allOrders = self.logInquirer.getLogData(inputOrderDict.get("orderInfoList"),
                                                                                     inputOrderDict.get("writeInSingleFile"),
                                                                                     inputOrderDict.get("fileNameAppendString"),
                                                                                     passNum, exclusion_list_to_use)
                logInquireStatus = self.printResultDict(logInquireStatusDict)
                if logInquireStatus:
                    logInquireStatus = self.logInquireOutputAction(passNum, outputFile_allOrders, outFileNameAppendString_allOrders)
                logInquireStatusFinal = logInquireStatus and logInquireStatusFinal

            else:
                ordInfoList = inputOrderDict.get("orderInfoList")
                for eachOrder in range(len(ordInfoList)):
                    eachOrderList = []
                    eachOrderList.append(ordInfoList[eachOrder])
                    logInquireStatus, outputFile_eachOrder, outFileNameAppendString_eachOrder = self.logInquirer.getLogData(eachOrderList,
                                                                                     inputOrderDict.get("writeInSingleFile"),
                                                                                     inputOrderDict.get("fileNameAppendString"),
                                                                                     passNum, exclusion_list_to_use)
                    logInquireStatus = self.printResultDict(logInquireStatus)
                    if logInquireStatus:
                        logInquireStatus = self.logInquireOutputAction(passNum, outputFile_eachOrder, outFileNameAppendString_eachOrder)
                    logInquireStatusFinal = logInquireStatus and logInquireStatusFinal

        if(logInquireStatusFinal):
            self.lmLogger.info("\n\nLog Manager has analyzed the input information passed. Check the Output folder " + self.fileManager.getOutputDirectory().replace("\\","/") + " for log files produced.\n\n")
        else:
            self.lmLogger.info("\n\nLog Manager has analyzed the input information passed. There are problems with the orderInfo. Check the output folder " + self.fileManager.getOutputDirectory().replace("\\","/") + " and logs for more details.\n\n")





        return logInquireStatusFinal

    def printResultDict(self, logStatusDict):
        self.lmLogger.info("Result of order Info passed:")
        logInquireStatusFinal = True
        for eachKey in logStatusDict:
            self.lmLogger.info(eachKey + " --> " + logStatusDict[eachKey])
            if("Success" in logStatusDict[eachKey]):
                logInquireStatusFinal = True and logInquireStatusFinal
            else:
                logInquireStatusFinal = False and logInquireStatusFinal
        return logInquireStatusFinal


    """
    buildOrderInfoTree function builds the required tree for the passed order info
    outputLogFile - the final log output
    orderInfoString - orderInfo string that was passed
    """

    def buildOrderInfoTree(self, outputLogFile, orderInfoString):
        self.buildOrderTree_instance = BuildOrderTree(self.appConfig, self.fileManager, self.dataManager, self.logInquirer, self.lmLogger, self.regexManager)
        tree_status = self.buildOrderTree_instance.buildTreeStructure(outputLogFile, orderInfoString)
        return tree_status
    """
    inputValidation function validates the input
    commandLineOrderInfo - orderInfo from command line
    """
    def inputOrderInfoValidation(self, commandLineOrderInfo):
        # If the orderInfo is not passed in command line, default is False
        user_OrderInfoDict = {}
        userOrderInfoList=[]
        writeToSameFile = True
        fnAppendString = None

        if commandLineOrderInfo == "False":
            # check if the orderInfo is present in the userConfig
            if self.userConfig and "orderInfo" in self.userConfig:
                if "orderInfoList" in self.userConfig["orderInfo"]:
                    userOrderInfoList = self.userConfig["orderInfo"].get("orderInfoList")
                    userOrderInfoList = [temp for temp in userOrderInfoList if temp != "None"]
                    userOrderInfoList = [temp.strip() for temp in userOrderInfoList if temp.strip() != ""]

                if "writeInSingleFile" in self.userConfig["orderInfo"]:
                    writeToSameFile_readValue = self.userConfig["orderInfo"].get("writeInSingleFile").strip().upper()
                    if(writeToSameFile_readValue == "TRUE"):
                        writeToSameFile = True
                    else:
                        writeToSameFile = False

                if "fileNameAppendString" in self.userConfig["orderInfo"]:
                    fnAppendString = self.userConfig["orderInfo"].get("fileNameAppendString").strip()



        else:
            # If the orderInfo is passed in command line, all good
            userOrderInfoList.append(commandLineOrderInfo)

        user_OrderInfoDict.setdefault("orderInfoList",userOrderInfoList)
        user_OrderInfoDict.setdefault("writeInSingleFile", writeToSameFile)
        user_OrderInfoDict.setdefault("fileNameAppendString", fnAppendString)

        return user_OrderInfoDict



    """
    clearLogs function clears the Data folder
    """

    def clearLogs(self):
        self.fileManager.clearLogs()


if __name__ == '__main__':
    ViPRLogManager()
