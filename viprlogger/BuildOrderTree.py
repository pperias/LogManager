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
from WorkflowDetail import WorkflowDetail
from datetime import datetime




__author__ = "Priya Periaswamy"

"""
    BuildOrderTree class builds the order defining keywords as a tree

"""


class BuildOrderTree(object):

    def __init__(self, appConfig, fileMgr, dataMgr, logInquirer, lmLgr, regexMgr):
        self.lmLogger = lmLgr
        self.dataManager = dataMgr
        self.fileManager = fileMgr
        self.metaDB = self.dataManager.getMetaDB()
        self.finalKeyWordQueue = logInquirer.finalKeyWordQueue
        self.regexManager = regexMgr
        self.kwTree = logInquirer.kwTree
        self.opId_stepId_Dict = {}
        # Todo: move to config
        self.sqBracket_regex = '(?<=\[)(.+?)(?=\])'
        self.opId_regex = "(?<!:|\\w)[\\w]{8}-[\\w]*-[\\w]*-[\\w]*-[\\w]{12}(?!:|\\w)"
        self.stepId_regex = "(?<!:|\\w)[\\w]{8}-[\\w]{4}-[\\w]{4}-[\\w]{4}-[\\w]{20}-[\\w]*-[\\w]*-[\\w]*-[\\w]{12}(?!:|\\w)"
        self.threadId_regex = "^\d*(?=\|)"
        self.urn_regex = appConfig['urn_regex']


# Get the step Id and op id which is inside the square brackets
    def checkOpId_StepIdExists(self, input):
        idExists = False
        op_id=list(set(re.findall(self.opId_regex, input)))
        if(len(op_id) != 0 ):
            return True, op_id

        step_id=list(set(re.findall(self.stepId_regex, input)))
        if(len(step_id) != 0 ):
            idExists = True
            return True, step_id

        return idExists, None

    """
    getStepIdOpIdRelationship function gets the relationship between stepid and opid / stepid

    line - the line to get the relationship
    parentId - the parent id from the square brackets
    """

    def getStepIdOpIdRelationship(self, line, parentId):
        # this is a lazy way to identify relationship. But this was confirmed from the workflow service wiki
        # https://asdwiki.isus.emc.com:8443/display/OS/Workflow+Service
        # hence reading the output file and getting the lines where the steps are related to op_id or step_ids
        childStepIdVal = None
        childStepId_regex = '(?<=step:)(.+?)(?=queued state)'
        childStepId_regexGroup = re.search(childStepId_regex, str(line))
        if childStepId_regexGroup:
            childStepIdVal = childStepId_regexGroup.group().strip()

        parentExistinTree = False

        if(parentId in self.finalKeyWordQueue and childStepIdVal in self.finalKeyWordQueue):
            # add this relationship to the tree
            if(parentId not in self.kwTree.keys()):
                # investigate if the parentId is hidden inside the tuple values
                for eachList in self.kwTree.values():
                    # each value is a list which consists of tuples
                    if(parentId in eachList):
                        parentExistinTree = True
                        break
                    tempTupleTolist=[]
                    if isinstance(eachList, collections.Iterable):
                        for eachVal in eachList:
                            if(isinstance(eachVal, tuple)):
                                for j in eachVal:
                                    tempTupleTolist.append(j)
                                #tempTupleTolist = [i for sub in eachVal for i in sub]
                            #tempTupleTolist.append(eachVal)
                            else:
                                tempTupleTolist.append(eachVal)

                    #tempTupleTolist = [i for sub in eachListVal for i in sub]
                    if(parentId in tempTupleTolist):
                        parentExistinTree = True
                        break
                    else:
                        parentExistinTree = False
            else:
                parentExistinTree = True

            # if the parent is not in the kwTree then this should be tagged as the root
            if(not parentExistinTree):
                root = "root"
                self.kwTree.setdefault(root, list()).append(("WorkflowTaskId", parentId))
            self.kwTree.setdefault(parentId, list()).append(childStepIdVal)


        return True

    """
    Convert the string date to date object for sorting. This code can be used if we want the uniform timestamps (for start and end time)
    Commenting the code where convertToDateObject method is used since the occurence of time format is highly unreliable
    date - input date
    """
    def convertToDateObject(self, dateFromLine):
        # currently there are two formats that are seen in the logs such as follows:
        # Format 1:
        # started: Wed Sep 23 10:37:25 UTC 2015 completed: Wed Sep 23 10:37:25 UTC 2015 elapsed: 0 ms
        # Format 2:
        # vipr5 controllersvc 2015-08-12 00:11:53,654 [752|zoneExportMasksDelete|ed9d0d49-0e23-45c6-9493-4ea78b05ab86b6a0885a-b50c-45a0-a669-55f939ac8660]

        # this method investigates the input date format (which is assumed to be one of the 2 formats) and converts to a date object

        converted_date_object = dateFromLine

        if(dateFromLine == ""):
            #return datetime.date(date.MINYEAR, 1, 1)
            return datetime.strptime('0001-01-01 00:00:00,000', '%Y-%m-%d %H:%M:%S,%f')

        if(isinstance(dateFromLine, datetime)):
            return dateFromLine

        try:
            return datetime.strptime(dateFromLine, '%a %b %d %H:%M:%S UTC %Y')
        except ValueError:
            self.lmLogger.debug("Date format is not of type %a %b %d %H:%M:%S UTC %Y")

        try:
            return datetime.strptime(dateFromLine, '%Y-%m-%d %H:%M:%S,%f')
        except ValueError:
                self.lmLogger.debug("Date format is not of type %Y-%m-%d %H:%M:%S,%f")

        return converted_date_object


    """
    saveWorkflowDetail function saves the workflow task detail to the dictionary

    current_workflowTask - current workflowTask to be saved (after investigation)
    """
    def saveWorkflowDetail(self, current_workflowDetail):

        workflowId = current_workflowDetail.workflowId
        if(workflowId in self.opId_stepId_Dict):
            savedWfDetail = self.opId_stepId_Dict[workflowId]
             #merge values
            #workflowId, operationName, startTime, endTime, message, state
            if(savedWfDetail.state.lower() == current_workflowDetail.state.lower()):
                pass
            if(savedWfDetail.state.lower() == ""):
                savedWfDetail.state = current_workflowDetail.state
            if(savedWfDetail.state.lower() != current_workflowDetail.state.lower() and current_workflowDetail.state.lower() != "success"):
                savedWfDetail.state = savedWfDetail.state + ", "+ current_workflowDetail.state

            if(savedWfDetail.message.lower() in current_workflowDetail.message.lower()):
                #substring of the current wflow msg
                savedWfDetail.message = current_workflowDetail.message
            elif(current_workflowDetail.message.lower() in savedWfDetail.message.lower()):
                #substring of the saved wflow msg
                pass
            else:
                savedWfDetail.message = savedWfDetail.message + " " + current_workflowDetail.message

            if(savedWfDetail.oprDetailDesc.lower() in current_workflowDetail.oprDetailDesc.lower()):
                #substring of the current wflow oprDetailDesc
                savedWfDetail.oprDetailDesc = current_workflowDetail.oprDetailDesc
            elif(current_workflowDetail.oprDetailDesc.lower() in savedWfDetail.oprDetailDesc.lower()):
                #substring of the saved wflow msg
                pass
            else:
                savedWfDetail.oprDetailDesc = savedWfDetail.oprDetailDesc + " " + current_workflowDetail.oprDetailDesc

            if(savedWfDetail.startTime != "" and current_workflowDetail.startTime != ""):
                try:
                    savedWfDetail.startTime = min(savedWfDetail.startTime, current_workflowDetail.startTime)
                except Exception as e:
                    self.lmLogger.debug("date Time not in expected format%s. ",e)
            if(savedWfDetail.startTime == ""):
                savedWfDetail.startTime = current_workflowDetail.startTime


            if(savedWfDetail.endTime != "" and current_workflowDetail.endTime != ""):
                try:
                    savedWfDetail.endTime = max(savedWfDetail.endTime, current_workflowDetail.endTime)
                except Exception as e:
                    self.lmLogger.debug("date Time not in expected format%s. ",e)
            if(savedWfDetail.endTime == ""):
                savedWfDetail.endTime = current_workflowDetail.endTime

            savedWfDetail.elapsedTime = max(savedWfDetail.elapsedTime, current_workflowDetail.elapsedTime)

        else:
            # current_workflowDetail.startTime = self.convertToDateObject(current_workflowDetail.startTime)
            # current_workflowDetail.endTime = self.convertToDateObject(current_workflowDetail.endTime)
            self.opId_stepId_Dict[workflowId] = current_workflowDetail

    """

    """

    """
    getWorfkflowTaskDetail function gets the workflow task detail from the file

    line - line to be investigated
    """

    def getWorfkflowTaskDetail(self,line):

        valid = False
        lookfor = ["Step:","state","message","started","completed"]
        for eachStr in range(len(lookfor)):
            if lookfor[eachStr] in line:
                valid = True
            else:
                valid = False
                break

        # WorkflowService.java (line 329) Step: 66980671-41dd-4cb8-a87a-fa1c934b887508859f11-e8a5-4f1d-9cd5-cedac62f022c
        # (VPlex urn:storageos:StorageSystem:6977ccd0-a1c7-43a6-9b73-feb3e09eb972: creating virtual volumes: Volume: pwdf5196_test (urn:storageos:Volume:fdc27e09-0da0-4740-9f93-741650e3efad:vdc1) )
        # state: CANCELLED message: Cancelled by step: faaa5ede-eb10-4abc-9c77-815e35ffd528945881f7-1dac-422e-b121-d3a1af96d2f2
        # started: Wed Sep 23 10:37:25 UTC 2015 completed: Wed Sep 23 10:37:25 UTC 2015 elapsed: 0 ms

        if valid:
            workflowTask_id_details = re.search('(?<=WorkflowService.java )(\(line .*Step)(.*)(?=state)',line)
            if(workflowTask_id_details):
                workflowTask_idExists, workflowTask_id = self.checkOpId_StepIdExists(workflowTask_id_details.groups()[1])
                workflowTask_operationDetDesc = workflowTask_id_details.groups()[1].replace("".join(workflowTask_id),"").strip(": ")

            workflowTask_state = self.regexManager.checkdRegex('(?<=state)(.*)(?=message)',line).strip(": ")
            workflowTask_message = self.regexManager.checkdRegex('(?<=message)(.*)(?=started)',line).strip(": ")
            workflowTask_started = self.regexManager.checkdRegex('(?<=started)(.*)(?=completed)',line).strip(": ")
            #workflowTask_completed = self.regexManager.checkdRegex('(?<=completed)(.*)',line).strip(": ")
            workflowTask_completed = self.regexManager.checkdRegex('(?<=\d completed)(.*)',line).strip(": ")
            if("elapsed" in workflowTask_completed):
                workflowTask_completed = self.regexManager.checkdRegex('(?<=\d completed)(.*)(?=elapsed)',line).strip(": ")
                workflowTask_elapsed = self.regexManager.checkdRegex('(?<=elapsed)(.*)',line).strip(": ")
            else:
                workflowTask_elapsed = ""

            # if(workflowTask_started.strip() != ""):
            #     workflowTask_started = self.convertToDateObject(workflowTask_started.strip())
            #
            # if(workflowTask_completed.strip() != ""):
            #     workflowTask_completed = self.convertToDateObject(workflowTask_completed.strip())


            for eachId in workflowTask_id:
                workflowTask_id_str = ''.join(workflowTask_id)



                #workflowId, operationDesc, startTime, endTime, message, state
                current_workflowTask = WorkflowDetail(workflowTask_id_str.strip(), "", workflowTask_started, workflowTask_completed, workflowTask_message.strip(),
                                                   workflowTask_state.strip(), workflowTask_operationDetDesc.strip(),  workflowTask_elapsed)

                # store the current_workflowTask in the dict

                self.saveWorkflowDetail(current_workflowTask)

        #WorkflowService.java (line 349) Workflow 6619dd5f-9ed1-48cb-9873-faf444ad6810
        # overall state: ERROR (The job has failed: string ErrorDescription = "The requested feature is not supported for this microcode or SYMAPI version";)

        # if the line does not have the step description, then check if it has the overall state description of the operation / step example line given above)

        workflowOverallState_Detail = re.search('(?<=WorkflowService.java )(\(line \d*\) )(Workflow .*)(overall state:.*)',line)
        if(workflowOverallState_Detail):
            workflowTask_idExists, workflowTask_id = self.checkOpId_StepIdExists(workflowOverallState_Detail.groups()[1])
            workflowTask_st_opdesc_rgx = re.search('(?<=overall state:\s)(\w*)(\s\(.*)',line)
            if(workflowTask_st_opdesc_rgx):
                workflowTask_state = workflowTask_st_opdesc_rgx.groups()[0]
                workflowTask_operationDetDesc = workflowTask_st_opdesc_rgx.groups()[1].strip()

                for eachId in workflowTask_id:
                    workflowTask_id_str = ''.join(workflowTask_id)
                    current_workflowTask = WorkflowDetail(workflowTask_id_str, "", "", "", "", workflowTask_state.strip(), workflowTask_operationDetDesc.strip() , "")
                    self.saveWorkflowDetail(current_workflowTask)


    """
    getThrd_op_step_id_opName function gets the thread id, operation name, op id and step id from the file

    outputFile - The log output generated
    """

    def getThrd_op_step_id_opName2(self, outputFile):
        self.opId_stepId_Dict = {}
        with open(outputFile) as file:
            for line in file:
                sqBracket_regexValue=re.search(self.sqBracket_regex, line)
                if(sqBracket_regexValue):
                    # the line has the threadId, operation name and the op id or step id for further investigation
                    # see if the contents between [ and ] has a op id or step id. else ignore the line and go on.
                    thId_opNm_opId_stepId = sqBracket_regexValue.group()
                    opId_StepIdExists, idReturned = self.checkOpId_StepIdExists(thId_opNm_opId_stepId)
                    if(opId_StepIdExists):
                        # thread id is in the start of the string inside the square brackets. Get the thread id while parsing the file.
                        threadId = re.findall(self.threadId_regex, thId_opNm_opId_stepId)

                        repalceStr = thId_opNm_opId_stepId

                        for eachId in idReturned:
                            idReturned_str = ''.join(eachId)
                            repalceStr = repalceStr.replace(''.join(idReturned_str),'')

                        if(len(threadId) != 0 ):
                            threadId_str = ''.join(threadId)
                            repalceStr = repalceStr.replace(threadId_str, '')

                        # TODO: Move the hard code values to config. there can be various formats of null occuring in the operation name
                        # repalceStr = repalceStr.replace("|null|", '')
                        # repalceStr = repalceStr.replace("null|", '')
                        # repalceStr = repalceStr.replace("null|", '')
                        repalceStr = repalceStr.replace("null", '')
                        repalceStr = repalceStr.replace("|", ' ')
                        operationName = repalceStr.strip()
                        # opearation name can repeat
                        if(len(operationName) > 50):
                            operationName = operationName[0:50]


                        # save the ids and the operation name in a hash table

                        for eachId in idReturned:
                            idReturned_str = ''.join(eachId)


                            if(idReturned_str in self.opId_stepId_Dict):
                                curr_opName = self.opId_stepId_Dict[idReturned_str].operationName
                                if(curr_opName != "" and operationName in self.opId_stepId_Dict[idReturned_str].operationName):
                                    pass
                                else:
                                    self.opId_stepId_Dict[idReturned_str].operationName = curr_opName + " ," + operationName
                            else:
                                #self.operationName_Dict.setdefault(idReturned_str, list()).append(operationName)
                                #startTime = ""
                                #if(self.regexManager.checkdRegex(self.opId_regex, idReturned_str)):
                                startTime = self.regexManager.getDateFromLine(line)
                                # startTime= self.convertToDateObject(startTime.strip())
                                current_workflowTask = WorkflowDetail(idReturned_str, operationName, startTime, "", "", "", "" , "")
                                self.saveWorkflowDetail(current_workflowTask)


                        # building relationship
                        # this is a lazy way to identify relationship. But this was confirmed from the workflow service wiki
                        # https://asdwiki.isus.emc.com:8443/display/OS/Workflow+Service
                        # hence reading the output file and getting the lines where the steps are related to op_id or step_ids
                            if ' queued state ' in line:
                                self.getStepIdOpIdRelationship(line, idReturned_str)

                worfkflowTaskDetail = self.getWorfkflowTaskDetail(line)

                catalogName_regexValue=re.search("(?<=NotificationManagerImpl.java)(.*\(.*\))(.*)(?=\s\(Order: urn:storageos:Order)", line)

                if catalogName_regexValue:
                    catalog_name = catalogName_regexValue.groups()[1]
                    orderId = re.search(self.urn_regex, line)
                    endTime =  self.regexManager.getDateFromLine(line)
                    # if(endTime.strip() != ""):
                    #     endTime= self.convertToDateObject(endTime.strip())
                    if(orderId):
                        orderDetail = WorkflowDetail(orderId.group(), catalog_name, "", endTime, "", "", "", "")
                        self.saveWorkflowDetail(orderDetail)
                        # self.opId_stepId_Dict.setdefault(orderId.group(), list()).append(catalog_name)




        return True



    """
    This function helps to print the tree for the orderInfo
    orderInfoString - the order info string which is used to build the output
    """
    def printTreeToFile(self, orderInfoString):
        #outputFile = self.fileManager.writeOrderTreeToFile(self.kwTree, self.operationName_Dict, orderInfoString)
        outputFile = self.fileManager.writeOrderTreeToFile(self.kwTree, self.opId_stepId_Dict, orderInfoString)

    """
    This function helps to print the steps for the orderInfo in seperate files
    outputFile - the outputFile which is used to build the output
    """
    def printOpIdandStepsToFile(self, outputFile, sortedopId_stepIdList):
        #self.fileManager.writeOpIdandStepsToFile(self.kwTree, self.opId_stepId_Dict, outputFile)
        logIndex = set([])
        logData = []

        counter = 1
        for eachKeyword in sortedopId_stepIdList:
            if(self.regexManager.checkopIdOrStepIdExists(eachKeyword) ):
                logIndex = set([])
                logData = []
                indxList = self.dataManager.keywordDict.get(eachKeyword)
                logIndex |= set(indxList)
                for eachIndex in logIndex:
                    metaRow = self.metaDB.tagsList[eachIndex]
                    logData.append(metaRow)
                # This is the only place where we sort. We do not need to sort the input since for building the
                #  associations there is no  need to sort and get the relationship.
                logData = sorted(logData, key=attrgetter("timestamp"))
                #self.fileManager.writeMetaRowToFile(logData, passNum, True)
                #filenameString = orderInfoString + "_" + eachKeyword
                filenameString = self.opId_stepId_Dict[eachKeyword].operationName.strip()
                if(filenameString != ""):
                    filenameString = str(counter) + "_" + eachKeyword + "_" + filenameString
                else:
                    filenameString = str(counter) + "_" + eachKeyword
                self.fileManager.writeOpIdandStepsToFile(logData, filenameString)
                counter += 1
        return outputFile

    """
    This function helps to print the unique keywords that are associated with the order info
    orderInfoString - the order info string which is used to build the output
    """
    def printKeywordListToFile(self, orderInfoString):
        outputFile = self.fileManager.writeFinalKeywordListToFile(self.finalKeyWordQueue, orderInfoString)

    """
    This function helps to build the tree for the orderInfo requested in the input
    outputFile - File which is used for relating the opid and stepid
    orderInfoString - the order info string which is used to build the output
    """
    def buildTreeStructure(self, outputFile, orderInfoString):

            # In this method we relate the steps and the opId / task and add to the tree

            # easiest ... check for the string 'queued state' in the generated output file, get the op_id / step ids
            # mark relationship which is parent and which is child
            # CHECK if these op_id and step_id are indeed valid ones with the finalKeywordQueue and then add to the tree

            #2nd option:
            # for the op_id, examine the meta row which has only one step_id (and this op_id)
            # for this step id, check if the line contains the string "queued state"
            # continue this until all step ids have been exhausted. when should we stop??


        getStepRelStatus = self.getThrd_op_step_id_opName2(outputFile)

        # for key in self.opId_stepId_Dict:
        #     wkflowtask = self.opId_stepId_Dict[key]
        #     print(wkflowtask.workflowId + "," + wkflowtask.operationName + ",", (wkflowtask.startTime) , "," , wkflowtask.endTime , "," + wkflowtask.message + "," + wkflowtask.state)
        #
        # print("sorted")
        # print("")
        # print("")
        try:
            tempwkflowtask_List = sorted(self.opId_stepId_Dict.values(), key=attrgetter("startTime", "endTime"))

        except:
            tempwkflowtask_List = self.opId_stepId_Dict.values()

        sortedlmList=[]
        for wkflowtask in tempwkflowtask_List:
            #print(wkflowtask.workflowId + "," + wkflowtask.operationName + "," , (wkflowtask.startTime) , "," , wkflowtask.endTime , "," + wkflowtask.message + "," + wkflowtask.state)
            self.lmLogger.debug("%s , %s, %s, %s, %s, %s",wkflowtask.workflowId ,wkflowtask.operationName , wkflowtask.startTime,  wkflowtask.endTime , wkflowtask.message , wkflowtask.state)
            sortedlmList.append(wkflowtask.workflowId)


        for key in self.kwTree:
            if(key in self.opId_stepId_Dict.keys()):
                try:
                    self.kwTree[key].sort(key=lambda x: sortedlmList.index(x))
                except Exception as e:
                    self.lmLogger.debug("Trying to sort the kwTree[key].list. error occured possibly the values not in desired form %s. " , e)
            else:
                try:
                    self.kwTree[key].sort(key=lambda x: sortedlmList.index(x[1]))
                except Exception as e:
                    self.lmLogger.debug("Trying to sort the kwTree.lst (of tuples). Exception encountered %s. ",e)


            # The values exist as tuples. Sort them as well.


        if(not getStepRelStatus):
            return False

        #Last but not least, print the traverse the tree and print the output

        printTreeFilename = self.printTreeToFile(orderInfoString)
        printopIDStepsStatus = self.printOpIdandStepsToFile(outputFile, sortedlmList)

        #Print the keyword list to a file
        #printKwListFn = self.printKeywordListToFile(orderInfoString)

        return True

