#!/usr/bin/python
"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""
import logging

__author__ = "Julio Colon, Priya Periaswamy"

"""
    MetaDB class is responsible for creating the metaDB list which consists of metaRows
"""
class MetaDB(object):
    __slots__ = ['tagsList']



    def __init__(self):
        # rows = {}
        # last_row_id = 0
        self.tagsList = []

    """
    InsertData function inserts the metaRow to metaDB
    metarow - metarow  which is defined below
    """

    def InsertData(self, metarow):
        self.tagsList.append(metarow)

    """
    getLastIndexFromMetaDB function is a utility method to return the last index from metaDB
    """

    def getLastIndexFromMetaDB(self):
        return len(self.tagsList)-1

    def RemoveData(self, metarow):
        pass

    """
    convenience method to print the metaDB to console
    """

    def printing(self):
        print("inside the metaDB print function")
        for eachMetaRow in self.tagsList:
            logging.debug("%s, %s, %s, %s, %s ", eachMetaRow.timestamp, eachMetaRow.filename, eachMetaRow.startline, eachMetaRow.endline, eachMetaRow.keywords)


"""
    MetaRow class consists of timestamp, filename, startline, endline, keywords which is parsed from each line of log file
"""

class MetaRow(object):
    __slots__ = ['timestamp', 'filename', 'startline','endline','negateAssociationFlag','keywords']
    def __init__(self, timestamp, filename, startline, endline, negateAssociationFlag, keywords):
        self.timestamp = timestamp
        self.filename = filename
        self.startline = startline
        self.endline = endline
        self.keywords = keywords
        self.negateAssociationFlag = negateAssociationFlag





