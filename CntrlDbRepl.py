#!/usr/bin/python
# encoding: utf-8
"""
CntrlDbRepl.py: Control database LUN replication
Created by Ramón Barrios Láscar on 2013/10/17
Last modified by Ramón Barrios Láscar on 2014/01/03
Copyright (c) 2013, 2014 Ínodo. All rights reserved
"""

import sys, os, inspect, subprocess, time, random
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn(Opts):
  if Opts.DEBUG:
    sys.stderr.write(" • %s\n"%(inspect.stack()[1][3]),)

def UNIXconnect(Opts, UserName, ServerName, CommandString):
  DebugFn(Opts)
  FnName=inspect.stack()[1][3]
  CxUserServer="%s@%s" % (UserName,ServerName)
  CxCommand=[Opts.RemoteUnixCommand, CxUserServer, CommandString]
  if Opts.DEBUG:
    sys.stderr.write(" •• %s=%s\n" % ("CxCommand", CxCommand))
  try:
    CxLines=""
    CxLines = subprocess.check_output(CxCommand,shell=False)
    CxLines = CxLines.decode('utf-8')
    if Opts.DEBUG:
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.write(str(CxLines))
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.flush()
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    sys.stderr.write("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CxCommand", CxCommand))
    if not Opts.DEBUG:
      Opts.ExitCode=8
      sys.exit(Opts.ExitCode) # Exit code 8 now defined as ERROR in SSH CONNECTION
  return CxLines

def WINconnect(Opts, ServerName, CommandString):
  DebugFn(Opts)
  FnName=inspect.stack()[1][3]
  CxServer=r"\\%s" % (ServerName,)
  CxCommand="%s %s %s" % (Opts.RemoteWindowsCommand, CxServer, CommandString)
  if Opts.DEBUG:
    sys.stderr.write(" •• %s=[%s]\n" % ("CxCommand", CxCommand))
  try:
    CxLines=""
    CxLines = subprocess.check_output(CxCommand)
    CxLines=CxLines.decode('utf-8')
    if Opts.DEBUG:
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.write(str(CxLines)+'\n')
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.flush()
  except subprocess.CalledProcessError as e:
    if e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    sys.stderr.write("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CxCommand", CxCommand))
    if not Opts.DEBUG:
      Opts.ExitCode=9
      sys.exit(Opts.ExitCode) # Exit code 9 now defined as ERROR in PSEXEC CONNECTION
  return CxLines

def MessageFn(Opts,M):
  if Opts.Verbose:
    if M==1:
      sys.stdout.write("%s: waiting %s for %s seconds.\n" % (Opts.PrgName,Opts.Server3Name,Opts.ShutdownWait))
    elif M==2:
      sys.stdout.write("%s: getting %s VMID...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==3:
      sys.stdout.write("%s: getting %s virtual machine state...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==4:
      sys.stdout.write("%s: shutting down target VM (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==5:
      sys.stdout.write("%s: powering off target VM (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==6:
      sys.stdout.write("%s: removing clone disk on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==7:
      sys.stdout.write("%s: unmapping clone disk on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==8:
      sys.stdout.write("%s: stopping services on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==9:
      sys.stdout.write("%s: stopping MS SQL Server Agent on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==10:
      sys.stdout.write("%s: stopping MS SQL Server on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==11:
      sys.stdout.write("%s: flushing first disk cache on target (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==12:
      sys.stdout.write("%s: stopping MS SQL Server first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==13:
      sys.stdout.write("%s: stopping MS SQL Server Agent first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==14:
      sys.stdout.write("%s: stopping MS SQL Server first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==15:
      sys.stdout.write("%s: flushing disk cache on first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==16:
      sys.stdout.write("%s: replicating volume on storage %s...\n" % (Opts.PrgName,Opts.Storage1Name))
    elif M==17:
      sys.stdout.write("%s: starting services on first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==18:
      sys.stdout.write("%s: starting MS SQL Server on first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==19:
      sys.stdout.write("%s: starting MS SQL Server Agent on first source (%s)...\n" % (Opts.PrgName,Opts.Server1Name))
    elif M==20:
      sys.stdout.write("%s: stopping services on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==21:
      sys.stdout.write("%s: stopping MS SQL Server Agent on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==22:
      sys.stdout.write("%s: stopping MS SQL Server on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==23:
      sys.stdout.write("%s: flushing disk cache on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==24:
      sys.stdout.write("%s: starting services on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==25:
      sys.stdout.write("%s: starting MS SQL Server on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==26:
      sys.stdout.write("%s: starting MS SQL Server Agent on second source (%s)...\n" % (Opts.PrgName,Opts.Server2Name))
    elif M==27:
      sys.stdout.write("%s: re-scanning SAN from all adapters on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==28:
      sys.stdout.write("%s: searching for snaphosts on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==29:
      sys.stdout.write("%s: resigning snapshot on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==30:
      sys.stdout.write("%s: searching for new snapshot file system on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==31:
      sys.stdout.write("%s: searching for new datastores on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==32:
      sys.stdout.write("%s: searching for new virtual disk files on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==33:
      sys.stdout.write("%s: trying to attach clone disk to target (%s)...\n" % (Opts.PrgName,Opts.Server3Name))
    elif M==34:
      sys.stdout.write("%s: starting virtual machine (%s)...\n" % (Opts.PrgName,Opts.Server3VMname))
    elif M==35:
      sys.stdout.write("%s: reassigning a drive letter on target (%s)...\n" % (Opts.PrgName,Opts.Server3Name))
    elif M==36:
      sys.stdout.write("%s: searching for mounted NFS file systems on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==37:
      sys.stdout.write("%s: adding and mounting NFS file systems on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==38:
      sys.stdout.write("%s: unmounting and removing NFS file systems on virtualization host (%s)...\n" % (Opts.PrgName,Opts.VHost1Name))
    elif M==39:
      sys.stdout.write("%s: trying to attach virtual disk to target (%s)...\n" % (Opts.PrgName,Opts.Server3Name))
    elif M==40:
      sys.stdout.write("%s: trying to attach NFS VMDK disk to target (%s)...\n" % (Opts.PrgName,Opts.Server3Name))
    sys.stdout.flush()

def MessageSpecific(Opts,Message):
  if Opts.Verbose:
    sys.stdout.write("%s: %s\n" % (Opts.PrgName,Message))
      
def WaitSeconds(Opts):
  MessageFn(Opts,1)
  if Opts.DEBUG and Opts.NoWaitOnDebug:
    sys.stderr.write(" • WaitSeconds(NoWaitOnDebug)\n")
  else:
    time.sleep(Opts.ShutdownWait)
  return True

def MiniWait(Opts):
  if not Opts.DEBUG:
    time.sleep(Opts.MiniWait)
  return True

def GetVirtualMachine(Opts,VMname):
  DebugFn(Opts)
  MessageFn(Opts,2)
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/getallvms | awk '$2~/%s$/ {print $1}' | tee %sVM.txt" % (Opts.VMre,Opts.Server3VMname,)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    Opts.VMid=OutputText.splitlines()[0]
    if len(Opts.VMid)==0:
      sys.stderr.write("%s: could not get the VM ID of %s, exiting...\n" % (Opts.PrgName,Opts.Server3Name))
      Opts.ExitCode=50
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to shutdown %s (%s) on %s!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=10
    sys.exit(Opts.ExitCode)
  return True
  
def GetVirtualMachineState(Opts):
  DebugFn(Opts)
  MessageFn(Opts,3)
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.getstate %s | tail -1 | sed 's/power/Power/g;s/on/On/;s/off/Off/;s/ //g'" % (Opts.VMid)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    Opts.VMstate=OutputText.splitlines()[0]
    if len(Opts.VMid)==0:
      sys.stderr.write("%s: could not get the state of VM %s (%s) on %s, exiting...\n" % (Opts.PrgName,Opts.Server3Name,Opts.VMid,Opts.VHostName))
      Opts.ExitCode=51
      sys.exit(Opts.ExitCode)
  return True
  
def ShutdownTarget(Opts):
  DebugFn(Opts)
  MessageFn(Opts,4)
  if Opts.VHostType=="vmware":
    if Opts.VMstate != "PoweredOff":
      CxCommand="vim-cmd vmsvc/power.shutdown %s 2>&1| awk '/existingState/{print substr($3,2,length($3)-3)}' " % (Opts.VMid,)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      if len(OutputText)>0 and len(OutputText.splitlines()[0])>0:
        Opts.VMstate=OutputText.splitlines()[0]
  else:
    sys.stderr.write("%s: don't know how to shutdown %s (%s) on %s!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=11
    sys.exit(Opts.ExitCode)
  return True

def PowerOffTarget(Opts):
  DebugFn(Opts)
  MessageFn(Opts,5)
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.off %s" % (Opts.VMid,)
    UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to stop %s (%s) on %s!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=12
    sys.exit(Opts.ExitCode)
  return True

def RemoveCloneOnTarget(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,6)
  MessageSpecific(Opts,"trying to remove disk %s (%s)..." % (Num,Opts.CloneDisk[Num]))
  Opts.Raise=False
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/device.diskremove %s %s %s false" % (Opts.VMid,Opts.Controller[1],Opts.CloneDisk[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    Opts.Raise=True
  else:
    sys.stderr.write("%s: don't know how to remove cloned disk #%s (%s) from %s on %s!\n" % (Opts.PrgName,Num,Opts.CloneDisk[Num],Opts.Server3Name,Opts.VHostName))
    Opts.ExitCode=13
    sys.exit(Opts.ExitCode)
  return True

def UnmapCloneLun(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,7)
  MessageSpecific(Opts,"trying to unmap disk %s (%s)..." % (Num,Opts.CloneDisk[Num]))
  if Opts.Storage1Type=="storwize":
    MessageSpecific(Opts,"unmapping from %s..." % ("SR-"+Opts.VHost2Name,))
    CxCommand="rmvdiskhostmap -host %s %s_snapshot1"%("SR-"+Opts.VHost2Name,Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    MessageSpecific(Opts,"unmapping from %s..." % ("SR-"+Opts.VHost1Name,))
    CxCommand="rmvdiskhostmap -host %s %s_snapshot1"%("SR-"+Opts.VHost1Name,Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to un-map volumes on %s!\n" % (Opts.PrgName,Opts.Storage1Name))
    Opts.ExitCode=21
    sys.exit(Opts.ExitCode)
  return True

def StopSQLServerOnTarget(Opts):
  DebugFn(Opts)
  MessageFn(Opts,8)
  if Opts.Server3Type=="windows":
    MessageFn(Opts,9)
    WINconnect(Opts,Opts.Server3Name,Opts.StopSQLServerAgent)
    MessageFn(Opts,10)
    WINconnect(Opts,Opts.Server3Name,Opts.StopSQLServer)
  else:
    sys.stderr.write("%s: dont' know how to connect and stop MS SQL Server on %s!\n" % (Opts.PrgName,Opts.Server3Name))
    Opts.ExitCode=31
    sys.exit(Opts.ExitCode)
  return True
  
def Flush1stCacheOnTarget(Opts):
  DebugFn(Opts)
  MessageFn(Opts,11)
  CxCommand="""CMD.EXE /C C:\Automatizacion\FlushCacheE.cmd"""
  if Opts.Server3Type=="windows":
    WINconnect(Opts,Opts.Server3Name,CxCommand)
  else:
    sys.stderr.write("%s: dont' know how to flush cache on %s!\n" % (Opts.PrgName,Opts.Server3Name))
    Opts.ExitCode=32
    sys.exit(Opts.ExitCode)
  return True

def StopSQLServerOnSource1(Opts):
  DebugFn(Opts)
  MessageFn(Opts,12)
  FnName=inspect.stack()[0][3]
  if Opts.Server1Type=="windows":
    try:
      MessageFn(Opts,13)
      WINconnect(Opts,Opts.Server1Name,Opts.StopSQLServerAgent)
      MessageFn(Opts,14)
      WINconnect(Opts,Opts.Server1Name,Opts.StopSQLServer)
    except subprocess.CalledProcessError as e:
      if e.returncode==2:
        sys.stderr.write("•• %s: SQL Server was stopped on %s!\n"%(FnName,Opts.Server1Name,))
  else:
    sys.stderr.write("%s: dont' know how to connect and stop MS SQL Server on %s!\n" % (Opts.PrgName,Opts.Server1Name))
    Opts.ExitCode=33
    sys.exit(Opts.ExitCode)
  return True

def FlushCacheOnSource1(Opts):
  DebugFn(Opts)
  MessageFn(Opts,15)
  FnName=inspect.stack()[0][3]
  CxCommand="""CMD /C C:\Automatizacion\FlushCacheE.cmd"""
  if Opts.Server1Type=="windows":
    try:
      WINconnect(Opts,Opts.Server1Name,CxCommand)
    except subprocess.CalledProcessError as e:
      if e.returncode==6:
        sys.stderr.write("•• %s: security problem connecting to %s!\n" % (Opts.PrgName,Opts.Server1Name))
  else:
    sys.stderr.write("%s: dont' know how to flush cache on %s!\n" % (Opts.PrgName,Opts.Server1Name))
    Opts.ExitCode=34
    sys.exit(Opts.ExitCode)
  return True

def ReplicateVolumeOnStorage(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,16)
  FnName=inspect.stack()[0][3]
  if Opts.Storage1Type=="storwize":
    MiniWait(Opts)
    MessageSpecific(Opts,"stopping snapshot pair %s_snapshot_pair1" % (Opts.LUN[Num],))
    CxCommand="stopfcmap %s_snapshot_pair1" % (Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    MiniWait(Opts)
    MessageSpecific(Opts,"preparing snapshot pair %s_snapshot_pair1" % (Opts.LUN[Num],))
    CxCommand="prestartfcmap -restore %s_snapshot_pair1" % (Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    MiniWait(Opts)
    MessageSpecific(Opts,"starting snapshot pair %s_snapshot_pair1" % (Opts.LUN[Num],))
    CxCommand="startfcmap -restore %s_snapshot_pair1" % (Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    MiniWait(Opts)
    MessageSpecific(Opts,"mapping to %s [SCSI ID %s]" % ("SR-"+Opts.VHost2Name,10+Num))
    CxCommand="mkvdiskhostmap -scsi %s -host %s -force %s_snapshot1"%(10+Num,"SR-"+Opts.VHost2Name,Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    MiniWait(Opts)
    MessageSpecific(Opts,"mapping to %s [SCSI ID %s]" % ("SR-"+Opts.VHost1Name,10+Num))
    CxCommand="mkvdiskhostmap -scsi %s -host %s -force %s_snapshot1"%(10+Num,"SR-"+Opts.VHost1Name,Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to replicate volumes on %s!\n" % (Opts.PrgName,Opts.Storage1Name))
    Opts.ExitCode=23
    sys.exit(Opts.ExitCode)
  return True
  
def StartSQLServerOnSource1(Opts):
  DebugFn(Opts)
  MessageFn(Opts,17)
  FnName=inspect.stack()[0][3]
  if Opts.Server1Type=="windows":
    try:
      MessageFn(Opts,18)
      WINconnect(Opts,Opts.Server1Name,Opts.StartSQLServer)
      MessageFn(Opts,19)
      WINconnect(Opts,Opts.Server1Name,Opts.StartSQLServerAgent)
    except subprocess.CalledProcessError as e:
      if e.returncode==2:
        sys.stderr.write("•• %s: SQL Server was started on %s!\n"%(FnName,Opts.Server1Name,))
  else:
    sys.stderr.write("%s: dont' know how to connect and start MS SQL Server on %s!\n" % (Opts.PrgName,Opts.Server1Name))
    Opts.ExitCode=35
    sys.exit(Opts.ExitCode)
  return True
  
def StopSQLServerOnSource2(Opts):
  DebugFn(Opts)
  MessageFn(Opts,20)
  FnName=inspect.stack()[0][3]
  if Opts.Server2Type=="windows":
    try:
      MessageFn(Opts,21)
      WINconnect(Opts,Opts.Server2Name,Opts.StopSQLServerAgent)
      MessageFn(Opts,22)
      WINconnect(Opts,Opts.Server2Name,Opts.StopSQLServer)
    except subprocess.CalledProcessError as e:
      if e.returncode==2:
        sys.stderr.write("•• %s: SQL Server was stopped on %s!\n"%(FnName,Opts.Server2Name,))
  else:
    sys.stderr.write("%s: dont' know how to connect and stop MS SQL Server on %s!\n" % (Opts.PrgName,Opts.Server2Name))
    Opts.ExitCode=36
    sys.exit(Opts.ExitCode)
  return True
  
def FlushCacheOnSource2(Opts):
  DebugFn(Opts)
  MessageFn(Opts,23)
  FnName=inspect.stack()[0][3]
  CxCommand="""CMD /C C:\Automatizacion\FlushCacheE.cmd"""
  if Opts.Server2Type=="windows":
    try:
      WINconnect(Opts,Opts.Server2Name,CxCommand)
    except subprocess.CalledProcessError as e:
      if e.returncode==6:
        sys.stderr.write("•• %s: security problem connecting to %s!\n" % (Opts.PrgName,Opts.Server2Name))
  else:
    sys.stderr.write("%s: dont' know how to flush cache on %s!\n" % (Opts.PrgName,Opts.Server2Name))
    Opts.ExitCode=34
    sys.exit(Opts.ExitCode)
  return True

def StartSQLServerOnSource2(Opts):
  DebugFn(Opts)
  MessageFn(Opts,24)
  FnName=inspect.stack()[0][3]
  if Opts.Server2Type=="windows":
    try:
      MessageFn(Opts,25)
      WINconnect(Opts,Opts.Server2Name,Opts.StartSQLServer)
      MessageFn(Opts,26)
      WINconnect(Opts,Opts.Server2Name,Opts.StartSQLServerAgent)
    except subprocess.CalledProcessError as e:
      if e.returncode==2:
        sys.stderr.write("•• %s: SQL Server was started on %s!\n"%(FnName,Opts.Server2Name,))
  else:
    sys.stderr.write("%s: dont' know how to connect and start MS SQL Server on %s!\n" % (Opts.PrgName,Opts.Server2Name))
    Opts.ExitCode=38
    sys.exit(Opts.ExitCode)
  return True

def RescanSANonVHost(Opts):
  DebugFn(Opts)
  MessageFn(Opts,27)
  FnName=inspect.stack()[0][3]
  Raise=Opts.Raise
  Opts.Raise=False
  # First on virtualization host #1
  if Opts.VHost1Type=="vmware":
    CxCommand="""esxcli storage core adapter rescan --all"""
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
    # Re-Enable LUNs
    CxCommand="""esxcli storage core device set --state=on --device $(cat LUN11DISKNAME.txt)"""
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
    CxCommand="""esxcli storage core device set --state=on --device $(cat LUN12DISKNAME.txt)"""
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to rescan the SAN on %s!\n" % (Opts.PrgName,Opts.VHost1Name))
    Opts.ExitCode=41
    sys.exit(Opts.ExitCode)
  # Then on virtualization host #2
  if Opts.VHost2Type=="vmware":
    CxCommand="""esxcli storage core adapter rescan --all"""
    OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
    # Re-Enable LUNs
    CxCommand="""esxcli storage core device set --state=on --device $(cat LUN11DISKNAME.txt)"""
    OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
    CxCommand="""esxcli storage core device set --state=on --device $(cat LUN12DISKNAME.txt)"""
    OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to rescan the SAN on %s!\n" % (Opts.PrgName,Opts.VHost1Name))
    Opts.ExitCode=41
    sys.exit(Opts.ExitCode)
  Opts.Raise=Raise
  return True

def ListSnapshotOnVHost(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,28)
  FnName=inspect.stack()[0][3]
  if Opts.VHostType=="vmware":
    CxCommand="esxcli storage vmfs snapshot list | awk '/UUID/ {print $3}' | tee SNAPSHOT%sUUID.txt" % (Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    Opts.SnapshotUUID[Num]=OutputText.splitlines()[0]
    MessageSpecific(Opts,"got UUID %s for %s" % (Opts.SnapshotUUID[Num],Opts.CloneDisk[Num]))
    if len(Opts.SnapshotUUID[Num])<35:
      sys.stderr.write("%s: %s could not get %s snapshot UUID! (got %s)\n%s: Exiting...\n"%(Opts.PrgName,FnName,Opts.CloneDisk[Num],Opts.SnapshotUUID[Num],Opts.PrgName))
      Opts.ExitCode=51
      sys.exit(Opts.ExitCode)
    if len(Opts.SnapshotUUID[Num])>35:
      sys.stderr.write("%s: %s got too much for %s snapshot UUID! (got %s)\n%s: Exiting...\n"%(Opts.PrgName,FnName,Opts.CloneDisk[Num],Opts.SnapshotUUID[Num],Opts.PrgName))
      Opts.ExitCode=52
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to list the SAN snapshots on %s!\n" % (Opts.PrgName,Opts.VHost1Name))
    Opts.ExitCode=42
    sys.exit(Opts.ExitCode)
  return True

def ResigSnapshotOnVHost(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,29)
  FnName=inspect.stack()[0][3]
  if Opts.VHostType=="vmware":
    try:
      MessageSpecific(Opts,"resigning snapshot using signature %s" % (Opts.SnapshotUUID[Num],))
      CxCommand="esxcli storage vmfs snapshot resignature -u %s" % (Opts.SnapshotUUID[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    except subprocess.CalledProcessError as e:
      if e.returncode!=0:
        sys.stderr.write("%s: %s (%s) on %s returned %d!\n" % (Opts.PrgName,FnName,CxCommand,Opts.VHostName,e.returncode))
        sys.stderr.write("%s: %s\n" % (Opts.PrgName,OutputText))
  else:
    sys.stderr.write("%s: don't know how to resignature the SAN snapshot on %s!\n" % (Opts.PrgName,Opts.VHostName))
    Opts.ExitCode=43
    sys.exit(Opts.ExitCode)
  return True

def ListSnapshotFSOnVHost(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,30)
  if Opts.VHostType=="vmware":
    CxCommand="esxcli storage filesystem list | awk '/snap.*%s/ {print $1}' | tee SNAPSHOT%sFSNAME.txt" % (Opts.LUN[Num],Opts.LUN[Num],)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    OutputLines=OutputText.splitlines()
    if len(OutputLines[0])>0:
      Opts.SnapshotFS[Num]=OutputLines[0]
      MessageSpecific(Opts,"got name of snapshot FS (%s)" % (OutputLines[0],))
    else:
      sys.stderr.write("%s: could not get snapshot file system name for %s! on %s!\n"%(Opts.PrgName,Opts.CloneDisk[Num],Opts.VHostName))
      Opts.ExitCode=62
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to get the filesystem of the SAN snapshot on %s!\n" % (Opts.PrgName,Opts.VHostName))
    Opts.ExitCode=44
    sys.exit(Opts.ExitCode)
  return True
  
def GetDataStoreInFSOnVHost(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,31)
  if Opts.VHostType=="vmware":
    CxCommand="ls %s | tee SNAPSHOT%sDSNAME.txt" % (Opts.SnapshotFS[Num],Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    if len(OutputText)>0:
      Opts.SnapshotDS[Num]=OutputText.splitlines()[0]
      MessageSpecific(Opts,"found datastore [%s] on file system %s" % (Opts.SnapshotDS[Num],Opts.SnapshotFS[Num]))
    else:
      sys.stderr.write("%s: could not get datastore name for %s!\n"%(Opts.PrgName,Opts.LUN[Num]))
      Opts.ExitCode=63
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to get the datastore of the SAN snapshot on %s!\n" % (Opts.PrgName,Opts.VHostName))
    Opts.ExitCode=45
    sys.exit(Opts.ExitCode)
  return True
  
def GetVMDKInFSOnVHost(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,32)
  if Opts.VHostType=="vmware":
    CxCommand="""ls %s/%s | awk '$NF!~/flat.vmdk/{print $NF}' | tee %sVMDKNAME.txt""" % (Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    if len(OutputText)>0:
      Opts.SnapshotVMDK[Num]=OutputText.splitlines()[0]
      MessageSpecific(Opts,"found virtual disk %s/%s/%s" % (Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.SnapshotVMDK[Num]))
    else:
      sys.stderr.write("%: could not get VMDK name for %s!\n"%(Opts.PrgName,Opts.CloneDisk[Num]))
      Opts.ExitCode=64
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to get the VMDK of the SAN snapshot on %s!\n" % (Opts.PrgName,Opts.VHostName))
    Opts.ExitCode=46
    sys.exit(Opts.ExitCode)
  return True

def AttachCloneDiskToTarget(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,33)
  RescanSANonVHost(Opts)
  ListSnapshotOnVHost(Opts,Num)
  ResigSnapshotOnVHost(Opts,Num)
  ListSnapshotFSOnVHost(Opts,Num)
  GetDataStoreInFSOnVHost(Opts,Num)
  GetVMDKInFSOnVHost(Opts,Num)
  if Opts.VHost1Type=="vmware":
    MessageSpecific(Opts,"trying to attach existing virtual disk %s" %(Num,))
    CxCommand="vim-cmd vmsvc/device.diskaddexisting %s %s/%s/%s %s %s" % (Opts.VMid,Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.SnapshotVMDK[Num],Opts.Controller[1],Opts.CloneDisk[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to attach 1st cloned disk from %s on %s!\n" % (Opts.PrgName,Opts.Server3Name,Opts.VHostName))
    Opts.ExitCode=47
    sys.exit(Opts.ExitCode)
  return True
  
def StartTargetVM(Opts):
  DebugFn(Opts)
  MessageFn(Opts,34)
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.on %s" % (Opts.VMid)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to start %s (%s) on %s!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

def ReassignLetterOnTarget(Opts):
  DebugFn(Opts)
  MessageFn(Opts,35)
  if Opts.Server3Type=="windows":
    CxCommand="""CMD /C C:\Automatizacion\ReassignLetterE2H.cmd"""
    WINconnect(Opts,Opts.Server3Name,CxCommand)
  else:
    sys.stderr.write("%s: dont' know how to change letters on %s!\n" % (Opts.PrgName,Opts.Server3Name))
    Opts.ExitCode=32
    sys.exit(Opts.ExitCode)
  return True

def NFSmounted(Opts):
  DebugFn(Opts)
  MessageFn(Opts,36)
  NFSmountedReturn=False
  if Opts.VHost1Type=="vmware":
    MessageSpecific(Opts,"checking for mounted NFS file systems")
    CxCommand="esxcli storage nfs list | grep -q '^%s' && echo True || echo False" % (Options.NFSvol)
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
    if len(OutputText)>0:
      if OutputText.splitlines()[0]=="True":
        MessageSpecific(Opts,"mounted NFS filesystems? got True")
        NFSmountedReturn=True
    else:
      sys.stderr.write("%s: could not list mounted NFS filesystems on %s!\n"%(Opts.PrgName,Opts.VHost1Name))
      Opts.ExitCode=64
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to list mounts on %s!\n" % (Opts.PrgName,Opts.VHost1Name))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return NFSmountedReturn

def NFSmount(Opts):
  DebugFn(Opts)
  MessageFn(Opts,37)
  if Opts.VHost1Type=="vmware":
    MessageSpecific(Opts,"adding %s:%s like %s" % (Opts.NFS1Name, Opts.NFS1Export, Opts.NFSvol))
    CxCommand="esxcli storage nfs add --host %s --share %s --volume-name %s" % (Opts.NFS1Name, Opts.NFS1Export, Opts.NFSvol)
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know mount %s:%s on %s!\n" % (Opts.PrgName,Opts.NFS1Name,Opts.NFS1Export,Opts.NFSvol))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

def NFSumount(Opts):
  DebugFn(Opts)
  MessageFn(Opts,38)
  if Opts.VHost1Type=="vmware":
    MessageSpecific(Opts,"removing NFS %s" % (Opts.NFSvol,))
    CxCommand="esxcli storage nfs remove --volume-name %s" % (Opts.NFSvol)
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
  else:
    sys.stderr.write("%s: don't know how to umount %s:%s (%s)!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHost1Name))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

def AttachNFSVMDK(Opts,FSDSpath,Num):
  DebugFn(Opts)
  MessageFn(Opts,39)
  if Opts.VHost1Type=="vmware":
    # Find VMDK
    MessageSpecific(Opts,"searching for virtual disk on %s" %(FSDSpath,))
    CxCommand="ls -1 %s | awk '/\.vmdk$/ && $NF!~/flat.vmdk/{print $NF}'" % (FSDSpath,)
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
    if len(OutputText[0])>0:
      NFSVMDK=OutputText.splitlines()[0]
      # Attach VMDK
      MessageSpecific(Opts,"VMDK found (%s), trying to attach to target VM (%s)" %(NFSVMDK,Opts.Server3VMname))
      CxCommand="vim-cmd vmsvc/device.diskaddexisting %s %s/%s %s %s" % (Opts.VMid,FSDSpath,NFSVMDK,Opts.Controller[1],Num)
      OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
    else:
      sys.stderr.write("%s: could not get snapshot file system name for %s!\n"%(Opts.PrgName,Opts.CloneDisk[Num]))
      Opts.ExitCode=62
      sys.exit(Opts.ExitCode)
  else:
    sys.stderr.write("%s: don't know how to umount %s:%s (%s)!\n" % (Opts.PrgName,Opts.Server3Name,Opts.Server3VMname,Opts.VHost1Name))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

def AttachNFSDiskToTarget(Opts,Num):
  DebugFn(Opts)
  MessageFn(Opts,40)
  # WARNING # CONSTANT VALUES HERE
  LocalDisksOffset=10
  SANDisksOffset=2
  if Opts.VHost1Type=="vmware":
    if NFSmounted(Opts):
      NFSfilesystem="/vmfs/volumes/%s/" % (Opts.NFSvol)
      CxCommand="ls -1 %s" % (NFSfilesystem,)
      MessageSpecific(Opts,"looking on %s" %(NFSfilesystem,))
      OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
      if len(OutputText)>0:
        OutputLines=OutputText.splitlines()
        for DS in Opts.NFSDS[Num:]:
          DSindex=OutputLines.index(DS)
          VMDKfullPath="%s%s" %(NFSfilesystem,OutputLines[DSindex])
          MessageSpecific(Opts,"found %s" %(VMDKfullPath,))
          AttachNFSVMDK(Opts,VMDKfullPath,LocalDisksOffset+SANDisksOffset+Num)
  else:
    sys.stderr.write("%s: don't know how to attach NFS virtual disks on %s!\n" % (Opts.PrgName,Opts.VHost1Name))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

# ------------------------------------------------------------------------------------------------------
# Start of main()
PrgName="CtrlDbRepl"

try:
  parser=OptionParser(usage="%prog [ --OPTIONS ]")
  parser.add_option("-q", dest="Verbose", action="store_false", default=True, help="Quiet mode. Don't show messages")
  parser.add_option("-o", "--output", dest="LogFile", action="store", type="string", help="Log execution into file name", default="%s.log" % (PrgName,))
  parser.add_option("-d", "--workdir", dest="WorkDir", action="store", type="string", help="Working directory", default="M:\Automatizacion")
  parser.add_option("-r", "--ur", "--remote-unix-command", dest="RemoteUnixCommand", action="store", type="string", help="Remote execution command for Unix connections", default="plink")
  parser.add_option("-R", "--wr", "--remote-windows-command", dest="RemoteWindowsCommand", action="store", type="string", help="Remote execution command for Windows connections", default="psexec")
  parser.add_option("--s1n", "--server1name", dest="Server1Name", action="store", type="string", help="Server #1 hostname", default="SR-SQL1CO")
  parser.add_option("--s1u", "--server1user", dest="Server1User", action="store", type="string", help="Server #1 username to connect to", default="sqlservice")
  parser.add_option("--s1t", "--server1type", dest="Server1Type", action="store", type="string", help="Server #1 type of OS", default="windows")
  parser.add_option("--s2n", "--server2name", dest="Server2Name", action="store", type="string", help="Server #1 hostname", default="SR-SQL2CO")
  parser.add_option("--s2u", "--server2user", dest="Server2User", action="store", type="string", help="Server #1 username to connect to", default="sqlservice")
  parser.add_option("--s2t", "--server2type", dest="Server2Type", action="store", type="string", help="Server #1 type of OS", default="windows")
  parser.add_option("--s3n", "--server3name", dest="Server3Name", action="store", type="string", help="Server #1 hostname", default="SR-SQLREP01")
  parser.add_option("--s3u", "--server3user", dest="Server3User", action="store", type="string", help="Server #1 username to connect to", default="sqlservice")
  parser.add_option("--s3t", "--server3type", dest="Server3Type", action="store", type="string", help="Server #1 type of OS", default="windows")
  parser.add_option("--t1n", "--storage1name", dest="Storage1Name", action="store", type="string", help="Storage server #1 hostname", default="V3700")
  parser.add_option("--t1u", "--storage1user", dest="Storage1User", action="store", type="string", help="Storage server #1 username to connect to", default="soporte")
  parser.add_option("--t1t", "--storage1type", dest="Storage1Type", action="store", type="string", help="Storage server #1 type of OS", default="storwize")
  parser.add_option("--v1n", "--vhost1name", dest="VHost1Name", action="store", type="string", help="Virtualization host #1 hostname", default="ESX11CO")
  parser.add_option("--v1u", "--vhost1user", dest="VHost1User", action="store", type="string", help="Virtualization host #1 username to connect to", default="root")
  parser.add_option("--v1t", "--vhost1type", dest="VHost1Type", action="store", type="string", help="Virtualization host #1 type of OS", default="vmware")
  parser.add_option("--v2n", "--vhost2name", dest="VHost2Name", action="store", type="string", help="Virtualization host #2 hostname", default="ESX06CO")
  parser.add_option("--v2u", "--vhost2user", dest="VHost2User", action="store", type="string", help="Virtualization host #2 username to connect to", default="root")
  parser.add_option("--v2t", "--vhost2type", dest="VHost2Type", action="store", type="string", help="Virtualization host #2 type of OS", default="vmware")
  parser.add_option("--n1n", "--nfs1hostname", dest="NFS1Name", action="store", type="string", help="NFS server #1 hostname", default="192.168.20.146")
  parser.add_option("--n1e", "--nfs1export", dest="NFS1Export", action="store", type="string", help="NFS server #1 export", default="/export/db1-clone")
  parser.add_option("-w", "--shutdown-wait", dest="ShutdownWait", action="store", type="int", help=SUPPRESS_HELP, default=30)
  parser.add_option("-C", "--only-clean", "--clean-only", dest="OnlyClean", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGUNIX", dest="DEBUGUNIX", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGWINDOWS", dest="DEBUGWINDOWS", action="store_true", default=False, help=SUPPRESS_HELP)

  (Options, Args)=parser.parse_args()
  Options.PrgName=PrgName
  Options.ExitCode=0
  # Internal variables
  Options.NoWaitOnDebug=True
  Options.Server3VMname=Options.Server3Name[3:]
  Options.Controller=[0,0]
  Options.CloneDisk=[0,11,12,13,14,15]
  # Options.RemoveLetterGscript="RemoveLetterG.scr"
  # Options.RemoveLetterHscript="RemoveLetterH.scr"
  Options.LUN=[0,"LDB1","LDB2"]
  Options.VMid=""
  Options.VMstate=""
  Options.SnapshotUUID=[0,"",""]
  Options.SnapshotDS=[0,"",""]
  Options.SnapshotFS=[0,"",""]
  Options.SnapshotVMDK=[0,"",""]
  # Options.StopSQLServer='NET STOP "SQL Server (MSSQLSERVER)"'
  # Options.StopSQLServerAgent='NET STOP "SQL Server Agent (MSSQLSERVER)"'
  # Options.StartSQLServer='NET START "SQL Server (MSSQLSERVER)"'
  # Options.StartSQLServerAgent='NET START "SQL Server Agent (MSSQLSERVER)"'
  # Options.NFSvol=Options.NFS1Export.split("/")[-1].upper()
  # Options.NFSDS=[0,"SR-SQLPAIS01","SR-SQLCIAS02","SR-SQLGPCOMPRAS01"]
  # Options.NFSVMDK=[0,"SR-SQLPAIS01","SR-SQLCAS02_1","SR-SQLGPCOMPRAS01"]
  Options.MiniWait=3
  Options.Raise=True
  Options.VMre='SQLREP.*1CO'
  if (random.randint(1,10) % 2)==0:
    # if even number, use virtualization host #2
    Options.VHostUser=Options.VHost2User
    Options.VHostName=Options.VHost2Name
    Options.VHostType=Options.VHost2Type
  else:
    # if odd number, use virtualization host #1
    Options.VHostUser=Options.VHost1User
    Options.VHostName=Options.VHost1Name
    Options.VHostType=Options.VHost1Type

  TimeStr="%4d/%2d/%2d %d:%02d:%02d" % (time.localtime(time.time())[0:6])
  sys.stdout.write("------------------------------------------------------------------------\n")
  if Options.OnlyClean:
    sys.stdout.write("%s starting to clean at %s\n"%(Options.PrgName,TimeStr))
  else:
    sys.stdout.write("%s starting out at %s\n"%(Options.PrgName,TimeStr))
  # ----------------------------------------------------------- Only for connectivity tests
  if Options.DEBUGWINDOWS:
    Options.DEBUG=True
    if len(Args)>0:
      for OneName in Args:
        WINconnect(Options,OneName,"ping %s"%(OneName))
    else:
      WINconnect(Options,"SR-SQL01CO","ping 192.168.20.1")
    sys.exit(0)
  if Options.DEBUGUNIX:
    Options.DEBUG=True
    if len(Args)>0:
      for OneName in Args:
        UNIXconnect(Options,"root",OneName,"ping %s"%(OneName,))
    else:
      UNIXconnect(Options,"root","ESX11CO","ping 192.168.20.1")
    sys.exit(0)
  # ----------------------------------------------------------- Only for connectivity tests
  
  # Change to working directory
  if not Options.DEBUG:
    os.chdir(Options.WorkDir)
    
  #Prepare target form new replication
  GetVirtualMachine(Options,Options.Server3VMname)
  GetVirtualMachineState(Options)
  if Options.VMstate != "PoweredOff":
    ShutdownTarget(Options)             # if not poweredOff, try shutdown
    WaitSeconds(Options)                # wait a little while
    GetVirtualMachineState(Options)     
    if Options.VMstate != "PoweredOff":
      PowerOffTarget(Options)           # the POWER OFF
  for i in range(2):                    # range(x) goes from 0 to x-1, change to number of disks
    RemoveCloneOnTarget(Options,i+1)
  UnmapCloneLun(Options,1)
  UnmapCloneLun(Options,2)
#  if NFSmounted(Options):
 #   NFSumount(Options)
  RescanSANonVHost(Options)

  if Options.OnlyClean:
    TimeStr="%4d/%2d/%2d %d:%02d:%02d" % (time.localtime(time.time())[0:6])
    sys.stdout.write("%s ending at %s\n"%(Options.PrgName,TimeStr))
    sys.stdout.write("------------------------------------------------------------------------\n")
    sys.exit(0)
    
  # Prepare 1st source for new replication
  # StopSQLServerOnSource1(Options)
  FlushCacheOnSource1(Options)
  
  # Do new snapshot for 1st source
  ReplicateVolumeOnStorage(Options,1)
  
  # Re-start 1st source
  # StartSQLServerOnSource1(Options)
  
  # Assign cloned disks to target
  AttachCloneDiskToTarget(Options,1)

  # Prepare 2nd source for new replication
  # StopSQLServerOnSource2(Options)
  FlushCacheOnSource2(Options)
  
  # Do new snapshot for 2nd source
  ReplicateVolumeOnStorage(Options,2)
  
  # Re-start 2nd source
  # StartSQLServerOnSource2(Options)
  
  # Assign cloned disks to target
  AttachCloneDiskToTarget(Options,2)
  
  # Mount NFS shared
  #if not NFSmounted(Options):
   # NFSmount(Options)
  
  # Attach selected datastores
  # AttachNFSDiskToTarget(Options,1)
  # AttachNFSDiskToTarget(Options,2)
  # AttachNFSDiskToTarget(Options,3)
  
  # Re-start target
  StartTargetVM(Options)
  WaitSeconds(Options)
#  ReassignLetterOnTarget(Options)
  TimeStr="%4d/%2d/%2d %d:%02d:%02d" % (time.localtime(time.time())[0:6])
  sys.stdout.write("%s ending at %s\n"%(Options.PrgName,TimeStr))
  sys.stdout.write("------------------------------------------------------------------------\n")
  
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Options.PrgName))
  sys.stderr.flush()
except IOError:
  sys.stderr.write("\n%s: IO Error changing directory to %s!\n" % (Options.PrgName,Options.WorkDir))
  sys.stderr.flush()
except:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName,))
  sys.stderr.flush()

# --------------------------------------------------------------------------------
# ASSERTS:
# PythonWin or ActivePython installed on machine running script
# On Windows servers:
#   Directory C:\Automatizacion
#   Command   C:\Automatizacion\PSEXEC.exe
#   Command   C:\Automatizacion\PLINK.exe
#   File      C:\Automatizacion\windowsprivdsa.ppk
#   ### This is user PRIVATE DSA KEY ###
#   File      C:\Automatizacion\windowspubdsa
# Must be a V3700 host definition on PuTTY saved, with priv/pub DSA keys defined
# Must be a ESX11CO host definition on PuTTY saved with priv/pub DSA keys defined
# On VMware ESX and on Storwize Storage servers:
#   windowspubdsa installed
#   ### This is user PUBLIC DSA KEY  ###
#
# --------------------------------------------------------------------------------
# Ramon Barrios Lascar, 2013, Ínodo S.A.S.
# --------------------------------------------------------------------------------
