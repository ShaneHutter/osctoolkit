#!/usr/bin/env python
'''
OSC Whispers
    oscwhispers.py
      Written by: Shane Huter

    Required Dependencies:  python >= 3.5, pyliblo

      This python script, and all of OSC_Tools is licensed
      under the GNU GPL version 3.

      OSC Whispers recieves OSC Messages and forwards the message to a new
      location(s) based on the messages Path Prefix.

      OSC Whispers is a part of osctoolkit.

      osctoolkit is free software; you can redistribute it and/or modify
      it under the terms of the GNU Lesser General Public License as published 
      by the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.

      osctoolkit is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
      GNU Lesser General Public License for more details.

      You should have received a copy of the GNU Lesser General Public License
      along with this program. If not, see <http://www.gnu.org/licenses/>..
'''

import sys, liblo

#PROGRAM CONST
CLEAN=0
ERROR=1
ENUMERATE_ITERATE_INDEX=0
OTW_FILE_ARG=1
REQUIRED_ARGUMENTS=2
MAIN_LOOP_LATENCY=1
HELP_CALL_ARG=1
HELP_ONLY_ARGUMENTS=2

#CONFIG CONST
CONFIG_PROPERTY_ARG=0
CONFIG_VALUE_ARG=1

#OSC CONST
IP_INDEX=0
PORT_INDEX=1
PATH_INFO_LIST_INDEX=0
CLIENT_TARGET_LIST_INDEX=1
PATH_PREFIX_INDEX=0
TRUNCATE_INDICATOR_INDEX=1
PATH_PREFIX_SPLIT_INDEX=1
STARTING_NON_PATH_PREFIX_INDEX=2

#program vars
forwardingList=[]
oscMessageTargets=[]
targetIdList=[]
tempMessageTargets=[]
reusedTarget=False

#OSC vars
oscTarget=[]

#Help and exit
def helpAndExit(exitStatus):
    print('Usage:')
    print('  oscwhispers [FILENAME]')
    print()
    print('Optional arguments:')
    print('  -h, --help    Display help and exit.')
    print()
    print('Further Documentation:')
    print('  https://github.com/ShaneHutter/osctoolkit/wiki')
    print()
    sys.exit(exitStatus)

#check for help call
if len(sys.argv)>= HELP_ONLY_ARGUMENTS:
    if sys.argv[HELP_CALL_ARG]=='-h' or sys.argv[HELP_CALL_ARG]=='--help':
        helpAndExit(CLEAN)

#Check if the required number of arguments where passed
if len(sys.argv)!=REQUIRED_ARGUMENTS:
    helpAndExit(ERROR)
    
#load config file and declare global vars
try:
    configFileName='osctoolkit.conf'
    configFile=open(configFileName,'r')
    configLines=configFile.read().split('\n')
except:
    configFileName='/etc/osctoolkit.conf'
    configFile=open(configFileName,'r')
    configLines=configFile.read().split('\n')
finally:
    configFile.close()
for lineRead in configLines:
    if lineRead!="" and lineRead.strip().startswith('#')==False:
        #verbosity settings
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='oscwhispers.verbose_listen_port':
            global verboseListenPort
            verboseListenPort=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='oscwhispers.verbose_incoming_osc':
            global verboseIncomingOsc
            verboseIncomingOsc=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='oscwhispers.verbose_outgoing_osc':
            global verboseOutgoingOsc
            verboseOutgoingOsc=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='oscwhispers.verbose_forwarding_list':
            global verboseForwardingList
            verboseForwardingList=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))

        #OSC Settings
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='oscwhispers.listen_port':
            global listenPort
            listenPort=int(lineRead.split()[CONFIG_VALUE_ARG])

#load the forwarding destinations from file
#FILE LOAD CONST
PATH_PREFIX_FILE_INDEX=0
TRUNCATE_INDICATOR_FILE_INDEX=1
DESTINATIONS_START_INDEX=2
#file load vars
otwFileName=sys.argv[OTW_FILE_ARG]
otwFile=open(otwFileName, 'r')
otwLines=otwFile.read().split('\n')
otwFile.close()
for lineRead in otwLines:
    if lineRead!="" and lineRead.strip().startswith('#')==False:
        if lineRead.strip().startswith("/")==True:
            #parse forwarding destinations line
            forwardingPathPrefix=lineRead.split()[PATH_PREFIX_FILE_INDEX].strip('/')
            if lineRead.split()[TRUNCATE_INDICATOR_FILE_INDEX]=="+":
                #do not truncate prefix of path
                truncatePathPrefix=False
            elif lineRead.split()[TRUNCATE_INDICATOR_FILE_INDEX]=="-":
                #truncate prefix of path
                truncatePathPrefix=True
            else:
                helpAndExit(ERROR)
            pathPrefixInfo=[forwardingPathPrefix,truncatePathPrefix]
            for destination in range(DESTINATIONS_START_INDEX,len(lineRead.split())):
                #load the destinations into its own list, and load the index of the destination into the forwardingList
                #It will have to scan back through the destination (server list) to make sure it doesnt store duplicates
                messageIP=lineRead.split()[destination].split(':')[IP_INDEX]
                messagePort=int(lineRead.split()[destination].split(':')[PORT_INDEX])
                tempMessageTargets.append([messageIP, messagePort])
                for targetScan in tempMessageTargets:
                    oscMessageTargets.append([targetScan[IP_INDEX], targetScan[PORT_INDEX]])
                    targetId=len(oscMessageTargets)-1
                targetIdList.append(targetId)
                tempMessageTargets=[]
            forwardingList.append([pathPrefixInfo, targetIdList])
            reusedTarget=False
            targetIdList=[]
            
#setup OSC Server
try:
    if verboseListenPort == True:
        print('Listening on port: ', end='')
        print(listenPort)
    oscListenServer=liblo.Server(listenPort)
except liblo.ServerError as error:
    print(str(error))
    sys.exit(ERROR)

#setup OSC clients
for target in oscMessageTargets:
    try:
        oscTarget.append(liblo.Address(target[IP_INDEX], target[PORT_INDEX]))
    except liblo.AddressError as error:
        print(str(error))
        sys.exit(ERROR)

def sendOSC(target, path, args):
    #send osc messages in this function
    libloSend='liblo.send(target, path'
    for eachArg in enumerate(args):
        libloSend+=', args['+str(eachArg[ENUMERATE_ITERATE_INDEX])+']'
    libloSend+=')'
    exec(libloSend)
    return

def truncatePathPrefix(inpath):
    #truncate osc paths here
    outpath=''
    for dirs in range(STARTING_NON_PATH_PREFIX_INDEX,len(inpath.split('/'))):
        outpath+='/'+inpath.split('/')[dirs]
    return outpath

def pathPrefix(inpath):
    #this function returns the a paths top level
    prefix=inpath.split('/')[PATH_PREFIX_SPLIT_INDEX]
    return prefix

def forwardMessage(path, args):
    for eachList in forwardingList:
        if eachList[PATH_INFO_LIST_INDEX][PATH_PREFIX_INDEX]==pathPrefix(path):
            if eachList[PATH_INFO_LIST_INDEX][TRUNCATE_INDICATOR_INDEX]==True:
                for eachTarget in eachList[CLIENT_TARGET_LIST_INDEX]:
                    sendOSC(oscTarget[eachTarget], truncatePathPrefix(path), args)
            else:
                for eachTarget in eachList[CLIENT_TARGET_LIST_INDEX]:
                    sendOSC(oscTarget[eachTarget], path, args)
    return
        
#register OSC Listen method
oscListenServer.add_method(None, None, forwardMessage)
    
#output Startup verbosity
if verboseForwardingList==True:
    print()
    for eachList in forwardingList:
        #make this output look nicer
        print('Path with prefix /', end='')
        print(eachList[PATH_INFO_LIST_INDEX][PATH_PREFIX_INDEX], end=' ')
        if eachList[PATH_INFO_LIST_INDEX][TRUNCATE_INDICATOR_INDEX]==True:
            print('will truncate path prefix.')
        else:
            print('will not truncate path prefix.')
        print('Then it will forward to:')
        for target in eachList[CLIENT_TARGET_LIST_INDEX]:
            print('IP: ', end='')
            print(oscMessageTargets[target][IP_INDEX], end='    Port: ')
            print(str(oscMessageTargets[target][PORT_INDEX]))
        print()

#main loop
while True:
    oscListenServer.recv(MAIN_LOOP_LATENCY)
sys.exit(CLEAN)
