#!/usr/bin/env python
# encoding: utf-8
"""
ConsolidateWWPN.py: imports files with hosts and WWPN definitions into a master list

Created by Ramón Barrios Lascar on 2019-03-12.
Copyright (c) 2019 Ínodo S.A.S. All rights reserved.
"""
import sys, os, string
from optparse import OptionParser, SUPPRESS_HELP

def ShowStorageTypes(Opts):
  # Show only the supported storage types
  sys.stdout.write("%s: supported storage type syntaxes.\n"%(Opts.PrgName,))
  # Show SVC modes
  sys.stdout.write("  ")
  for Type in Opts.VirtualizeType:
    sys.stdout.write(Type)
    if Opts.VirtualizeType.index(Type)+1<len(Opts.VirtualizeType):
      sys.stdout.write(" | ")
    else:
      sys.stdout.write("\n")
  # Show XIV modes
  sys.stdout.write("  ")
  for Type in Opts.AccelerateType:
    sys.stdout.write(Type)
    if Opts.AccelerateType.index(Type)+1<len(Opts.AccelerateType):
      sys.stdout.write(" | ")
    else:
      sys.stdout.write("\n")
  # Show DS8000 modes
  sys.stdout.write("  ")
  for Type in Opts.DS8000Type:
    sys.stdout.write(Type)
    if Opts.DS8000Type.index(Type)+1<len(Opts.DS8000Type):
      sys.stdout.write(" | ")
    else:
      sys.stdout.write("\n")
  return

def MakeHostCommand(Opts,Name):
  # Return string command to create host in storage types
  if Opts.MakeSyntax=="SVC":
    HString="mkhost -name "
  elif Opts.MakeSyntax=="XIV":
    HString="host_define host="
  elif Opts.MakeSyntax=="DS8K":
    HString="N/A"
  return "%s%s"%(HString,Name)
  
def MakeAddPortPrefix(Opts):
  if Opts.MakeSyntax=="SVC":
    PString="; "
  elif Opts.MakeSyntax=="XIV":
    PString="; "
  else:
    PString=""
  return PString
  
def MakeHostPortSep(Opts):
  return "; "

def MakeAddPortSuffix(Opts):
  return ""
  
def MakeAddPortCommand(Opts,Name,WWPN):
  # Return string command to add port to host in storage types
  if Opts.MakeSyntax=="SVC":
    PString="addhostport -fcwwpn %s -force %s"%(WWPN,Name)
  elif Opts.MakeSyntax=="XIV":
    PString="host_add_port host=%s fcaddress=%s"%(Name,WWPN)
  elif Opts.MakeSyntax=="DS8K":
    PString="N/A"
  return PString

def ExtractWWPNs(Opts,PartialList):
  # Split list into a WWPN list
  BasicList=[]
  if Opts.Debug:
    sys.stderr.write("\n\t%s%s ExtractWWPNs(%s)\n"%(Opts.PrgName,Opts.ColonSep,PartialList))
  for Elem in PartialList:
    BasicList.extend(Elem.split(":"))
  for Elem in BasicList:
    Elem=Elem.upper()
  BasicList = [Item.upper() for Item in BasicList]
  if Opts.Debug:
    print "BasicList=",BasicList
  return BasicList
  
def ProcessOneFile(List, Opts, FileName):
  # Load WWPN for items in list
  if os.path.basename(FileName) in Opts.Exclusions:
    if Opts.Debug:
      sys.stderr.write("  DEBUG: %s%s excluded file '%s' found\n" % (Opts.PrgName,Opts.ColonSep,FileName))
    return List, Opts
  if os.path.getsize(FileName):
    # Process only sizeable files
    if Opts.Debug:
      sys.stderr.write("%s%s processing %s...\n"%(Opts.PrgName,Opts.ColonSep,FileName,))
    WWPNlines=open(FileName,"r").readlines() # Slurp all file
    Opts.Count+=1
    if Opts.Debug:
      sys.stderr.write("%s%s slurp %d lines from '%s'\n"%(Opts.PrgName,Opts.ColonSep,len(WWPNlines),FileName))
    for TextLine in WWPNlines:
      TextLine=TextLine.strip()
      if Opts.Debug:
        sys.stderr.write("%s%s processing [%s]"%(Opts.PrgName,Opts.ColonSep,TextLine))
      try:
        TextName=TextLine.split()[0]
        Name=TextName.upper()
        if Name in List:
          # Adjust list of WWPNs and add to server in list
          FoundWWPN=ExtractWWPNs(Opts,TextLine.split()[1:])
          FoundWWPN.extend(List[Name])
          # List[Name]=sorted(set(FoundWWPN))
        else:
          # If not, the server is NOT in the list, add a new keyed element to the list
          if Opts.Debug:
            sys.stderr.write("\t add [%s] to List\n"%(Name,))
          FoundWWPN=ExtractWWPNs(Opts,TextLine.split()[1:])
        List[Name]=sorted(set(FoundWWPN))
        if Opts.Debug:
          print(List[Name])
      except IndexError:
        # If empty text line, process next
        continue
  else:
    sys.stderr.write("%s%s zero sized file found [%s]!\n"%(Opts.PrgName,Opts.ColonSep,FileName))
  return List, Opts
    
def OutputConsolidated(List,Opts,O):
  # Show consolidated list in output
  if O==sys.stdout:
    F=sys.stdout
  else:
    F=open(O,"w")
  if len(MasterList)>0:
    if (not Opts.MakeSyntax):
      if not Opts.Output:
        sys.stderr.write("%s consolidated list%s\n"%(Options.PrgName,Options.ColonSep))
    else:
      if not Opts.Output:
        sys.stderr.write("%s host creation list%s\n"%(Options.PrgName,Options.ColonSep))
    for HostName in sorted(MasterList):
      if Opts.MakeSyntax:
        HostNameCommand=MakeHostCommand(Opts,HostName)
        AddPortPrefix=MakeAddPortPrefix(Opts)
        HostPortSep=MakeHostPortSep(Opts)
        AddPortSuffix=MakeAddPortSuffix(Opts)
      else:
        HostNameCommand="%-32s"%(HostName,)
        AddPortCommand=""
        AddPortPrefix=""
        HostPortSep=":"
        AddPortSuffix=""
        
      F.write(HostNameCommand)
      # sys.stdout.write(" ") # Separator
      F.write(AddPortPrefix)
      if len(MasterList[HostName])>0:
        for WWPN in MasterList[HostName]:
          if Opts.MakeSyntax:
            AddPortCommand=MakeAddPortCommand(Opts,HostName,WWPN)
            F.write(AddPortCommand)
          else:
            F.write(WWPN)
          if MasterList[HostName].index(WWPN)+1==len(MasterList[HostName]):
            F.write(AddPortSuffix)
            F.write("\n")
          else:
            F.write(HostPortSep)
  F.flush()
  if (O!=sys.stdout) and (O!=sys.stderr):
    F.close()
  return
  
# START OF MAIN FILE ------------------------------------------------------------------
try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] DIR ... FILE ... ")
  parser.add_option("-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
  parser.add_option("-o", "--output", dest="Output", action="store", help="Output file")
  parser.add_option("-0", "--null", dest="NullTerminated", action="store_true", help="Null terminated file names", default=False)
  parser.add_option("-l", "--skip-symlinks", dest="SkipSymLinks", action="store_true", help="Skip symbolic links", default=False)
  parser.add_option("-t", "--show-time", dest="ShowTime", action="store_true", help="Show time used", default=False)
  parser.add_option("-p", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME")
  parser.add_option("-m", "--make",dest="MakeSyntax", action="store", type="string", help="Show mkhost syntax for storage type", metavar="STORAGE")
  parser.add_option("--show-storage-types",dest="ShowStorage",action="store_true",default=False, help="Show storage types")
  parser.add_option("--DEBUG", dest="Debug", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DIGITS", "-#", dest="Digits", action="store", type="int", default=4, help=SUPPRESS_HELP)
  parser.add_option("--BASEFORMAT", "-B", dest="BaseFormat", action="store", default=" [%%%dd]", help=SUPPRESS_HELP)
  parser.add_option("--width", "-w", dest="LineWidth", action="store", type="int", default=100, help=SUPPRESS_HELP)

  (Options, Args) = parser.parse_args()
  Options.PrgName="ConsolidateWWPN"
  Options.VirtualizeType=["SVC","SPECTRUM_VIRTUALIZE","VIRTUALIZE","STORWIZE","V3000","V5000","V7000","V9000","FS900","FS9100","FS9K"]  
  Options.AccelerateType=["XIV","SPECTRUM_ACCELERATE","ACCELERATE","A9000","A9K","A9000R","A9KR"]
  Options.DS8000Type=["DS8000","DS8K"]
  if Options.ShowStorage:
    ShowStorageTypes(Options)
    exit(0)  
  Options.Count = 0
  Options.Format=Options.BaseFormat % Options.Digits
  if Options.ShowTime:
    import time
    Options.StartTime = time.time()
    Options.EndTime = time.time ()

  if Options.Debug:
    Options.ColonSep=""
  else:
    Options.ColonSep=":"  

  MasterList = {}
  ExclusionsList = ['.DS_Store']
  Options.Exclusions = ExclusionsList

  if len(Args) > 0 :
    if Options.Debug:
      sys.stderr.write("  DEBUG: ")
    if Options.ShowTime:
      StartTime = time.localtime(Options.StartTime)
      sys.stderr.write("%s%s started at %04d/%02d/%02d %02d:%02d:%02d\n" % (Options.PrgName, Options.ColonSep, StartTime[0], StartTime[1], StartTime[2], StartTime[3], StartTime[4], StartTime[5]))
    for OneArg in Args:
      if Options.SkipSymLinks:
        if Options.Debug:
          sys.stderr.write("  DEGUG: same skipping symbolic links\n")
        if (not os.path.islink(OneArg) and os.path.isfile(OneArg)) or ():  
          try:
            MasterList,Options = ProcessOneFile(MasterList,Options,OneArg)
          except (IOError, OSError):
            pass
        else:
          if os.path.isfile(OneArg):
            try:
              MasterHashes,Options = ProcessOneFile(MasterHashes,Options,OneArg)
            except (IOError, OSError):
              pass
      else:
        try:
          MasterList,Options = ProcessOneFile(MasterList,Options,OneArg)
          if Options.Debug:
            print(MasterList)
        except (IOError, OSError):
          pass
    if Options.MakeSyntax:
      Options.MakeSyntax=Options.MakeSyntax.upper()
      if not Options.MakeSyntax in ["SVC","XIV","DS8K"]:
        if Options.MakeSyntax in Options.VirtualizeType:
          Options.MakeSyntax="SVC"
        elif Options.MakeSyntax in Options.AccelerateType:
          Options.MakeSyntax="XIV"
        elif Options.MakeSyntax in Options.DS8000Type:
          Options.MakeSyntax="DS8K"
        else:
          sys.stderr.write("%s: unsupported or unrecognized storage syntax option '%s', exiting...\n"%(Options.PrgName,Options.MakeSyntax))
          exit(2)
    # Show in standard output (screen)
    if Options.Verbose:
      OutputConsolidated(MasterList,Options,sys.stdout)
    # Store in file
    if Options.Output:
      OutputConsolidated(MasterList,Options,Options.Output)

    if Options.ShowTime:
      EndTime = time.localtime(Options.StartTime)
      if Options.Count==1:
        sys.stderr.write( "%s%s processed %d file, in %fs (%fs/file)\n" % (Options.PrgName, Options.ColonSep, Options.Count, Options.EndTime-Options.StartTime, (Options.EndTime-Options.StartTime)/Options.Count))
      else:
        sys.stderr.write( "%s%s processed %d files, in %fs (%fs/file)\n" % (Options.PrgName, Options.ColonSep, Options.Count, Options.EndTime-Options.StartTime, (Options.EndTime-Options.StartTime)/Options.Count))
  else:
    parser.error("one or more arguments are needed!")
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
