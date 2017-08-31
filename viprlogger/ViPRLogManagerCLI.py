#!/usr/bin/python

"""
Copyright 2015 EMC Corporation
All Rights Reserved
EMC Confidential: Restricted Internal Distribution
81ff427ffd0a66013a8e07b7b967d6d6b5f06b1b.ViPR
"""

import sys
import time
import argparse
import os

from ViPRLogManager import ViPRLogManager

__author__ = "Julio Colon, Priya Periaswamy"

import logging

"""
    ViPRLogManagerCLI class is the CLI which is responsible for processing the log files and getting the log data for the order info passed
"""
class ViPRLogManagerCLI(object):
    # @profile
    def __init__(self):
        self.lmLogger = logging.getLogger("ViPRLogManager")
        arguments = self.parseArguments()
        self.viprLogManager = ViPRLogManager()
        self.lmLogger.info("Hi!  Thank you for using Log Manager.  Starting Log Analysis.")
        self.main(arguments)

    """
    parseArguments function parses the arguments passed in the input
    input_file - the zip or tar file with log files from ViPR controller
    order info - such as order Number, orderId or task id
    pass number - the pass number which is requested
    """
    def parseArguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', action='store', dest='download_file', help='download zip file to process', default="False")
        parser.add_argument('-i', action='store', dest='input_file', help='Input zip or tar file to process', default="False")
        parser.add_argument('-o', action='store', dest='order_info', help='Order Detail to investigate', default="False")
        parser.add_argument('-e', action='store', dest='exclusion_list', help='Exclusion List to use', default="False")
        parser.add_argument('-p', action='store', dest='pass_num', help='Pass number to process the logs', default="1")
        parser.add_argument('-ucf', action='store', dest='user_config_file', help='UserConfig file to use', default="False")
        arguments = parser.parse_args()

        return arguments

    def getPassNum(self):
        while(True):
            try:
                print('Please enter pass number: ')
                passNum=sys.stdin.readline().strip()
                if(passNum.isdigit()):
                    return str(passNum).strip()
            except ValueError:
                print("Sorry, I didn't understand that.")
                #better try again... Return to the start of the loop
                continue

    """
    str2bool function is a convenience function to convert the user input to desired True vaules
    """

    def str2bool(self, value):
      return value.lower() in ("yes", "true", "t", "1", "y")

    """
    main function which calls the appropriate methods with the input arguments
    input_file - the file with log files from ViPR controller
    order info - such as order Number, orderId or task id
    pass number - the pass number which is requested
    """

    def main(self, myArgs):
        if(myArgs.input_file != "False"):
            self.lmLogger.info("Input file is %s", myArgs.input_file)
            input_file_to_analyze = myArgs.input_file
        elif(myArgs.download_file != "False"):
            self.lmLogger.info("User has requested to download the log file from ViPR nodes")
        else:
            print("Either the input file (in zip format) or the option to download from the ViPR instance need to be given.")
            exit(0)


        if(myArgs.order_info != "False"):
            self.lmLogger.info("Order information provided is %s", myArgs.order_info)
        elif(myArgs.user_config_file != "False"):
            self.lmLogger.info("User configuration file to use is %s ", myArgs.user_config_file)
            self.viprLogManager.readUserConfig(myArgs.user_config_file)
        else:
            self.lmLogger.info("\n\nEither orderInfo details should be passed in the command line or populated in the orderInfoList section of the userConfig.json file."
                               "Do not forget to pass the userConfig.json in the command with -ucf option \n\n")
            exit(0)

        if sys.version_info < (2, 7, 5):
            print( "Log Manager requires a minimum Python version 2.7.5. Your Python interpreter is too old. Please consider upgrading.")
            exit(0)

        if(myArgs.download_file != "False"):
            import GetLogsFromViPRNode
            downloadDirectory = self.viprLogManager.getDownloadDirectory()
            input_file_to_analyze = GetLogsFromViPRNode.getLogs(downloadDirectory)

        # Either the orderInfo should be passed in the command line or in the userConfig under the orderInfoList
        userOrderInfoDict = self.viprLogManager.inputOrderInfoValidation(myArgs.order_info)
        if(len(userOrderInfoDict.get("orderInfoList")) == 0):
            self.lmLogger.info("\n\nEither orderInfo details should be passed in the command line or populated in the orderInfoList section of the userConfig.json file."
                               "Do not forget to pass the userConfig.json in the command with -ucf option \n\n")
            exit(0)

        self.viprLogManager.createAnalysis(input_file_to_analyze)
        logInquireStatusFinal = True
        while(True):
            logInquireStatus = self.viprLogManager.fetchLogInfo(userOrderInfoDict, myArgs.pass_num, myArgs.exclusion_list)



            time.sleep(2)
            if(os.name == 'posix'):
                self.lmLogger.debug("the total memory used is (in MB)"),
                self.lmLogger.debug(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000)
            print('Do you want to continue the execution with another order number in the same input logs that was submitted... Press Y to continue... Any other key to quit: ')
            answer=sys.stdin.readline()
            if(answer.strip().upper()  == 'Y'):
                print('Please enter Order Info: ')
                myArgs.order_info=sys.stdin.readline().strip()
                userOrderInfoList = []
                userOrderInfoList.append(myArgs.order_info)
                userOrderInfoDict["orderInfoList"] = userOrderInfoList

            else:
                break

        self.lmLogger.info("Log Manager finished analyzing the submitted log files. Exiting the application.")
        self.viprLogManager.clearLogs()
        if(os.name == 'posix'):
            self.lmLogger.debug("the total memory used is (in MB)"),
            self.lmLogger.debug(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000)


if __name__ == "__main__":
    if(os.name == 'posix'):
        import resource
    ViPRLogManagerCLI()

