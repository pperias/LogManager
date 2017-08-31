#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import datetime
import os
import logging
import shutil, stat
import zipfile
import tarfile
import time
import linecache
import sys
import json
import re

__author__ = "Julio Colon, Priya Periaswamy"

"""
    FileManager class consists of all the functions responsible for file access
"""

class FileManager(object):
    def __init__(self, appConfig, regexMgr, lmLogr):
        self.lmLogger = lmLogr
        self.data_directory = appConfig['Data_Directory']
        self.download_directory = appConfig['Download_Directory']
        self.output_directory = appConfig['Output_Directory']
        self.log_folder = appConfig['log_folder']
        self.write_metaDBList_file = appConfig['debug_metaDBList_file']
        self.write_keywordDict_file = appConfig['debug_keywordDict_file']
        self.write_log_metaDb_output_file = appConfig['debug_log_metaDb_output_file']
        self.write_log_output_complete_file = appConfig['write_log_output_complete_file']
        self.write_log_output_userSpecified_file = appConfig['write_log_output_userSpecified_file']
        self.write_tree_output_file = appConfig['write_tree_output_file']
        self.write_orderKeys_file = appConfig['write_orderKeys_file']
        self.log_output_individualSvc = appConfig['log_output_individualSvc']
        self.write_log_output_indSvc = appConfig['write_log_output_indSvc']
        self.write_log_output_Step = appConfig['write_log_output_Step']
        self.controllerSvc_str = "controllersvc"
        self.relationshipKw_regex = appConfig['queued_state_regex']
        self.regexManager = regexMgr
        self.create_Data_Directory()
        self.userConfig = None

    def setUserConfig(self, userConfig):
        self.userConfig = userConfig


    def get_parent_dir_location(self):
        src_dir = os.path.dirname(__file__)
        return src_dir

    def get_dir_file_location(self, filename):
        return os.path.join(self.get_parent_dir_location(), filename)

    """
    Create_Data_Directory function creates the data directory which is a placeholder for processing logfiles
    """

    def create_Data_Directory(self):
        data_directory = self.data_directory
        if not os.path.isdir(data_directory):
            self.lmLogger.debug(str.format("Creating directory: {0}", data_directory))
            os.makedirs(self.get_dir_file_location(data_directory))
        else:
            self.lmLogger.debug(str.format("Directory '{0}' found", data_directory))

    def create_Download_Directory(self):
        download_directory = self.download_directory
        if not os.path.isdir(download_directory):
            self.lmLogger.debug(str.format("Creating directory: {0}", download_directory))
            os.makedirs(self.get_dir_file_location(download_directory))
        else:
            self.lmLogger.debug(str.format("Directory '{0}' found", download_directory))

    """
    Create_Output_Directory function creates the output directory which is a placeholder for output logfiles
    """
    def create_Output_Directory(self, outputDirectoryName):
        outDir = self.output_directory
        if outputDirectoryName:
            self.output_directory = os.path.join(outDir, outputDirectoryName)

        if not os.path.isdir(self.output_directory):
            self.lmLogger.debug(str.format("Creating directory: {0}", self.output_directory))
            os.makedirs(self.get_dir_file_location(self.output_directory))
            #os.makedirs(os.path.join(outDir, outputDirectoryName))
        else:
            pass
            #self.lmLogger.debug(str.format("Directory '{0}' found", output_directory))

    """
    GetOutputDirectory function gets the output directory
    analysis_time - time when the analysis started
    """

    def getOutputDirectory(self):
#        self.create_Output_Directory()
        return str.format("./{0}", self.output_directory)

    """
    GetDownloadDirectory function gets the download directory
    """

    def getDownloadDirectory(self, ):
        return str.format("./{0}", self.download_directory)

    """
    GetAnalysisDirectory function gets the analysis directory
    analysis_time - time when the analysis started
    """

    def getAnalysisDirectory(self, analysis_time):
        return str.format("./{0}/{1}", self.data_directory, analysis_time)

    """
    GetLogDirectory function gets the relative path of the log folder in the analysis directory
    analysisID - unique analysis id
    """

    def getLogFilePath(self, analysisID):
        #return str.format("{0}/{1}", self.GetAnalysisDirectory(analysisID), self.log_folder)
        logFileList=[]
        for root, directories, filenames in os.walk(self.getAnalysisDirectory(analysisID)):
            for filename in filenames:
                logFileList.append(os.path.join(root,filename))

        return logFileList
                #print(os.path.join(root,filename))

    """
    create_Analysis_Directory function creates the analysis directory
    """

    def create_Analysis_Directory(self):

        analysis_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        os.makedirs(self.getAnalysisDirectory(analysis_time))
        os.chmod(self.getAnalysisDirectory(analysis_time), 0o755)
        self.lmLogger.debug(str.format('Created directory path {0} for analysis', analysis_time))
        return analysis_time

    """
    ImportZipFile function creates the analysis directory and imports the log files from zip file
    analysisID - unique analysis id
    zipFilename - zipFilename passed in the input
    """

    def importZipFile(self, analysisID, inputFile):

        #self.metaDB.print()
        start_time= time.time()
        self.lmLogger.debug("Importing input file")
        exception = False
        isTarFile = False
        isZipFile = False
        try:

            if(zipfile.is_zipfile(inputFile)):
                self.lmLogger.debug("The file that was input is a zipfile")
                sourceZip = zipfile.ZipFile(inputFile, 'r')

                for name in sourceZip.namelist():
                    # will look for only the .log files
                    if name.find('.log') != -1:
                        sourceZip.extract(name, self.getAnalysisDirectory(analysisID))
                sourceZip.close()
                isZipFile = True
        except:
            exception = True

        try:
            if(tarfile.is_tarfile(inputFile)):
                tfile = tarfile.open(inputFile)
                member= tfile.getmembers()
                names=tfile.getnames()
                for name in names:
                    # will look for only the .log files
                    if name.find('.log') != -1:
                        tfile.extract(name, self.getAnalysisDirectory(analysisID))

                #tfile.extractall(self.GetAnalysisDirectory(analysisID),members=[name for name in names if name.find('.log') != -1])
                tfile.close()
                isTarFile = True
        except Exception as strerror:
            exception = True
            self.lmLogger.debug("Exception encountered %s",strerror)
        if(not(isZipFile or isTarFile) or exception ):
            try:
                shutil.copy(inputFile,self.getAnalysisDirectory(analysisID))
            except IOError as strerror:
                self.lmLogger.info("I/O error: %s",strerror)
                exit(0)
            except:
                self.lmLogger.info("Unexpected error:", sys.exc_info()[0])
                exit(0)

    """
    GetPathToLogFiles function gets the relative path to log files in the analysis directory
    analysisID - unique analysis id
    """

    def getPathToLogFiles(self, analysisID):
        self.lmLogger.debug("Retrieving the path to log filenames from analysis directory")
        logFilesWithPath = self.getLogFilePath(analysisID)
        self.lmLogger.debug("The full path path to log filename from analysis directory %s", logFilesWithPath)
        return logFilesWithPath

    """
     clearLogs function clears the data directory
    """

    def clearLogs(self):
        self.lmLogger.debug("Clearing log and data directory")
        #shutil.rmtree(self.data_directory)
        for folder in os.listdir(self.data_directory):
            folder_path = os.path.join(self.data_directory, folder)
            try:
                if os.path.isfile(folder_path):
                    os.unlink(folder_path)
                elif os.path.isdir(folder_path):
                    shutil.rmtree(folder_path)
            except Exception as e:
                print(e)

    """
     lm_getline function gets the line from the file
     thefilepath - filepath to get the line from
     startLineNumber - start line number
     endLineNumber - endLineNumber
    """
    def lm_getline(self, thefilepath, startLineNumber, endLineNumber):
        lines_str = ""
        startLineNumberPlaceHolder = startLineNumber
        while(startLineNumber <= endLineNumber):
            line = linecache.getline(thefilepath, startLineNumber)
            lines_str = lines_str + line
            startLineNumber+=1
        if((" controllersvc " in lines_str) and startLineNumberPlaceHolder < endLineNumber):
            checkInput = re.search("WorkflowService.java", lines_str)
            if(checkInput):
                lines_str = lines_str.replace('\n', ' ')
                lines_str = lines_str.replace('\r', '')
                return lines_str + "\n"
            else:
                return lines_str
        else:
            return lines_str

    """
    writeLogInfoToOutput function is the actual output function used to write the output log file
    metaDBList - the metaDBList to write - this list is the order relationship
    passNum - the investigated pass num
    searchString - the searchString to name the output file
    """

    def writeLogInfoToOutput(self, metaDBList, passNum, searchString):

        try:
            start_time= time.time()
            type=".txt"
            searchString = self.regexManager.replaceSpecialCharacters(searchString)
            if(int(passNum) > 0):
                #suffix="_"+searchString + "_Pass_" + passNum + type
                suffix="_" + searchString + type
            else:
                suffix="_"+searchString + "_NoExclusions" + type
            regular_outputFileName = self.getOutputDirectory() + "/" +self.write_log_output_complete_file + suffix

            userSpecifiedServiceLogsToOutputFlag = False
            userServiceLogsToOutputValues = []
            defaultIndSvcsLogs = False
            indFnDict = {}

            """
             The following was added for the usecase where given the unique order details such as order number, order ID,
             Task ID, OP-ID, Workflow ID and Step ID, need ability for user to be able to
             select only the required logs files that needs to be chronologically order and sorted based on timestamp in the output file.
            """
            if self.userConfig and "ServiceLogsToOutput" in self.userConfig and self.userConfig['ServiceLogsToOutput']:
                userServiceLogsToOutputValues = self.userConfig['ServiceLogsToOutput']
                userServiceLogsToOutputValues = [temp for temp in userServiceLogsToOutputValues if temp != "None"]
                if userServiceLogsToOutputValues:
                    userSpecifiedServiceLogsToOutputFlag = True
                    userSelected_outputFileName = self.getOutputDirectory() + "/" + self.write_log_output_userSpecified_file + suffix
                    userSelected_writeFilename = open(userSelected_outputFileName, 'w')

            if self.log_output_individualSvc and self.write_log_output_indSvc:
                defaultIndSvcsLogs = True
                for eachSvc in self.log_output_individualSvc:
                    write_log_output_indSvc_eachSvc = self.getOutputDirectory() + "/" + self.write_log_output_indSvc + "_" + eachSvc + "_Output"+suffix
                    #self.lmLogger.debug("creating individual log files")
                    write_log_output_indSvc_fn_eachSvc = open(write_log_output_indSvc_eachSvc, 'w')
                    indFnDict[eachSvc] = write_log_output_indSvc_fn_eachSvc

            self.lmLogger.debug("creating output file" + regular_outputFileName)
            rglr_writeFilename = open(regular_outputFileName, 'w')
            self.lmLogger.debug("length of metadblist in FileManager" + str(len(metaDBList)))
            try:
                for eachMetaRow in metaDBList:
                    startLine = eachMetaRow.startline
                    endLine = eachMetaRow.endline
                    lineString = self.lm_getline(eachMetaRow.filename, startLine, endLine)
                    nodeId, serviceName = self.regexManager.getNodeAndServiceNameFromLine(lineString)
                    if not serviceName:
                        lfname = os.path.basename(os.path.normpath(eachMetaRow.filename))
                        if("." in lfname):
                            index_of_dot = lfname.index('.')
                            file_name_without_extension = lfname[:index_of_dot]
                        else:
                            file_name_without_extension = lfname


                        serviceName = file_name_without_extension

                    rglr_writeFilename.write(lineString)
                    if userSpecifiedServiceLogsToOutputFlag and serviceName in userServiceLogsToOutputValues:
                        userSelected_writeFilename.write(lineString)
                    if defaultIndSvcsLogs and serviceName in self.log_output_individualSvc and serviceName in indFnDict:
                            writeFilename_indFlnm = indFnDict[serviceName]
                            writeFilename_indFlnm.write(lineString)

            except OSError as err:
                print("OS error: {0}".format(err))

            except:
                print("Unexpected error:", sys.exc_info()[0])
            finally:

                rglr_writeFilename.close()
                if userSpecifiedServiceLogsToOutputFlag and serviceName in userServiceLogsToOutputValues:
                    userSelected_writeFilename.close()
                if defaultIndSvcsLogs:
                    for eachSvc in self.log_output_individualSvc:
                        writeFilename_indFlnm = indFnDict[eachSvc]
                        writeFilename_indFlnm.close()
                self.lmLogger.debug("--- time to write to output file is %s seconds ---" % round(time.time() - start_time))
                return regular_outputFileName
        except IOError:
            print("Error: while writing to the output file")
            return None

    """
    getoperationDetails function gets the operationName and the associated status with messages from the dictionary
    node - the node to get the details from
    id_opname_dict - The dictionary that has the WorkflowDetail objects (with operation values)
    """
    def getoperationDetails(self, id_opname_dict, node):
        operationNameStr = ""
        if node in id_opname_dict:
            if(id_opname_dict[node].operationName.strip() or id_opname_dict[node].state.strip() or id_opname_dict[node].elapsedTime.strip()):
                operationNameStr = operationNameStr + "  -->  "

            if(id_opname_dict[node].operationName.strip()):
                operationNameStr = operationNameStr + "opName = " + str(id_opname_dict[node].operationName.strip())

            if(id_opname_dict[node].state.strip()):
                operationNameStr = operationNameStr + ", status = " + str(id_opname_dict[node].state.strip())
                if(id_opname_dict[node].state.strip().lower() != "success"):
                    if(id_opname_dict[node].message.strip() != ""):
                        operationNameStr = operationNameStr + ", message = " + str(id_opname_dict[node].message.strip())
                    else:
                        operationNameStr = operationNameStr + ", message = " + str(id_opname_dict[node].oprDetailDesc.strip())

            if(id_opname_dict[node].elapsedTime.strip()):
                operationNameStr = operationNameStr + ", elapsedTime = " + str(id_opname_dict[node].elapsedTime.strip())


        return operationNameStr

    """
    writeTupleValues function is a convenience function that is used to write the tuple values in the tree to a txt file
    node - the node that is investigated for children
    plusCounter - prints the '+' character in the text file to denote the level
    writeFilename - the filename to write to
    """
    def writeTupleValues(self, id_opname_dict, node, plusCounter, writeFilename):
        returnVal = None
        for i in range(plusCounter):
            #print("+", end="", file = writeFilename)
            writeFilename.write("+")
        #print(node[0] + " <--> "+ node[1], file = writeFilename)
        operationNameStr = ""
        prefixStr = None
        counter=0

        for eachTupleVal in node:
            #opId = self.regexManager.checkOpIdRegex(eachTupleVal)
            #returnVal = eachTupleVal
            if eachTupleVal in id_opname_dict:
                returnVal = eachTupleVal
                operationNameStr = " <==> "+  eachTupleVal + self.getoperationDetails(id_opname_dict, eachTupleVal)

            else:
                if(not prefixStr):
                    prefixStr = eachTupleVal
                else:
                    prefixStr = prefixStr + ", " + eachTupleVal


        writeFilename.write(prefixStr + operationNameStr+ "\n")

        return returnVal

    """
    recursiveChildren function is a convenience function that is used to write the tree to a txt file
    kwTree - the dict where the parent/child relationship is outlined
    node - the node that is investigated for children
    plusCounter - prints the '+' character in the text file to denote the level
    writeFilename - the filename to write to
    """

    def recursiveChildren(self, kwTree, id_opname_dict, node, plusCounter, writeFilename):
        tupleValue = False
        if(node in kwTree.keys()):
            results = kwTree[node]

            if len(results) > 0:
                for child in results:
                    # if this is tuple then it should be orderNum and orderId combo
                    # or taskId op_id combo
                    if(isinstance(child, tuple)):
                        tupleValue = True
                        child_ret = self.writeTupleValues(id_opname_dict, child, plusCounter, writeFilename)
                        if(not child_ret):
                            for eachTupleVal in child:
                                if eachTupleVal in kwTree.keys():
                                    child = eachTupleVal
                                    break
                        else:
                            child = child_ret


                    if(not tupleValue):
                        for i in range(plusCounter):
                            #print("+", end="", file = writeFilename)
                            writeFilename.write("+")
                        #print(child,  file = writeFilename)
                        if(child in id_opname_dict):
                            operationNameStr = self.getoperationDetails(id_opname_dict, child)
                            writeFilename.write(child + operationNameStr + "\n")
                        else:
                            writeFilename.write(child + "\n")
                    plusCounter += 1
                    self.recursiveChildren(kwTree, id_opname_dict, child, plusCounter, writeFilename)
                    plusCounter -= 1

        return True
    """
    getOutFileName function is a convenience function that is used to write to a txt file
    orderInfoString - The string which was used to analyze the log files. This is for naming the tree output file
    """
    def getOutFileName(self, orderInfoString, filenameString):
        type = ".txt"
        searchString = self.regexManager.replaceSpecialCharacters(orderInfoString)
        suffix = "_"+ searchString + type
        outputFileName = self.getOutputDirectory() + "/" + filenameString + suffix
        return outputFileName

    """
    writeTreeToFile function is the output function used to write the tree to a txt file
    kwTree - the dict where the parent/child relationship is outlined
    orderInfoString - The string which was used to analyze the log files. This is for naming the tree output file
    """

    def writeOrderTreeToFile(self, kwTree, id_opname_dict, orderInfoString):
        outputFileName = self.getOutFileName(orderInfoString, self.write_tree_output_file)
        writeFilename = open(outputFileName, 'w')

        startingPoint = "root"
        plusCounter = 0

        self.recursiveChildren(kwTree, id_opname_dict, startingPoint, plusCounter, writeFilename)

        writeFilename.close()
        return outputFileName

    """
    writeOpIdandStepsToFile2 function writes the output related to steps in a log file
    metaDBList - the metadb list to write
    searchString - filename string
    """
    def writeOpIdandStepsToFile(self, metaDBList, searchString):
        type=".txt"
        opidstepDict={}
        outputStepFolderName = "steps_logs"
        self.steps_output_directory = os.path.join(self.getOutputDirectory(), outputStepFolderName)

        if not os.path.isdir(self.steps_output_directory):
            self.lmLogger.debug(str.format("Creating directory: {0}", self.steps_output_directory))
            os.makedirs(self.get_dir_file_location(self.steps_output_directory))


        searchString = self.regexManager.replaceSpecialCharacters(searchString)
        suffix = "_" + searchString + type
        outputFileName = self.steps_output_directory + "/" + self.write_log_output_Step + suffix
        # TODO: if the file already exists with the same name. no need to write. the contents would not change
        if(os.path.isfile(outputFileName)):
            self.lmLogger.info("The output file name " + outputFileName + " already exists.")
            return

        try:
            writeFilename = open(outputFileName, 'w')
        except (OSError, IOError) as e:
            if(len(searchString) > 70):
                searchString = searchString[0:28] + searchString[-70:]
            else:
                searchString = searchString[0:28]

            outputFileName = self.steps_output_directory + "/" + self.write_log_output_Step + "_" + searchString + type
            try:
                writeFilename = open(outputFileName, 'w')
            except (OSError, IOError) as e:
                self.lmLogger.info("The output file name " + outputFileName + " could not be created. The input filename might be too long. Shorten the input filename that is used and try again.")
                return
        for eachMetaRow in metaDBList:
            lineString = self.lm_getline(eachMetaRow.filename, eachMetaRow.startline, eachMetaRow.endline)
            nodeId, serviceName = self.regexManager.getNodeAndServiceNameFromLine(lineString)
            if not serviceName:
                lfname = os.path.basename(os.path.normpath(eachMetaRow.filename))
                if("." in lfname):
                    index_of_dot = lfname.index('.')
                    file_name_without_extension = lfname[:index_of_dot]
                else:
                    file_name_without_extension = lfname


                serviceName = file_name_without_extension

            if serviceName == self.controllerSvc_str:
                writeFilename.write(lineString)
        writeFilename.close()

    """
    writeKeywordListToFile function writes the keyword list to a text output file. This is a debug function.
    keywordList - the keyword list to write
    """

    def writeFinalKeywordListToFile(self, keywordList, orderInfoString):
        # TODO: write the list to file
        outputFileName = self.getOutFileName(orderInfoString, self.write_orderKeys_file)
        writeFilename = open(outputFileName, 'w')

        for eachValue in keywordList:
            writeFilename.write(eachValue + "\n")

        writeFilename.close()
        """
    writeMetaRowToFile function is a debug function used to write the metaDBList to a text output file. This is a debug function.
    metaDBList - the metaDBList to write
    out - boolean value
    """

    def writeMetaRowToFile(self, metaDBList, passNum, out):
        self.lmLogger.debug("Writing the rows in MetaDB to file")
        self.lmLogger.debug("length of metaDB list %s",len(metaDBList))
        type=".txt"
        if out:
            outputMetaDBFileName = self.getOutputDirectory() + "/" + self.write_log_metaDb_output_file + "_Pass" + str(passNum) + type
        else:
            outputMetaDBFileName = self.getOutputDirectory() + "/" + self.write_metaDBList_file + type

        writeFilename = open(outputMetaDBFileName, 'w')


        for eachMetaRow in metaDBList:
            writeFilename.write(str(eachMetaRow.timestamp) + " , " + eachMetaRow.filename + " , " + str(eachMetaRow.startline) + " , " + str(eachMetaRow.endline) + " , " + str(eachMetaRow.keywords) +"\n")

        writeFilename.close()

    """
    writeDictToFile function is a debug function used to write the keyword dictionary to a text output file. This is a debug function.
    keywordDict - the keyword dict to write
    """

    def writeDictToFile(self, keywordDict):
        self.lmLogger.debug("Writing the keyword dictionary to file")
        outputDictFileName = self.getOutputDirectory() + "/" + self.write_keywordDict_file
        writeFilename = open(outputDictFileName, 'w')
        for key,val in keywordDict.items():
            writeFilename.write(key + "=>" + str(val) +"\n")

        writeFilename.close()





