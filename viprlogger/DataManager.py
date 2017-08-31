#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import logging
import os
import fileinput
import time
import sys

from MetaDB import MetaDB
from MetaDB import MetaRow


__author__ = "Julio Colon, Priya Periaswamy"

"""
    DataManager class consists of all the functions responsible for data access
"""

class DataManager(object):

    """
    Contructor which is responsible for the data operations
    """
    def __init__(self, appConfig, fileMgr, regexMgr, lmLgr):
        self.lmLogger = lmLgr
        self.metaDB = MetaDB()
        self.fileManager = fileMgr
        self.regexManager = regexMgr
        self.keywordDict = {}

    def createCustomer(self):
        self.metaDB = MetaDB()

    def getMetaDB(self):
        return self.metaDB

    def addAnalysisToCustomer(self, customer):
        self.lmLogger.debug("Adding customer to db.")

    """
    findFileNameString function gets the filename of the log file that is currently parsed
    file - the file that is parsed to build the metaDB
    """
    def findFileNameString(self, file):
        filename = os.path.splitext(os.path.basename(file))[0].__str__().split('.')
        fileString = filename[1] + " " + filename[0]
        print(fileString)
        return fileString

    """
    ImportLogFiles function process the ilog files to build hte metaDB
    analysisId - the analysisId that is uniquely created
    logFilenames - the logfiles passed in the zip file
    """
    def importLogFiles(self, analysisId, logFilenames):

        if(os.name == 'posix'):
            import resource

        self.lmLogger.info("Building associations from the given log files... Check the ViPR Log Manager log (ViPRLogManager.log), "
                           "to see which input log file is being analysed. ")
        start_time= time.time()
        for logfile in logFilenames:
            logfilename = os.path.splitext(logfile)
            lfname = None
            suffix = None
            if(len(logfilename) > 0):
                lfname = os.path.basename(os.path.normpath(logfilename[0]))
            if(len(logfilename) >= 1):
                suffix = logfilename[1]

            # if(os.name == 'posix'):
            #     self.lmLogger.info("Memory usage (in MB): " + str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000))

            self.lmLogger.debug("Working on the log file: "+ lfname + suffix)

            # initialization
            endLineNumber = startLineNumber = 0
            date=""
            keywordsToWrite=[]
            negateAssociationFlagMRow = False
            #fileString = self.findFileNameString(logfile)
            for line in fileinput.input(logfile):

                #get the keywords for the current line that is read
                keywords, negateAssociationFlag = self.regexManager.getKeywordsForLine(line)
                dateFromLine = self.regexManager.getDateFromLine(line)


                # if date is  present then it is a new line
                if (not dateFromLine == ""):
                    #if this is not a first line then this is a new line where the fileString is found. So go ahead and store the start and end line numbers
                    if (not fileinput.isfirstline() and (len(keywordsToWrite) > 0) and date != "" ):
                        """
                            The -if- condition ensures that we have looked the earlier lines for new line with file string. If first line then we should continue until we find the next fileString
                            write start line and end line.
                        """

                        metaRow = MetaRow(date, fileinput.filename(), startLineNumber, endLineNumber, negateAssociationFlagMRow, list(set(keywordsToWrite)))
                        self.metaDB.InsertData(metaRow)
                        lastInd=self.metaDB.getLastIndexFromMetaDB()
                        for eachKeyword in keywordsToWrite:
                            self.keywordDict.setdefault(eachKeyword, list()).append(lastInd)

                    #reset the keywordsToWrite for next block
                    keywordsToWrite=[]
                    negateAssociationFlagMRow = False

                    #This is the line number of the new line
                    endLineNumber = startLineNumber = fileinput.filelineno()
                    #get the date here, not earlier since this is the new line
                    date = self.regexManager.getDateFromLine(line)

                    #reset the list of keywords for the new block
                    keywordsToWrite+=keywords
                    # logical or on the negate flag
                    negateAssociationFlagMRow = negateAssociationFlagMRow or negateAssociationFlag

                else:
                    #the line is continuation of previous line so keep reading file
                    endLineNumber = fileinput.filelineno()
                    #save the read keywords
                    keywordsToWrite+=keywords
                    negateAssociationFlagMRow = negateAssociationFlagMRow or negateAssociationFlag
            else:
                #this is the last line
                if (len(keywordsToWrite) > 0 and date != "") :
                    metaRow = MetaRow(date,fileinput.filename(),startLineNumber,endLineNumber,negateAssociationFlagMRow, list(set(keywordsToWrite)))
                    self.metaDB.InsertData(metaRow)
                    lastInd=self.metaDB.getLastIndexFromMetaDB()
                    for eachKeyword in keywordsToWrite:
                        self.keywordDict.setdefault(eachKeyword,list()).append(lastInd)

                #reset the keywordsToWrite for next block
                keywordsToWrite=[]
                negateAssociationFlagMRow = False
                fileinput.close()

        self.lmLogger.debug("--- time to parse and build associations is %s seconds ---" % round(time.time() - start_time))
        self.lmLogger.debug("Total number of metarow (input log file - lines containing keywords) " + str(len(self.metaDB.tagsList)))
        self.lmLogger.debug("Total number of unique keywords " + str(len(self.keywordDict)))
        self.lmLogger.debug("keyword dict size (in KB): "+str(sys.getsizeof(self.keywordDict)/1024))
        self.lmLogger.debug("self.metaDB.tagsList size (in KB): "+str(sys.getsizeof(self.metaDB.tagsList)/1024))
        if(os.name == 'posix'):
            self.lmLogger.debug("Memory usage after making the associations (in MB): " + str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000))
        #self.fileManager.writeMetaRowToFile(self.metaDB.tagsList,'out', False)

        #self.fileManager.writeDictToFile(self.keywordDict)




