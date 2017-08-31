#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import logging

__author__ = "Priya Periaswamy"

"""
    WorkflowDetail class is responsible for storing the details of the workflow. This helps to get the status and the elapsed Time for the step under investigation
"""

class WorkflowDetail(object):
    __slots__ = ['startTime', 'endTime', 'workflowId', 'operationName', 'oprDetailDesc', 'message', 'state', 'elapsedTime']

    def __init__(self, workflowId, operationName, startTime, endTime, message, state, oprDetailDesc, elapsedTime):
        self.workflowId = workflowId
        self.operationName = operationName
        self.startTime = startTime
        self.endTime = endTime
        self.message = message
        self.state = state
        self.oprDetailDesc = oprDetailDesc
        self.elapsedTime = elapsedTime
