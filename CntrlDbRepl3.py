#!/usr/bin/python
# encoding: utf-8
"""
CntrlDbRepl3.py: Control database LUN replication
Created by Ramón Barrios Láscar on 2013/10/17
Last mod by Ramón Barrios Láscar on 2014/04/02
Copyright (c) 2013, 2014 Ínodo. All rights reserved
"""

import sys, os, time, re, inspect, subprocess
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn(Opts):
  if Opts.DEBUG:
    sys.stderr.write(" • %s\n"%(inspect.stack()[1][3]),)
  return

def FileLog(Opts,Message):
  if not Opts.NoLog:
    TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
    LogF=open(Opts.LogFile, "a")
    LogF.write("%s: %s %s\n"%(Opts.PrgName,TimeStr,Message))
    LogF.close()
  return

def Msg(Opts,Message):
  if Opts.Verbose:
    sys.stdout.write("%s: %s\n"%(Opts.PrgName,Message))
  FileLog(Opts,Message)
  return
  
def ErrMsg(Opts,Message):
  sys.stderr.write("%s: ERROR %s\n"%(Opts.PrgName,Message))
  sys.stderr.flush()
  FileLog(Opts,"ERROR %s"%(Message,))
  return
      
def WaitSeconds(Opts):
  Msg(Opts,"waiting...")
  if Opts.DEBUG and Opts.NoWaitOnDebug:
    sys.stderr.write(" • WaitSeconds(NoWaitOnDebug)\n")
  else:
    time.sleep(Opts.ShutdownWait)
  return True

def MiniWait(Opts):
  if not Opts.DEBUG:
    time.sleep(Opts.MiniWait)
  return True

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

def GetVolumeSize(Opts,VolumeName):
  """Return the size of VolumeName or 0 (zero)"""
  DebugFn(Opts)
  Msg(Opts,"trying to get size of %s..."%(VolumeName,) )
  ReturnedSize=0
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="lsvdisk -bytes -delim : %s"%(VolumeName,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          if TextLine.startswith("capacity"):
            CapacityLine=TextLine
            break # of for
        CapacityInBytes=CapacityLine.split(":")[1]
        ReturnedSize=int(CapacityInBytes)
        Msg(Opts,"found size (%dB) for %s"%(ReturnedSize,VolumeName))
    finally:
      return ReturnedSize
  else:
    return ReturnedSize # 0

def GetListOfNamedSnaps(Opts,VolumeName):
  """Get the list of volumes (clones) with VolumeName like base name"""
  DebugFn(Opts)
  Msg(Opts,"trying to get the list of snapshots of %s..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      VolumeList=[]
      CxCommand="lsvdisk -bytes"
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          SecondWord=TextLine.split()[1]
          if SecondWord.startswith("%s_c_" % (VolumeName,)):
            # Append to result list
            # Msg(Opts,"%s volume found" % (SecondWord,))
            VolumeList.append(SecondWord)
        return VolumeList
      else:
        return []
    except:
      return []
  else:
    return []

def CountNamedSnaps(Opts,VolumeName):
  """Count how many snapshots a VolumeName has"""
  DebugFn(Opts)
  Msg(Opts,"trying to count snapshots for volume %s"%(VolumeName,))
  return len(GetListOfNamedSnaps(Opts,VolumeName))

def GetNameOfFirstNamedSnap(Opts,VolumeName):
  """Get name of first volume (snapshot) with VolumeName like base name"""
  DebugFn(Opts)
  Msg(Opts,"trying to get first snapshot for %s"%(VolumeName,))
  return sorted(GetListOfNamedSnaps(Opts,VolumeName),reverse=False)[0]
  
def GetNameOfLastNamedSnap(Opts,VolumeName):
  """Get name of first volume (snapshot) with VolumeName like base name"""
  DebugFn(Opts)
  Msg(Opts,"trying to get last snapshot for %s"%(VolumeName,))
  return sorted(GetListOfNamedSnaps(Opts,VolumeName),reverse=True)[0]

def GetVMID(Opts,VMname):
  """Get the VMID of a named virtual machine. Stores the VMID on Opts.VMid"""
  DebugFn(Opts)
  Msg(Opts,"trying to get the VMID of virtual machine \"%s\""%(VMname))
  if Opts.VHost1Type=="vmware":
    CxCommand="vim-cmd vmsvc/getallvms | awk '$2~/%s$/ {print $1}' | tee %sVM.txt"%(Opts.VMre,Opts.Server3VMname,)
    try:
      OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
      Opts.VMid=OutputText.splitlines()[0]
      if len(Opts.VMid)==0:
        ErrMsg(Opts,"could not get the VM ID of %s, exiting..."%(Opts.Server3Name,))
        Opts.ExitCode=50
        sys.exit(Opts.ExitCode)
      Opts.VHostType=Opts.VHost1Type
      Opts.VHostName=Opts.VHost1Name
      Opts.VHostUser=Opts.VHost1User
    except IndexError:
      try:
        OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
        Opts.VMid=OutputText.splitlines()[0]
        if len(Opts.VMid)==0:
          ErrMsg(Opts,"could not get the VM ID of %s, exiting..."%(Opts.Server3Name,))
          Opts.ExitCode=50
          sys.exit(Opts.ExitCode)
        Opts.VHostType=Opts.VHost2Type
        Opts.VHostName=Opts.VHost2Name
        Opts.VHostUser=Opts.VHost2User
      except IndexError:
        Opts.ExitCode=50
        sys.exit(Opts.ExitCode)
  else:
    ErrMsg(Opts,"don't know how to shutdown %s (%s) on %s!"%(Opts.Server3Name,Opts.Server3VMname,Opts.VHost1Name))
    Opts.ExitCode=10
    sys.exit(Opts.ExitCode)
  Msg(Opts,"got %s for %s"%(Opts.VMid,VMname))
  return True
    
def GetTargetVMState(Opts):
  """Get the power state of the VM Opts.#VMID and stores it in Opts.VMstate"""
  DebugFn(Opts)
  Msg(Opts,"trying to get the state of VM #%s..."%(Opts.VMid,))
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.getstate %s | tail -1 | sed 's/power/Power/g;s/on/On/;s/off/Off/;s/ //g'"%(Opts.VMid)
    try:
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      Opts.VMstate=OutputText.splitlines()[0]
      if len(Opts.VMid)==0:
        ErrMsg(Opts,"could not get the state of VM %s (%s) on %s, exiting..."%(Opts.Server3Name,Opts.VMid,Opts.VHostName))
        Opts.ExitCode=51
        sys.exit(Opts.ExitCode)
      Msg(Opts,"got %s for VM #%s"%(Opts.VMstate,Opts.VMid))
    except IndexError:
      ErrMsg(Opts,"could not get the state of VM %s (%s) on %s, exiting..."%(Opts.Server3Name,Opts.VMid,Opts.VHostName))
      Opts.ExitCode=51
      sys.exit(Opts.ExitCode)
  return True

def ShutdownTargetVM(Opts):
  """Shuts down the target VM (with VMID on Opts.VMid)"""
  DebugFn(Opts)
  Msg(Opts,"trying to shutdown VM #%s..."%(Opts.VMid,))
  if Opts.VHostType=="vmware":
    if Opts.VMstate != "PoweredOff":
      CxCommand="vim-cmd vmsvc/power.shutdown %s 2>&1| awk '/existingState/{print substr($3,2,length($3)-3)}' " % (Opts.VMid,)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      if len(OutputText)>0 and len(OutputText.splitlines()[0])>0:
        Opts.VMstate=OutputText.splitlines()[0]
      Msg(Opts,"shutdown order sent for VM #%s"%(Opts.VMid,))
  else:
    ErrMsg(Opts,"don't know how to shutdown %s (%s) on %s!"%(Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=11
    sys.exit(Opts.ExitCode)
  return True

def PowerOffTargetVM(Opts):
  """Immediately powers off the target VM (with VMID on Opts.VMid)"""
  DebugFn(Opts)
  Msg(Opts,"trying to power off VM #%s"%(Opts.VMid,))
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.off %s" % (Opts.VMid,)
    UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    ErrMsg(Opts,"don't know how to stop %s (%s) on %s!"%(Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=12
    sys.exit(Opts.ExitCode)
  return True

def RemoveCloneOnTarget(Opts,Num):
  """Removes a VMDK from the target VM (with VMDK attached like disk #Num, and VMID on Opts.VMid)"""
  DebugFn(Opts)
  Msg(Opts,"trying to remove disk %s from VM #%s..." % (Num,Opts.VMid))
  Opts.Raise=False
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/device.diskremove %s %s %s false" % (Opts.VMid,Opts.Controller[1],Num)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    Opts.Raise=True
  else:
    ErrMsg(Opts,"don't know how to remove cloned disk #%s (%s) from %s on %s!"%(Num,Opts.CloneDisk[Num],Opts.Server3Name,Opts.VHostName))
    Opts.ExitCode=13
    sys.exit(Opts.ExitCode)
  return True

def UnmapLunForHost(Opts,HostName,VolumeName):
  """Removes snapshot clone mapping whose names start with VolumeName and host names are in Options.VHostNName"""
  DebugFn(Opts)
  Msg(Opts,"tring to unmap volume %s from ESX hosts %s"%(VolumeName,HostName))
  if Opts.Storage1Type=="storwize":
    try:
      if HostName==HostName.split("-")[0]:
        HostName="SR-%s"%(HostName,)
      CxCommand="rmvdiskhostmap -host %s %s"%(HostName,VolumeName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Msg(Opts,"volume %s unmapped from %s"%(VolumeName,HostName))
    except:
      ErrMsg(Opts,"error unmapping volume %s for %s"%(VolumeName,HostName))
  else:
    ErrMsg(Opts,"don't know how to unmap LUNs for %s"%(Opts.Storage1Type,))
    return False
  return True

def ListMappedVolumesForHost(Opts,HostName):
  """Stores the list of storwize mapped volumes for HostName. Only stores volumes with SCSI ID >= ScsiOffset
  On error the list is empty"""
  DebugFn(Opts)
  Msg(Opts,"trying to list volumes from %s mapped to %s..."%(Opts.Storage1Name,HostName))
  HostPrefix="SR-"
  Opts.MappedVolume=[]
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="lshostvdiskmap -nohdr %s%s"%(HostPrefix,HostName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if OutputText and len(OutputText)>0:
        for OutputLine in OutputText.splitlines():
          if OutputLine and len(OutputLine)>0:
            MappedHostName=OutputLine.split()[1]
            if MappedHostName and MappedHostName==(HostPrefix+HostName):
              TextMappedScsiId=OutputLine.split()[2]
              if TextMappedScsiId and len(TextMappedScsiId)>0:
                try:
                  MappedScsiId=int(TextMappedScsiId)
                  if MappedScsiId>=Opts.ScsiOffset:
                    MappedVolume=OutputLine.split()[4]
                    Opts.MappedVolume.append(MappedVolume)
                    Msg(Opts,"volumes found mapped %s"%(Opts.MappedVolume,))
                except TypeError:
                  ErrorMsg(Opts,"problem interpreting the list of mapped volumes for %s at %s"%(HostName,Opts.Storage1Name))
      return Opts.MappedVolume
    except:
      ErrMsg(Opts,"problem gettting the list of volumes mapped to %s%s"%(HostPrefix,HostName))
      return []
  else:
    ErrMsg(Opts,"don't know how to list mapped volumes for %s"%(Opts.Storage1Type,))
    return []

def UnmapAllCloneLun(Opts):
  """Remove all LUN mappings greater than ScsiOffset"""
  DebugFn(Opts)
  Msg(Opts,"removing mappings of old clone volumes from VMware ESX hosts...")
  if Opts.Storage1Type=="storwize":
    for ESXHost in [ Opts.VHost1Name, Opts.VHost2Name]:
     try:
       for MappedVolume in ListMappedVolumesForHost(Opts,ESXHost):
         UnmapLunForHost(Opts,ESXHost,MappedVolume)
     except:
       ErrMsg(Opts,"error removeing old mapped volumes for %s"%(ESXHost,))
  else:
    ErrMsg(Opts,"don't know how to unmap from %s" % (Opts.Storage1Name,))
  return True
  
def RescanSANonVHosts(Opts):
  """Rescan the san in both ESX hosts"""
  DebugFn(Opts)
  Msg(Opts,"rescanning SAN on ESX hosts...")
  Raise=Opts.Raise
  Opts.Raise=False
  # First on virtualization host #1
  if Opts.VHost1Type=="vmware":
    CxCommand="""esxcli storage core adapter rescan --all"""
    OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
  else:
    ErrMsg(Opts,"don't know how to rescan the SAN on %s!"%(Opts.VHost1Name,))
    Opts.ExitCode=41
    sys.exit(Opts.ExitCode)
  # Then on virtualization host #2
  if Opts.VHost2Type=="vmware":
    CxCommand="""esxcli storage core adapter rescan --all"""
    OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
  else:
    ErrMsg(Opts,"don't know how to rescan the SAN on %s!\n"%(Opts.VHost1Name,))
    Opts.ExitCode=41
    sys.exit(Opts.ExitCode)
  Opts.Raise=Raise
  return True

def ListSnapshotOnVHost(Opts,Num):
  DebugFn(Opts)
  Msg(Opts,"trying to get the list of snapshot volumes attached to VMware eSX hosts...")
  if Opts.VHostType=="vmware":
    try:
      CxCommand="esxcli storage vmfs snapshot list | awk '/UUID/ {print $3}' | tee SNAPSHOT%sUUID.txt" % (Opts.LUN[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      for OutputLine in OutputText.splitlines():
        if OutputLine and len(OutputLine)>0:
          SnapshotUUID=OutputLine.split()[0]
          if len(SnapshotUUID)==35:
            Msg(Opts,"found UUID %s"%(SnapshotUUID,))
            Opts.SnapshotUUID.append(SnapshotUUID)
          elif len(SnapshotUUID)>35:
            ErrMsg(Opts,"got too much for UUID (%s), exiting..."%(SnapshotUUID,))
            Opts.ExitCode=51
            sys.exit(Opts.ExitCode)
          else:
            ErrMsg(Opts,"got too little for UUID (%s), exiting..."%(SnapshotUUID,))
            Opts.ExitCode=25
            sys.exit(Opts.ExitCode)
    except:
      ErrMsg(Opts,"could not get UUID for LUN %s!"%(Opts.LUN[Num],))
  else:
    ErrMsg(Opts,"don't know how to list the SAN snapshots on %s!"%(Opts.VHost1Name,))
    Opts.ExitCode=42
    sys.exit(Opts.ExitCode)
  return True

def ListMountedSnapshotFSOnVHost(Opts):
  DebugFn(Opts)
  Msg(Opts,"trying to get the list of mounted snapshot filesystems on VMware ESX hosts...")
  if Opts.VHostType=="vmware":
    try:
      Msg(Opts,"getting mounted snapshots on %s" % (Opts.VHostName,))
      CxCommand="esxcli storage filesystem list | awk '$2~/snap-.*-/&&$4==\"true\"{print $1}' | tee SNAPSHOTFSs.txt"
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      for OutputLine in OutputText.splitlines():
        if OutputLine and len(OutputLine)>0:
          SnapshotFS=OutputLine.split()[0]
          if len(SnapshotFS)>0:
            Msg(Opts,"found FS %s"%(SnapshotFS,))
            Opts.SnapshotFS.append(SnapshotFS)
          else:
            ErrMsg(Opts,"could not find FS")
    except:
      ErrMsg(Opts,"error listing mounted snapshots on %s!"%(Opts.VHostName,))
      Opts.ExisCode=43
      sys.exit(Opts.ExitCode)
    return True
  else:
    return False

def ResigSnapshotOnVHost(Opts,Num):
  """Create new identity for filesystem on cloned volume"""
  DebugFn(Opts)
  Msg(Opts,"trying to resignature snapshot of volume %s..."%(Opts.LUN[Num],))
  FnName=inspect.stack()[0][3]
  if Opts.VHostType=="vmware":
    try:
      Msg(Opts,"resigning snapshot of %s using signature %s" %(Opts.LUN[Num],Opts.SnapshotUUID[Num],))
      CxCommand="esxcli storage vmfs snapshot resignature -u %s"%(Opts.SnapshotUUID[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      MiniWait(Opts)
      Msg(Opts,"getting new UUID for snapshot of %s"%(Opts.LUN[Num],))
      CxCommand="esxcli storage filesystem list | awk '$0~/snap/ && $0~/%s/{print substr($0,72,35)}'"%(Opts.LUN[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      if OutputText and len(OutputText)>0:
        OutputLine=OutputText.splitlines()[0]
        if OutputLine and len(OutputLine)>0:
          Opts.SnapshotUUID[Num]=OutputLine.split()[0]
        else:
          raise
      else:
        raise
      Msg(Opts,"unmounting snapshot filesystem with UUID %s"%(Opts.SnapshotUUID[Num],))
      CxCommand="esxcli storage filesystem unmount -u %s"%(Opts.SnapshotUUID[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    except subprocess.CalledProcessError as e:
      if e.returncode!=0:
        ErrMsg(Opts,"%s (%s) on %s returned %d!"%(FnName,CxCommand,Opts.VHostName,e.returncode))
        ErrMsg(Opts,"%s"%(OutputText,))
  else:
    ErrMsg(Opts,"don't know how to resignature the SAN snapshot on %s!"%(Opts.VHostName,))
    Opts.ExitCode=43
    sys.exit(Opts.ExitCode)
  return True

def MountSnapshotOnVHosts(Opts,Num):
  """Create new identity for filesystem on cloned volume"""
  DebugFn(Opts)
  Msg(Opts,"trying to mount snapshot %s..."%(Opts.SnapshotUUID[Num],))
  if Opts.VHostType=="vmware":
    try:
      Msg(Opts,"mounting (temporary) snapshot using signature %s" %(Opts.SnapshotUUID[Num],))
      CxCommand="esxcli storage filesystem mount -u %s"%(Opts.SnapshotUUID[Num],)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    except subprocess.CalledProcessError as e:
      if e.returncode!=0:
        ErrMsg(Opts,"%s"%(OutputText,))
  else:
    ErrMsg(Opts,"don't know how to resignature the SAN snapshot on %s!"%(Opts.VHostName,))
    Opts.ExitCode=43
    sys.exit(Opts.ExitCode)
  return True

def ListSnapshotFSOnVHost(Opts,Num):
  DebugFn(Opts)
  Msg(Opts,"trying to get filesystem names of snapshot/clone volume on ESX host...")
  if Opts.VHostType=="vmware":
    CxCommand="esxcli storage filesystem list | awk '$2~/snap-.*%s/ {print $1}' | tee SNAPSHOT%sFSNAME.txt" % (Opts.LUN[Num],Opts.LUN[Num],)
    # GET FS NAME
    try:
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      OutputLines=OutputText.splitlines()
      if len(OutputLines)>0 and len(OutputLines[0])>0:
        if len(Opts.SnapshotFS)<(Num+1):
          Opts.SnapshotFS.append(OutputLines[0].split()[0])
        else:
          Opts.SnapshotFS[Num]=OutputLines[0].split()[0]
        Msg(Opts,"got name of snapshot FS (%s)" % (OutputLines[0],))
      else:
        ErrMsg(Opts,"could not get snapshot file system name for %s! on %s!"%(Opts.LUN[Num],Opts.VHostName))
        return False
    except IndexError:
      ErrMsg(Opts,"could not get snapshot file system name for %s! on %s!\n"%(Opts.LUN[Num],Opts.VHostName))
      return False
    # GET NAA
    CxCommand="esxcli storage vmfs extent list | awk '$1~/snap.*%s/ {print $4}' | tee SNAPSHOT%sNAA.txt" % (Opts.LUN[Num],Opts.LUN[Num],)
    try:
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      OutputLines=OutputText.splitlines()
      if len(OutputLines)>0 and len(OutputLines[0])>0:
        if len(Opts.SnapshotNAA)<(Num+1):
          Opts.SnapshotNAA.append(OutputLines[0].split()[0])
        else:
          Opts.SnapshotNAA[Num]=OutputLines[0].split()[0]
        Msg(Opts,"got name of NAA for FS (%s)" % (OutputLines[0],))
      else:
        ErrMsg(Opts,"could not get snapshot NAA for %s! on %s!"%(Opts.LUN[Num],Opts.VHostName))
        return False
    except IndexError:
      ErrMsg(Opts,"could not get snapshot NAA for %s! on %s!"%(Opts.LUN[Num],Opts.VHostName))
      return False
  else:
    ErrMsg(Opts,"don't know how to get the NAA the SAN snapshot on %s!"%(Opts.VHostName,))
    Opts.ExitCode=44
    sys.exit(Opts.ExitCode)
  return True
  
def GetDataStoreInFSOnVHost(Opts,Num):
  DebugFn(Opts)
  Msg(Opts,"trying to search for datastores in FS %s..."%(Opts.SnapshotFS[Num],))
  if Opts.VHostType=="vmware":
    CxCommand="ls %s | tee SNAPSHOT%sDSNAME.txt" % (Opts.SnapshotFS[Num],Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    OutputLines=OutputText.splitlines()
    if len(OutputLines)>0 and len(OutputLines[0])>0:
      if len(Opts.SnapshotDS)<(Num+1):
        Opts.SnapshotDS.append(OutputLines[0].split()[0])
      else:
        Opts.SnapshotDS[Num]=OutputLines[0].split()[0]
      Msg(Opts,"found datastore [%s] on file system %s" % (Opts.SnapshotDS[Num],Opts.SnapshotFS[Num]))
    else:
      ErrMsg(Opts,"could not get datastore name for %s!"%(Opts.LUN[Num],))
      Opts.ExitCode=63
      sys.exit(Opts.ExitCode)
  else:
    ErrMsg(Opts,"don't know how to get the datastore of the SAN snapshot on %s!"%(Opts.VHostName,))
    Opts.ExitCode=45
    sys.exit(Opts.ExitCode)
  return True

def GetDataStoresOnVHost(Opts,FSName):
  """Gets datastores on root of filesystem FSName given. Adds them to Opts.SnapshotDS list"""
  DebugFn(Opts)
  Msg(Opts,"trying to search for datastores on '%s'..."%(FSName,))
  if Opts.VHostType=="vmware":
    try:
      CxCommand="ls -1 '%s'"%(FSName,)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      if OutputText and len(OutputText)>0:
        for OutputLine in OutputText.splitlines():
          if OutputLine and len(OutputLine)>0 and OutputLine.split()[0] and len(OutputLine.split()[0])>0:
            DatastoreName=OutputLine.split()[0]
            Msg(Opts,"found datastore [%s] on filesystem '%s'"%(DatastoreName,FSName))
            Opts.SnapshotDS.append(DatastoreName)
        return True
      else:
        Msg(Opts,"no datastores found on filesystem '%s'"%(FSName,))
        return False
    except:
      ErrMsg(Opts,"problem listing datastores on filesystem '%s'"%(FSName,))
      return False
  else:
    ErrMsg(Opts,"don't know how to list datastores for servers of type '%s'"%(Opts.VHostType,))
    Opts.ExitCode=46
    sys.exit(Opts.ExitCode)
  
def GetVMDKsOnVHost(Opts,FSName):
  """Get VMDKs on datastores on filesystem FSName given. Adds them to Opts.SnapshotVMDK"""
  DebugFn(Opts)
  Msg(Opts,"trying to look for VMDKs on '%s'..."%(FSName,))
  if Opts.VHostType=="vmware":
    if len(Opts.VMDKlist)>0:
      for GivenVMDK in Opts.VMDKlist:
        try:
          SavedRaise=Opts.Raise
          Opts.Raise=False
          CxCommand="ls -1 '%s'/%s-flat.vmdk 2>/dev/null"%(FSName,GivenVMDK)
          OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
          Opts.Raise=SavedRaise
          if OutputText and len(OutputText)>0:
            for OutputLine in OutputText.splitlines():
              if OutputLine and len(OutputLine)>0:
                FullVMDKname=OutputLine.split()[0]
                Opts.SnapshotVMDK.append(FullVMDKname)
                Msg(Opts,"%s found"%(FullVMDKname,))
        except:
          ErrMsg(Opts,"problem listing VMDKs on filesystem '%s'"%(FSName,))
    else:
      Msg(Opts,"because the list of filtered VMDKs is empty, will search for everyone...")
      try:
        CxCommand="find '%s' -name '*-flat.vmdk'"%(FSName,)
        OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
        if OutputText and len(OutputText)>0:
          for OutputLine in OutputText.splitlines():
            if OutputLine and len(OutputLine)>0:
              FullVMDKname=OutputLine.split()[0]
              Opts.SnapshotVMDK.append(FullVMDKname)
              Msg(Opts,"%s found"%(FullVMDKname,))
      except:
        ErrMsg(Opts,"problem searching for all VMDKs on filesystem '%s'"%(FSName,))
  else:
    ErrMsg(Opts,"don't know how to search VMDKs for servers of type '%s'"%(Opts.VHostType,))
    Opts.ExitCode=47
    sys.exit(Opts.ExitCode)
  
def GetVMDKInFSOnVHost(Opts,Num):
  DebugFn(Opts)
  Msg(Opts,"trying to look for VMDK in %s/%s..."%(Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],))
  if Opts.VHostType=="vmware":
    CxCommand="""ls %s/%s | awk '$NF!~/flat.vmdk/{print $NF}' | tee %sVMDKNAME.txt""" % (Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.LUN[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
    OutputLines=OutputText.splitlines()
    if len(OutputLines)>0 and len(OutputLines[0])>0:
      if len(Opts.SnapshotVMDK)<(Num+1):
        Opts.SnapshotVMDK.append(OutputLines[0].split()[0])
      else:
        Opts.SnapshotVMDK[Num]=OutputLines[0].split()[0]
      Msg(Opts,"found virtual disk %s/%s/%s" % (Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.SnapshotVMDK[Num]))
    else:
      ErrMsg(Opts,"could not get VMDK name for %s!\n"%(Opts.CloneDisk[Num],))
      Opts.ExitCode=64
      sys.exit(Opts.ExitCode)
  else:
    ErrMsg(Opts,"don't know how to get the VMDK of the SAN snapshot on %s!"%(Opts.VHostName,))
    Opts.ExitCode=46
    sys.exit(Opts.ExitCode)
  return True

def AttachCloneVMDKsToTarget(Opts):
  """Sequentially attachs found VMDKs on snapshots to target VM"""
  DebugFn(Opts)
  Msg(Opts,"trying to attach virtual disks to target VM")
  if Opts.VHostType=="vmware":
    if len(Opts.SnapshotVMDK)>0:
      VirtualDiskIndex=Opts.ScsiOffset+1
      for FullVmdkName in Opts.SnapshotVMDK:
        try:
          CxCommand="vim-cmd vmsvc/device.diskaddexisting %s %s %s %s"%(Opts.VMid,FullVmdkName,Opts.Controller[1],VirtualDiskIndex)
          OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
          VirtualDiskIndex=VirtualDiskIndex+1
        except:
          ErrMsg(Opts,"problem attaching '%s' like disk [%s:%s] to VM %s"%(FullVmdkName,Opts.Controller[1],VirtualDiskIndex,Opts.VMid))
    else:
      ErrMsg(Opts,"no VMDKs found!")
  else:
    ErrMsg(Opts,"don't know how to attach virtual disks in hosts of type %s"%(Opts.VHostType,))

def AttachCloneDiskToTarget(Opts,Num):
  DebugFn(Opts)
  Msg(Opts,"trying to attach the cloned VMDK (%s/%s/%s) to target VM..."%(Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.SnapshotVMDK[Num],))
  if Opts.VHostType=="vmware":
    Msg(Opts,"trying to attach existing virtual disk %s" %(Num,))
    CxCommand="vim-cmd vmsvc/device.diskaddexisting %s %s/%s/%s %s %s" % (Opts.VMid,Opts.SnapshotFS[Num],Opts.SnapshotDS[Num],Opts.SnapshotVMDK[Num],Opts.Controller[1],Opts.CloneDisk[Num])
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    ErrMsg(Opts,"don't know how to attach 1st cloned disk from %s on %s!\n"%(Opts.Server3Name,Opts.VHostName))
    Opts.ExitCode=47
    sys.exit(Opts.ExitCode)
  return True
  
def StartTargetVM(Opts):
  DebugFn(Opts)
  Msg(Opts,"trying to start VM #%s"%(Opts.VMid,))
  if Opts.VHostType=="vmware":
    CxCommand="vim-cmd vmsvc/power.on %s" % (Opts.VMid)
    OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
  else:
    ErrMsg(Opts,"don't know how to start %s (%s) on %s!"%(Opts.Server3Name,Opts.Server3VMname,Opts.VHostName))
    Opts.ExitCode=49
    sys.exit(Opts.ExitCode)
  return True

def AddCleanedTime(Opts,TimeStr):
  DebugFn(Opts)
  Opts.ExecutionTimes.append(TimeStr)
  return
  
def CleanTimeString(Opts,TimeStr):
  DebugFn(Opts)
  ShortMatch=re.match('^([0-9](:?:)?[0-5][0-9])$',TimeStr)
  LongMatch=re.match('^((([01][0-9])|(2[0-3]))(:?:)?[0-5][0-9])$',TimeStr)
  try:
    CleanedTime="0"+ShortMatch.group(0).replace(":","")
  except AttributeError:
    try:
      CleanedTime=LongMatch.group(0).replace(":","")
    except AttributeError:
      CleanedTime=''
  return CleanedTime

def CheckCloneTimes(Opts):
  DebugFn(Opts)
  # Msg(Opts,"validating clone times given like arguments...")
  try:  
    for i in range(len(Opts.CloneTimes)):
      CleanedTime=CleanTimeString(Opts,Opts.CloneTimes[i])
      if (len(CleanedTime)>0) and (CleanedTime not in Opts.ExecutionTimes):
        AddCleanedTime(Opts,CleanedTime)
      else:
        ErrMsg(Opts,"could not interpret time \"%s\", skipping...\n"%(Opts.CloneTimes[i],))
    if len(Opts.ExecutionTimes)==0:
      ErrMsg(Opts,"No valid execution times given!")
      sys.exit(2)
    else:
      Msg(Opts,"execution times %s validated OK"%(Opts.ExecutionTimes,))
      return True
  except TypeError:
    ErrMsg(Opts,"no CloneTimes given! Exiting...")
    sys.exit(2)

def ValidateVolume(Opts,VolName):
  DebugFn(Opts)
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="lsvdisk -nohdr"
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      VolumeExists=False
      VolumeIsValid=False
      if OutputText and len(OutputText)>0:
        for OutputLine in OutputText.splitlines():
          if OutputLine.split()[1] and len(OutputLine.split()[1])>0 and OutputLine.split()[1]==VolName:
            VolumeExists=True
            break
        if not VolumeExists:
          ErrMsg(Opts,"given volume \"%s\" was not found!... removing from LUN list..."%(VolName,))
          Opts.LUN.remove(VolName)
      SaveVerbose=Opts.Verbose
      Opts.Verbose=False # Disable messages
      if VolumeExists and GetVolumeSize(Opts,VolName)>0:
        VolumeIsValid=True
      Opts.Verbose=SaveVerbose
      return VolumeIsValid
    except:
      ErrMsg(Opts,"could not validate volumes on %s... exiting"%(Opts.Storage1Name,))
      sys.exit(5)
  else:
    ErrMsg(Opts,"don't know how to check volumes on %s... exiting"%(Opts.Storage1Name,))
    sys.exit(4)

def ValidateGivenVolumes(Opts):
  """Counts how many volumes of given exists in SAN storage"""
  if len(Opts.LUN)>0:
    LunList=list(Opts.LUN)     # Use a copy of the LUN list because removing items breaks the loop
    for VolumeName in LunList:
      ValidateVolume(Opts,VolumeName)
    if len(Opts.LUN)==0:
      ErrMsg(Opts,"none of given volumes exist in SAN storage... exiting")
      sys.exit(3)
  else:
    ErrMsg(Opts,"no valid SAN volumes to process given... exiting")
    sys.exit(2)
      
def CreateNowNamedVolume(Opts,VolumeName):
  """Create a now named volume based on VolumeName, and return the name"""
  """ Note this is the same CreateNowNamedVolume than in CntrlSnaps.py """
  """Except it creates NAME_cDATE_TIME named volumes and non-0 CopyRate"""
  DebugFn(Opts)
  Msg(Opts,"trying to create new volume to clone %s..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      TimeSuffix=GetTimedSuffix(Opts)
      NowVolumeName="%s_c%s" % (VolumeName,TimeSuffix)
      NewSnapSize=GetVolumeSize(Opts,VolumeName)
      CxCommand="mkvdisk -mdiskgrp %s -iogrp %d -size %d -unit b -rsize %d%% -warning %d%% -autoexpand -easytier %s -name %s" % (Opts.Pool,Opts.IOgroup,NewSnapSize,Opts.PercentThin,Opts.SnapWarning,Opts.SnapEasy,NowVolumeName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0 and OutputText.endswith('created\n'):
        Msg(Opts,"volume %s created" % (NowVolumeName,))
      else:
        Msg(Opts,"could not create volume %s!" % (NowVolumeName,))
        return COULD_NOT_CREATE
    except:
      Msg(Opts,"could not create volume %s!" % (NowVolumeName,))
      return COULD_NOT_CREATE
    # Now get the VDISK_UID
    try:
      CxCommand="lsvdisk -nohdr -delim : -bytes %s" % NowVolumeName
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        for OneLine in OutputText.splitlines():
          if OneLine.startswith("vdisk_UID:"):
            NewVolumeVUID=OneLine.split(":")[1]
            Msg(Opts,"new volume %s VUID is %s" % (NowVolumeName,NewVolumeVUID))
            Opts.SnapshotVUID.append(NewVolumeVUID)
      return NowVolumeName
    except:
      Msg(Opts,"could not get volume %s VDISK_UID!" % (NowVolumeName,))
  else:
    return COULD_NOT_CREATE

def CloneVolumeToVolume(Opts,SourceVolume,TargetVolume):
  """Create snapshot clone mapping between source volume and target volume"""
  """Filter using VOLUME_c_DATE_TIME filter                               """
  DebugFn(Opts)
  Msg(Opts,"trying to clone %s to %s"%(SourceVolume,TargetVolume))
  if Opts.Storage1Type=="storwize":
    try:
      MatchOb = re.match( '%s_c_([0-9]{8}_[0-9]{6})'%(SourceVolume), TargetVolume)
      if MatchOb:
        TimeSuffix=MatchOb.group(1)
      else:
        TimeSuffix="__NOTSEQ__%d" % (random.randint(1000,10000),)
      CloneNow="%s%s%s" % (SourceVolume,"_clone_",TimeSuffix)
      CxCommand="mkfcmap -source %s -target %s -name %s -copyrate %d" % (SourceVolume,TargetVolume,CloneNow,Opts.SnapCopy)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      CxCommand="startfcmap -prep -restore %s" % (CloneNow,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Msg(Opts,"snapshot clone of volume %s created into %s (pair named %s)"%(SourceVolume,TargetVolume,CloneNow))
    except:
      ErrMsg(Opts,"snapshot clone of volume %s could not created into %s!"%(SourceVolume,TargetVolume))
  return
  
def RemoveVolume(Opts,VolumeName):
  """Remove named volume from storage"""
  DebugFn(Opts)
  Msg(Opts,"trying to force remove volume %s..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="rmvdisk -force %s"%(VolumeName,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Msg(Opts,"Volume %s removed."%(VolumeName,))
    except:
      ErrMsg(Opts,"volume %s could not be removed."%(VolumeName,))
  else:
    ErrMsg(Opts,"volume %s could not be removed.\n"%(VolumeName,))
  return

def WaitNextIteration(Opts):
  """Wait for next iteration"""
  # This function waits ONE HOUR if RunOClock==FALSE
  # This function waits for HOUR OCLOCK if RunOClock==TRUE
  DebugFn(Opts)
  StartingMinute=Opts.StartingSecond//60
  FullWait=Opts.FullWait//60
  Msg(Opts, "waiting for next iteration, now is %s seq minutes"%(StartingMinute,))
  while True:
    # Run forever until break
    Now=time.localtime(time.time())[3:5]
    ExitIfKillFile(Opts)
    if Opts.DEBUG:
      break                               # On debug, return quickly
    NowStr="%02d%02d"%(Now[0],Now[1])
    if NowStr in Opts.ExecutionTimes:
      break                               # It's time to execute
    WaitSeconds(Opts)                     # Sleep for a while
  sys.stdout.write("\n")
  sys.stdout.flush()
  return

def GetTimedSuffix(Opts):
  """Return a timed suffix like _20140208_183716 for 2014/feb/08 6:37:16PM"""
  DebugFn(Opts)
  TimeStr="_%04d%02d%02d_%02d%02d%02d" % (time.localtime(time.time())[0:6])
  return TimeStr

def IsESXfsPath(FSstring):
  return FSstring.startswith("/vmfs/volumes/")

def IsESXshortUUID(FSstring):
  try:
    ShortMatch=re.match("^([0-9a-f]{8}-[0-9a-f]{8})$",FSstring)
    ShortUUID=ShortMatch.group(0)
    return True
  except AttributeError:
    return False
    
def IsESXlongUUID(FSstring):
  try:
    LongMatch=re.match("^([0-9a-f]{8}-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{12})$",FSstring)
    LongUUID=LongMatch.group(0)
    return True
  except AttributeError:
    return False

def IsMounted(Opts,VHU,VHN,FSname):
  """Return true if ESX filesystem is mounted"""
  DebugFn(Opts)
  Msg(Opts,"checking if filesystem is mounted...")
  if IsESXfsPath(FSname):
    Msg(Opts,"%s is a VMware fs path, checking..."%(FSname,))
    CxCommand="esxcli storage filesystem list | awk -v F='%s' 'NR>2 && $1==F'"%(FSname,)
  elif IsESXshortUUID(FSname):
    Msg(Opts,"%s is a VMware short UUID, checking..."%(FSname,))
    CxCommand="esxcli storage filesystem list | awk -v U='%s' 'NR>2 && $(NF-5)==U'"%(FSname,)
  elif IsESXlongUUID(FSname):
    Msg(Opts,"%s is a VMware long UUID, checking..."%(FSname,))
    CxCommand="esxcli storage filesystem list | awk -v U='%s' 'NR>2 && $(NF-5)==U'"%(FSname,)
  else:
    Msg(Opts,"%s looks like a volume label, checking..."%(FSname,))
    CxCommand="esxcli storage filesystem list | awk -v L='%s' 'NR>2 && (substr($0,52,18))~L'"
  if Opts.VHostType=="vmware":
    try:
      OutputText=UNIXconnect(Opts,VHU,VHN,CxCommand)
      if len(OutputText.splitlines())>0:
        Msg(Opts,"%s was found mounted on %s"%(FSname,VHN))
        return True
      else:
        Msg(Opts,"%s was not found mounted on %s"%(FSname,VHN))
        return False
    except:
      Msg(Opts,"could not check if %s is mounted on %s!"%(FSname,VHN))
      return False
  else:
    ErrMsg(Opts,"don't know how to check mounted filesystems on %s!"%(VHN))
    return False

def UnmountSnapshotFS(Opts,SnapshotFSname):
  """Unmount a snapshot FS (really any) on VMware ESX host"""
  DebugFn(Opts)
  Msg(Opts,"trying to unmount snapshot filesystem %s..."%(SnapshotFSname,))
  if Opts.Storage1Type=="storwize":
    try:
      if IsMounted(Opts,Opts.VHost1User,Opts.VHost1Name,SnapshotFSname):
        Msg(Opts,"unmounting snapshot fs with path %s from %s" % (SnapshotFSname,Opts.VHost1Name,))
        CxCommand="esxcli storage filesystem unmount -p %s" % (SnapshotFSname,)
        OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
      if IsMounted(Opts,Opts.VHost2User,Opts.VHost2Name,SnapshotFSname):
        Msg(Opts,"unmounting snapshot fs with path %s from %s" % (SnapshotFSname,Opts.VHost2Name,))
        CxCommand="esxcli storage filesystem unmount -p %s" % (SnapshotFSname,)
        OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
    except:
      ErrMsg(Opts,"error unmounting fs with path %s from VMware hosts!\n"%(SnapshotFSname,))
      sys.exit(6)
  return True

def RemoveSANAttachment(Opts,SnapshotNAA):
  """Disable SAN access from a VMware host to a LUN"""
  DebugFn(Opts)
  Msg(Opts,"trying to deattach to SAN LUN %s..."%(SnapshotNAA,))
  if Opts.Storage1Type=="storwize":
    try:
      Msg(Opts,"detaching from LUN with NAA %s on %s" % (SnapshotNAA,Opts.VHost1Name,))
      CxCommand="esxcli storage core device set --state=off -d %s" % (SnapshotNAA,)
      OutputText=UNIXconnect(Opts,Opts.VHost1User,Opts.VHost1Name,CxCommand)
      Msg(Opts,"detaching from LUN with NAA %s on %s" % (SnapshotNAA,Opts.VHost2Name,))
      CxCommand="esxcli storage core device set --state=off -d %s" % (SnapshotNAA,)
      OutputText=UNIXconnect(Opts,Opts.VHost2User,Opts.VHost2Name,CxCommand)
    except:
      ErrMsg(Opts,"error detaching from SAN volume %s"%(SnapshotNAA,))
      # sys.exit(6)
  return True
  
def CreateKillFile(FileName):
  open(FileName, "w").close()
  sys.exit(0)

def ExitIfKillFile(Opts):
  """Terminates script if kill file is found"""
  DebugFn(Opts)
  if os.path.exists(Opts.KillFile):
    # Exit now
    try:
      os.unlink(Opts.KillFile)
      sys.stdout.write("%s: kill file found and removed, exiting...\n" % (Opts.PrgName,))
      FileLog(Opts,"kill file found and removed, exiting...")
    except IOError:
      sys.stdout.write("%s: error trying to remove killfile (%s)\n" % (Opts.PrgName,Opts.KillFile))
      FileLog(Opts,"error trying to remove killfile (%s)"%(Opts.KillFile,))
    sys.exit(5)
  return
  
def MapVolumeToVHosts(Opts,VolumeName):
  """Map VolumeName to both VMware ESX hosts, starting at SCSI 11"""
  DebugFn(Opts)
  Msg(Opts,"mapping volume %s to VMware ESX hosts..."%(VolumeName,))
  Options.ScsiOffset=Options.ScsiOffset+1
  if Opts.Storage1Type=="storwize":
    try:
      MiniWait(Opts)
      Msg(Opts,"mapping to SR-%s [SCSI ID %d]" % (Opts.VHost1Name,Opts.ScsiOffset))
      CxCommand="mkvdiskhostmap -scsi %d -host %s -force %s" % (Opts.ScsiOffset,"SR-"+Opts.VHost1Name,VolumeName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      MiniWait(Opts)
      Msg(Opts,"mapping to SR-%s [SCSI ID %d]" % (Opts.VHost2Name,Opts.ScsiOffset))
      CxCommand="mkvdiskhostmap -scsi %d -host %s -force %s" % (Opts.ScsiOffset,"SR-"+Opts.VHost2Name,VolumeName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
    except:
      ErrMsg(Opts,"error mapping %s to VMware hosts!\n"%(VolumeName,))
      sys.exit(6)
  return True
  
def GetNAAForVHostFilesystem(Opts,FSName):
  """Get the NAA (SAN ID) for a given FS"""
  DebugFn(Opts)
  if Opts.VHostType=="vmware":
    try:
      Msg(Opts,"getting NAA for filesystem \"%s\""%(FSName,))
      UUID=FSName.split("/")[3]
      CxCommand="esxcli storage vmfs extent list | awk -v UUID=%s '$2==UUID{print $4; exit}' | tee SNAPSHOTNAA.%s.txt" % (UUID,UUID)
      OutputText=UNIXconnect(Opts,Opts.VHostUser,Opts.VHostName,CxCommand)
      for OutputLine in OutputText.splitlines():
        if OutputLine and len(OutputLine)>0:
          NAA=OutputLine.split()[0]
          if len(NAA)==36:
            Msg(Opts,"found NAA %s for \"%s\""%(NAA,SnapshotFS,))
            Opts.SnapshotNAA.append(NAA)
            return NAA
          else:
            ErrMsg(Opts,"could not find NAA")
    except:
      ErrMsg(Opts,"error getting the NAA for filesystem \"%s\""%(FSName,))
      Opts.ExisCode=45
      sys.exit(Opts.ExitCode)
    return False
  else:
    ErrMsg(Opts,"don't know get the NAA of the volume of \"%s\", exiting.."%(FSName,))
    Opts.ExitCode=12
    sys.exit(Opts.ExitCode)
  return False

def ListAllAttachedSnapshots(Opts):
  """Get the list of all attached volume NAA ids"""
  DebugFn(Opts)
  if Opts.VHostType=="vmware":
    for ESXhost in [Opts.VHost1Name,Opts.VHost2Name]:
      try: #SR-HOST1
        Msg(Opts,"getting NAA list from %s"%("SR-%s"%(ESXhost,)))
        CxCommand="esxcli storage vmfs extent list | awk '$1~/snap-.*-/{print $4}' | tee SNAPSHOTNAA.txt"
        OutputText=UNIXconnect(Opts,Opts.VHost1User,ESXhost,CxCommand) # Assumes VHost1User==VHost2User
        for OutputLine in OutputText.splitlines():
          if OutputLine and len(OutputLine)>0:
            NAA=OutputLine.split()[0]
            if len(NAA)==36:
              Msg(Opts,"got %s on %s"%(NAA,"SR-%s"%(ESXhost,)))
              Opts.SnapshotNAA.append(NAA)
            else:
              ErrMsg(Opts,"could not find NAA")
      except:
        ErrMsg(Opts,"error gettting the NAA for filesystem \"%s\""%(FSName,))
        Opts.ExisCode=45
        sys.exit(Opts.ExitCode)
    Opts.SnapshotNAA=list(set(Opts.SnapshotNAA))
    return True
  else:
    ErrMsg(Opts,"don't know get the NAA of the volume of \"%s\", exiting.."%(FSName,))
    Opts.ExitCode=12
    sys.exit(Opts.ExitCode)
  return False

def RemoveClonesFromTarget(Opts):
  """Remove old clone virtual disks attached to target VM"""
  # Clean the target virtual machine
  SaveVerbose=Opts.Verbose
  Opts.Verbose=False #Disable messages
  for i in range(Options.ScsiOffset):                 # range(x) goes from 0 to x-1, change to number of disks
    RemoveCloneOnTarget(Options,Options.ScsiOffset+i) # de-attach VMDK from Windows VM
  Opts.Verbose=SaveVerbose
  return True

def FlatList(AnyList):
  """Convert a list of items, with some items composed of comma separated items in one flat list"""
  for ItemElement in AnyList:
    if ItemElement!=ItemElement.split(",")[0]: # It item was broken, then is a composed element
      ItemIndex=AnyList.index(ItemElement)
      AnyList.pop(ItemIndex)
      for i in range(len(ItemElement.split(","))):
        AnyList.insert(ItemIndex+i,ItemElement.split(",")[i].strip())
  return True

# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"
COULD_NOT_CREATE=-1

try:
  parser=OptionParser(usage="%prog [ --OPTIONS ] LUN ...")
  parser.add_option("-q", dest="Verbose", action="store_false", default=True, help="Quiet mode. Don't show messages")
  parser.add_option("-o", "--output", dest="LogFile", action="store", type="string", help="Log execution into file name", default="%s.log"%(PrgName,))
  parser.add_option("-O", "--no-log", dest="NoLog", action="store_true", help="No log to a file", default=False)
  parser.add_option("-d", "--workdir", dest="WorkDir", action="store", type="string", help="Working directory", default="M:\Automatizacion")
  parser.add_option("-r", "--ur", "--remote-unix-command", dest="RemoteUnixCommand", action="store", type="string", help="Remote execution command for Unix connections", default="plink")
  parser.add_option("-R", "--wr", "--remote-windows-command", dest="RemoteWindowsCommand", action="store", type="string", help="Remote execution command for Windows connections", default="psexec")
  parser.add_option("--s1n", "--server1name", dest="Server1Name", action="store", type="string", help="Server #1 hostname", default="SR-SQL1CO")
  parser.add_option("--s1u", "--server1user", dest="Server1User", action="store", type="string", help="Server #1 username to connect to", default="sqlservice")
  parser.add_option("--s1t", "--server1type", dest="Server1Type", action="store", type="string", help="Server #1 type of OS", default="windows")
  parser.add_option("--s2n", "--server2name", dest="Server2Name", action="store", type="string", help="Server #2 hostname", default="SR-SQL2CO")
  parser.add_option("--s2u", "--server2user", dest="Server2User", action="store", type="string", help="Server #2 username to connect to", default="sqlservice")
  parser.add_option("--s2t", "--server2type", dest="Server2Type", action="store", type="string", help="Server #2 type of OS", default="windows")
  parser.add_option("--s3n", "--server3name", dest="Server3Name", action="store", type="string", help="Server #3 hostname", default="SR-SQLREP01")
  parser.add_option("--s3u", "--server3user", dest="Server3User", action="store", type="string", help="Server #3 username to connect to", default="sqlservice")
  parser.add_option("--s3t", "--server3type", dest="Server3Type", action="store", type="string", help="Server #3 type of OS", default="windows")
  parser.add_option("--t1n", "--storage1name", dest="Storage1Name", action="store", type="string", help="Storage server #1 hostname", default="V3700")
  parser.add_option("--t1u", "--storage1user", dest="Storage1User", action="store", type="string", help="Storage server #1 username to connect to", default="soporte")
  parser.add_option("--t1t", "--storage1type", dest="Storage1Type", action="store", type="string", help="Storage server #1 type of OS", default="storwize")
  parser.add_option("--v1n", "--vhost1name", dest="VHost1Name", action="store", type="string", help="Virtualization host #1 hostname", default="ESX11CO")
  parser.add_option("--v1u", "--vhost1user", dest="VHost1User", action="store", type="string", help="Virtualization host #1 username to connect to", default="root")
  parser.add_option("--v1t", "--vhost1type", dest="VHost1Type", action="store", type="string", help="Virtualization host #1 type of OS", default="vmware")
  parser.add_option("--v2n", "--vhost2name", dest="VHost2Name", action="store", type="string", help="Virtualization host #2 hostname", default="ESX06CO")
  parser.add_option("--v2u", "--vhost2user", dest="VHost2User", action="store", type="string", help="Virtualization host #2 username to connect to", default="root")
  parser.add_option("--v2t", "--vhost2type", dest="VHost2Type", action="store", type="string", help="Virtualization host #2 type of OS", default="vmware")
  parser.add_option("-c", "--clones", dest="Clones", action="store", type="int", help="How many snapshots clones to maintain", default=2)
  parser.add_option("-p", "--percent-thin", dest="PercentThin", action="store", type="int", help="How thin make snapshots, percent integer", default=5)
  parser.add_option("-P", "--storage-pool", dest="Pool", action="store", type="string", help="Storage pool name", default="CLUSTER_VMWARE")
  parser.add_option("-W", "--full-wait", dest="FullWait",action="store", type="int", help="Time between snapshots (seconds)", default=60*60)
  parser.add_option("-w", "--shutdown-wait", dest="ShutdownWait", action="store", type="int", help=SUPPRESS_HELP, default=30)
  parser.add_option("-T", "--clone-time", dest="CloneTimes", action="append", type="string", help="Times to start cloning")
  parser.add_option("-S", "--scsi-offset", dest="ScsiOffset", action="store", type="int", help="Virtual disk SCSI offset",default=10)
  parser.add_option("-V", "--vmdk", dest="VMDKlist", action="append", type="string", help="VMDK file names to attach")
  parser.add_option("-K", "--kill", dest="Kill", action="store_true", default=False, help="Kill another instance of script")
  parser.add_option("--run-each",dest="RunOClock",action="store_true",default=False,help=SUPPRESS_HELP)
  parser.add_option("--run-minutes",dest="OClock",action="store",default=5,help="Run at HOUR:RUN-MINUTES")
  parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGUNIX", dest="DEBUGUNIX", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGWINDOWS", dest="DEBUGWINDOWS", action="store_true", default=False, help=SUPPRESS_HELP)
  (Options, Args)=parser.parse_args()
  Options.PrgName=PrgName
  Options.KillFile=KillFile
  Options.ExitCode=0

  # ----- DEFAULT VALUES -----
  # Options.CloneDisk=[0,11,12,13,14,15]
  # Options.Controller=[0,0]
  # Options.ExitCode=0
  Options.MiniWait=3
  Options.NoWaitOnDebug=True
  # Options.Raise=True
  Options.Server3VMname=Options.Server3Name[3:]
  Options.LUN=[]
  Options.Controller=[0,0]
  Options.CloneDisk=[]
  Options.SnapshotNAA=[]
  Options.SnapshotDS=[]
  Options.SnapshotFS=[]
  Options.SnapshotUUID=[]
  Options.SnapshotVUID=[]
  Options.SnapshotVMDK=[]
  Options.SnapshotLUN=[]
  Options.MappedVolume=[]
  Options.VMid=""
  Options.VMre='SQLREP.*1CO'
  Options.VMstate=""
  Options.ExecutionTimes=[]
  Options.VMFS=[]
  # Internal variables
  Options.NoWaitOnDebug=True
  Options.MiniWait=3
  Options.Raise=True
  Options.IOgroup=0
  Options.SnapWarning=95
  Options.SnapTier="generic_hdd"
  Options.SnapEasy="off"
  Options.SnapCopy=50
  Options.StartingSecond=int(time.time())
  Options.SCSIstartingOffset=Options.ScsiOffset
  # Minimum wait is ONE minute
  if Options.FullWait<60:
    Options.FullWait=60
  Msg(Options,"---------------------------------------------------------------------------------------")

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
  
  # Check clone times
  FlatList(Options.CloneTimes)
  FlatList(Options.VMDKlist)
  CheckCloneTimes(Options) # This end the program if there are no correct times given
  if len(Args)>0:
    Msg(Options,"%s volumes given"%(Args,))
    FlatList(Args)
    Options.LUN=list(Args) # Copy the list of arguments, don't reference it
    ValidateGivenVolumes(Options) # This can modify the list of arguments
    if len(Args)!=len(Options.LUN):
      ErrMsg(Options,"*****************************************************************")
      ErrMsg(Options,"Not all given volumes exist on SAN storage or not all were usable")
      ErrMsg(Options,"volumes given %s, volumes usable %s"%(Args,Options.LUN))
      ErrMsg(Options,"*****************************************************************")
      if len(Options.LUN)==0:
        sys.exit(6)
  
  Msg(Options,"%s START --------------------------------------------------------------------"%(PrgName,))
  while True:
    # Process arguments
    TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
    Msg(Options,"%s waking at %s" % (Options.PrgName,TimeStr))

    # First clone the volumes
    for OneVolume in Options.LUN:
      NewVolumeName=CreateNowNamedVolume(Options,OneVolume)
      CloneVolumeToVolume(Options,OneVolume,NewVolumeName)
      while CountNamedSnaps(Options,OneVolume)>Options.Clones:
        # Remove excess of snapshots
        try:
          FirstClone=GetNameOfFirstNamedSnap(Options,OneVolume)
          RemoveVolume(Options,FirstClone)
        except:
          continue # with while

    # Then de-attach the virtual disks and volumes
    GetVMID(Options,Options.Server3VMname)
    GetTargetVMState(Options)
    # if not PoweredOff, shutdown it or power off it
    if Options.VMstate != "PoweredOff":
      ShutdownTargetVM(Options)                        # if not poweredOff, try shutdown
      WaitSeconds(Options)                             # wait a little while
      GetTargetVMState(Options)     
      if Options.VMstate != "PoweredOff":
        PowerOffTargetVM(Options)                      # the POWER OFF

    # Clean target virtual machine
    RemoveClonesFromTarget(Options)
    # Get the list of mounted snapshot file systems
    ListMountedSnapshotFSOnVHost(Options)
    # Unmount and detach all clone volumes
    for SnapshotFS in Options.SnapshotFS:
      SnapshotNAA=GetNAAForVHostFilesystem(Options,SnapshotFS)
      UnmountSnapshotFS(Options,SnapshotFS)
      RemoveSANAttachment(Options,SnapshotNAA)
    # Remove all remaining SAN attachments
    ListAllAttachedSnapshots(Options)
    for SnapshotNAA in Options.SnapshotNAA:
      RemoveSANAttachment(Options,SnapshotNAA)
      
    UnmapAllCloneLun(Options)
    
    for OneVolume in Options.LUN:
      LastCloneSnapshot=GetNameOfLastNamedSnap(Options,OneVolume) # Get name of las clone of VolumeName
      Msg(Options,"found %s as last clone snapshot for %s"%(LastCloneSnapshot,OneVolume))
      MapVolumeToVHosts(Options,LastCloneSnapshot)
      OneVolumeIndex=(Options.LUN.index(OneVolume))
      RescanSANonVHosts(Options)
      MiniWait(Options) # BUG?
      RescanSANonVHosts(Options) # BUG?
      ListSnapshotOnVHost(Options,OneVolumeIndex)
      ResigSnapshotOnVHost(Options,OneVolumeIndex)
      MiniWait(Options) # BUG?
      MountSnapshotOnVHosts(Options,OneVolumeIndex)
      RescanSANonVHosts(Options) # BUG?
      ListSnapshotFSOnVHost(Options,OneVolumeIndex)
      GetDataStoresOnVHost(Options,Options.SnapshotFS[-1]) # Datastores on last snapshot filesystem
      GetVMDKsOnVHost(Options,Options.SnapshotFS[-1])      # All VMDKs on last snapshot filesystem
      
    AttachCloneVMDKsToTarget(Options)
    StartTargetVM(Options)
    WaitNextIteration(Options)      
  TimeStr="%4d/%2d/%2d %d:%02d:%02d" % (time.localtime(time.time())[0:6])
  ErrMsg(Options,"%s ending at %s ------------------------------------------------------------------------"%(Options.PrgName,TimeStr))

except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Options.PrgName,))
  sys.stderr.flush()
except IOError:
  sys.stderr.write("\n%s: IO Error changing directory to %s!\n" % (Options.PrgName,Options.WorkDir))
  sys.stderr.flush()
except SyntaxError:
  sys.stderr.write("\n%s: Syntax error compiling/running!\n" % (Options.PrgName,))
  sys.stderr.flush()
except SystemExit as e:
  sys.stderr.write("%s: EXIT.\n" % (PrgName,))
  sys.exit(e)

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
