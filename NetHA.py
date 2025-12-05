#!/usr/bin/python
# encoding: utf-8
"""
NetHA.py: Manage cluster services with a shared service IP

Created by Ramón Barrios Lascar on 2008-07-15.
Copyright (c) 2008 iKnow. All rights reserved.
"""

import sys
import os
import string
import time
import re
from optparse import OptionParser

def ImPrimary(Opts):
  """
  This function tests if *this* node is the primary node in the cluster
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking if I'm the primary node ... " % (Opts.PrgName,) )
    if Opts.ImPrimary:
      sys.stdout.write( "I'm Primary!\n" )
    else:
      sys.stdout.write( "\n" )
  return Opts.ImPrimary
  
def WaitSettlingTime(Opts):
  """
  This simply waits for a configured time before trying to acquire resources
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Waiting for the settling time (%s secs)...\n" % (Opts.PrgName,Opts.SettlingTime) )
  time.sleep(Opts.SettlingTime)
  if Opts.Debug:
      sys.stdout.write( "Done the SettlingTime\n" )
  return True

def TestServiceInterface(Opts):
  """
  This function tests the availability of the service interfaces
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the service interface ...\n" % (Opts.PrgName,) )
  return True
  
def SplitValues(AString):
  """
  This function returns a list [ "item1", "item2", "item3" ] from a string "item1, item2, item3"
  """
  AList = []
  ItemList = AString.split(",")
  for AItem in ItemList:
    AList.append(AItem.strip())
  return AList
  
def LoadParams(Opts):
  """
  This function load de configuration for program from the configuration file
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Loading configuration file %s ...\n" % (Opts.PrgName, Opts.Config) )
  # Burned in values
  Opts.FlagFile = "/tmp/" + os.path.splitext(os.path.basename(sys.argv[0]))[0] + ".flag"
  # Burned in values
  try:
    ConfigFile = open( Opts.Config, "rU" )
    # The next RE is to capture the empty lines in the configuration file
    emptyRE = re.compile(r"^[ \t]*$")
    # The next RE is to capture the remark only lines in the configuration file
    remarkRE = re.compile(r"^[ \t]*#.*$")
    # The next RE is to capture general configuration lines in the configuration file
    compRE = re.compile(r"^[ \t]*[A-Za-z.]+[ \t]*=[ \t]*[A-Z0-9./][ \t]*$")
    # The next RE is only to capture the line of server names in the configuration file
    servernamesRE = re.compile(r"^[ \t]*ServerNames[ \t]*=[ \t]*(.*)[ \t]*")
    # The next RE is only to capture the ServerInterface lines in the configuration file
    serverinterfacesRE = re.compile(r"^[ \t]*ServerInterface\.(.*)[ \t]*=[ \t]*(.*)[ \t]*")
    # The next RE is only to capture the ServerDisk lines in the configuration file
    serverdisksRE = re.compile(r"^[ \t]*ServerDisk\.(.*)[ \t]*=[ \t]*(.*)[ \t]*")
    # The next RE is only to capture the ServerVolumeGroup lines in the configuration file
    servervolumegroupsRE = re.compile(r"^[ \t]*ServerVolumeGroup\.(.*)[ \t]*=[ \t]*(.*)[ \t]*")
    # The next RE is only to capture the ServerInterface lines in the configuration file
    serverfilesystemsRE = re.compile(r"^[ \t]*ServerFileSystem\.(.*)[ \t]*=[ \t]*(.*)[ \t]*")
    # The next RE is only to capture the ServerService lines in the configuration file
    serverservicesRE = re.compile(r"^[ \t]*ServerService\.(.*)\.(.*)[ \t]*=[ \t]*(.*)[ \t]*")

    for aLine in ConfigFile.readlines():
      aLine = aLine.strip()
      # The empty lines or only remark lines are skipped
      if not emptyRE.search(aLine) and not remarkRE.search(aLine):
        try:
          # First try to parse the line. The ServerNames line is VERY important
          servernamesMatch = servernamesRE.search(aLine)
          servergeneralMatch = compRE.search(aLine)
          serverinterfacesMatch = serverinterfacesRE.search(aLine)
          serverdisksMatch = serverdisksRE.search(aLine)
          servervolumegroupsMatch = servervolumegroupsRE.search(aLine)
          serverfilesystemsMatch = serverfilesystemsRE.search(aLine)
          serverservicesMatch = serverservicesRE.search(aLine)
          if servernamesMatch:
            try:
              Opts.ServerNames = SplitValues(servernamesMatch.group(1))
            except:
              sys.stdout.write("%s: from line '%s', error trying to load server names!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "%s\n" % (Opts,) )
          elif serverinterfacesMatch:
            try:
              Opts.ServerInterface[serverinterfacesMatch.group(1)] = SplitValues(serverinterfacesMatch.group(2))
            except:
              sys.stdout.write("%s: from line '%s', error trying to load server interface configuration!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "Opts.ServerInterface[%s] = %s\n" % (serverinterfacesMatch.group(1), serverinterfacesMatch.group(2) ) )
          elif serverdisksMatch:
            try:
              Opts.ServerDisk[serverdisksMatch.group(1)] = SplitValues(serverdisksMatch.group(2))
            except:
              sys.stdout.write("%s: from line '%s', error trying to load server disk configuration!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "Opts.ServerDisk[%s] = %s\n" % (serverdisksMatch.group(1), serverdisksMatch.group(2) ) )
          elif servervolumegroupsMatch:
            try:
              Opts.ServerVolumeGroup[servervolumegroupsMatch.group(1)] = SplitValues(servervolumegroupsMatch.group(2))
            except:
              sys.stderr.write("%s: from line '%s', error trying to load server volume groups configuration!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "Opts.ServerVolumeGroup[%s] = %s\n" % (servervolumegroupsMatch.group(1), servervolumegroupsMatch.group(2) ) )
          elif serverfilesystemsMatch:
            try:
              Opts.ServerFileSystem[serverfilesystemsMatch.group(1)] = SplitValues(serverfilesystemsMatch.group(2))
            except:
              sys.stderr.write("%s: from line '%s', error trying to load server file systems configuration!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "Opts.ServerFileSystem[%s] = %s\n" % (serverfilesystemsMatch.group(1), serverfilesystemsMatch.group(2) ) )
          elif serverservicesMatch:
            try:
              # try:
                if not serverservicesMatch.group(1) in dir(Opts.ServerService):
                  Opts.ServerService[serverservicesMatch.group(1)] = {}
                Opts.ServerService[serverservicesMatch.group(1)][serverservicesMatch.group(2)] = serverservicesMatch.group(3)
              # except:
              #   sys.stderr.write("%s: error trying to check Opts.ServerService[%s]!\n" %(Opts.Config,serverservicesMatch.group(1)))
            except:
              sys.stderr.write("%s: from line '%s', error trying to load server services configuration!\n" % (Opts.Config, aLine))
            if Opts.Debug:
              sys.stdout.write( "Opts.ServerService[%s][%s] = %s\n" % (serverservicesMatch.group(1), serverservicesMatch.group(2), serverservicesMatch.group(3) ) )
          elif servergeneralMatch:
            evaluateLine = "Opts." + aLine
            if Opts.Debug:
              sys.stdout.write("%s: %s\n" % (Opts.Config,evaluateLine))
            exec( evaluateLine )
        except:
          sys.stderr.write("%s: error trying to evaluate line '%s'!\n" % (Opts.Config,evaluateLine))
    ConfigFile.close()
    if Opts.Debug:
      print Opts
  except :
    sys.stderr.write("%s: Error processing configuration file (%s)!\n" % (Opts.PrgName, Opts.Config)) 
    sys.exit(3)
    
def TestFlagFile(Opts):
  """
  This function tests the existence of a flag file. If the flag file exists, the program stops
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking for the flag file %s ...\n" % (Opts.PrgName, Opts.Config) )
  return os.path.isfile(Opts.FlagFile)

def WaitCheckTime(Opts):
  """
  This function tests the existence of a flag file. If the flag file exists, the program stops
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Waiting the CheckWaitTime (%s secs) ... " % (Opts.PrgName, Opts.CheckWaitTime))
  time.sleep(Opts.CheckWaitTime)
  if Opts.Debug:
    sys.stderr.write( "Done the CheckWaitTime\n" )
    
def TestPeerNode(Opts):
  """
  This function tests the basic IP connectivity of some peer nodes
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the connectivity to peer nodes...\n" % (Opts.PrgName,))
  return True
        
def TestDisks(Opts):
  """
  This function tests the basic availability of cluster disks
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the basic availability of cluster disks...\n" % (Opts.PrgName,))
  return True

def TestVolumeGroups(Opts):
  """
  This function tests the basic availability of cluster volume groups
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the basic availability of cluster volume groups...\n" % (Opts.PrgName,))
  return True

def TestFileSystems(Opts):
  """
  This function tests the basic availability of cluster file systems
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the basic availability of cluster file systems...\n" % (Opts.PrgName,))
  return True

def TestRunningService(Opts):
  """
  This function tests the basic availability of cluster services
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Checking the basic availability of cluster services...\n" % (Opts.PrgName,))
  return True

def WaitRepetitionTime(Opts):
  """
  This function some defined time before starting the checks again
  """
  if Opts.Debug:
    sys.stdout.write( "%s: Waiting the RepetitionWaitTime (%s secs)... " % (Opts.PrgName, Opts.RepetitionWaitTime))
  time.sleep(Opts.RepetitionWaitTime)
  if Opts.Debug:
    sys.stdout.write( "Done wating.\n" )
  return True
  
def BringUpInterfaces(Opts):
  """
  This function tries to bring up interfaces
  """
  return True

def BringUpPeerNodes(Opts):
  """
  This function tries to bring up peer node communication
  """
  return True
  
def BringUpDisks(Opts):
  """
  This function tries to bring up disks
  """
  return True
  

# Start of main program  
parser = OptionParser()
parser.add_option( "-D", "--debug", dest="Debug", action="store_true", help="Debug mode", default=True)
parser.add_option( "-f", "--config", dest="Config", action="store", type="string", help="Configuration file name", default=os.path.splitext(os.path.basename(sys.argv[0]))[0]+".conf")

(Options, Args) = parser.parse_args()
# Load defaults
Options.PrgName = "NetHA"
Options.ImPrimary = False
Options.NumberOfChecks = 1
Options.CheckWaitTime = 10
Options.SettlingTime = 30
Options.RepetitionWaitTime = 30
Options.NumberOfRetries = 1
Options.ServerNames = []
Options.ServerInterface = {}
Options.ServerDisk = {}
Options.ServerVolumeGroup = {}
Options.ServerFileSystem = {}
Options.ServerService = {}
Options.CriticalReason = None

LoadParams(Options)
Options.NumberOfChecks = Options.NumberOfChecks+1
# Check if I'm the primary node
if not ImPrimary(Options):
  WaitSettlingTime(Options)
# Run forever
while True:
  # Test for a flag file. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestFlagFile(Options):
      break
    WaitCheckTime(Options)

  # Test for the availability of service interface. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestServiceInterface(Options):
      if not BringUpInterfaces(Options):
        Options.CriticalReason = "Interfaces"
        CriticalAlert(Options)
    WaitCheckTime(Options)
    
  # Test for the availability of peer nodes. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestPeerNode(Options):
      if not BringUpPeerNodes(Options):
        Options.CriticalReason = "Peers"
        CriticalAlert(Options)
    WaitCheckTime(Options)
    
  # Test for the availability of defined disks. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestDisks(Options):
      if not BringUpDisks(Options):
        Options.CriticalReason = "Disks"
        CriticalAlert(Options)
    WaitCheckTime(Options)
    
  # Test for the availability of defined volume groups. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestVolumeGroups(Options):
      if not BringUpVolumeGroups(Options):
        Options.CriticalReason = "VolumeGroups"
        CriticalAlert(Options)
    WaitCheckTime(Options)
    
  # Test for the availability of file systems. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestFileSystems(Options):
      if not BringUpFileSystems(Options):
        Options.CriticalReason = "FileSystems"
        CriticalAlert(Options)
    WaitCheckTime(Options)
    
  # Test for running services. Each check can be repeated
  for i in range(1, Options.NumberOfChecks):
    if TestRunningService(Options):
      if not BringUpServices(Options):
        Options.CriticalReason = "Services"
        CriticalAlert(Options)
    WaitSleepTime(Options)
    
  # Wait a defined time to repeat tests
  WaitRepetitionTime(Options)
  
  # If debug mode, run only once
  if Options.Debug:
    sys.exit(0)
  
