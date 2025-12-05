#!/usr/bin/env python3
# encoding: utf-8
"""
Same.py: identifies and lists repeated files. Identifies repeated files using digital crypto-hashes

Created by Ramón Barrios Lascar on 2006-12-15.
Changed 2010-03-29: Changed line 79 "import md5" to "import hashlib"
Changed 2010-03-29: Changed line 32 "import hash=md5.new()" to "hash = hashlib.new('md5')"
Changed 2010-07-23: Enhanced to use and/or store hashes in extended attributes
Changed 2012-09-29: Adjust output in DEBUG mode
Changed 2016-04-05: Add plain file case and len(MasterList) -> Options.Count
Changed 2016-04-16: Change to use /usr/bin/env
Changed 2016-04-16: Add an exclusion list for filenames
Changed 2019-04-18: Add support for Visual Studio Code
Changed 2021-04-01: Changed to run on Python 3.9
Changed 2022-02-02: Changed to store date of hash
Changed 2022-05-24: Changed to store date of hash only optionally
Changed 2023-02-05: Changed to use file timestamps optionally
Changed 2023-04-01: Progress indicators on stderr
Changed 2024-03-09: Changed format strings
Changed 2025-09-05: Changed xattr name prefix to be option `xattr-prefix` wit default
Changed 2025-10-15: Defaults to skips empty files, with an option to process them
Copyright (c) 2007-2025 Ínodo S.A.S. All rights reserved.
"""
import sys, os, string, xattr
from optparse import OptionParser, SUPPRESS_HELP
from datetime import datetime

def ShowAlgorithms( Opts ):
  import hashlib
  sys.stdout.write(f"{Opts.PrgName}: Algoriths available:\n")
  for Alg in hashlib.algorithms_available:
    sys.stdout.write(f"{Opts.PrgName}: {Alg.upper()}\n")

def AddToHashList( HashList, FileName, FileHash ):
  # if HashList.has_key( FileHash ):
  # Python3:
  if FileHash in HashList:
    # If the hash is in the hash list add the filename to the list of files with this hash
    HashList[ FileHash ].append(FileName)
  else:
    # If NOT, the hash is NOT in the list add a new keyed element to the hash list
    HashList[ FileHash ] = [ FileName ]
  return HashList

def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  try:
    hash = hashlib.new(Opts.Crypto)
  except ValueError:
    sys.stderr.write(f"{Opts.PrgName}: unsupported hash crypto algorithm \"{Opts.Crypto}\"!\n {Opts.PrgName}: EXITTING...!\n")
    sys.stderr.flush()
    sys.exit(255)
  BlockSize=65536
  with open(FileName,"rb") as AFile:
    Buf=AFile.read(BlockSize)
    while len(Buf)>0:
      hash.update(Buf)
      Buf=AFile.read(BlockSize)
  AFile.close()
  return hash.hexdigest().encode('utf-8')

def ProcessOneFile( Hashes, Opts, FileName ):
  # Calculates secure sum of a file
  
  if os.path.basename(FileName) in Opts.Exclusions:
    if Opts.Debug:
      sys.stderr.write(f"  DEBUG: {Opts.PrgName}: excluded file '{FileName}' found\n")
    return Hashes, Opts
  if os.path.getsize(FileName):
    # Process only sizeable files
    # if Opts.Debug:
    #   sys.stderr.write( "  %s\t" % (FileName,) )
    if not Opts.ForceCreateAttr or Opts.UseAttr:
      if Opts.UseStatTime or Opts.DateAttr:
        FileMTime = datetime.fromtimestamp(os.path.getmtime(FileName))
      FileHashRead = False
      # If working with extended attributes then read attribute
      try:
        FileHash = xattr.getxattr(FileName, f"{Opts.XattrPrefix}.{Opts.Crypto}" ).decode('utf-8','replace')
        if not Opts.ForceCreateAttr:
          FileHashRead = True
        if Opts.DateAttr:
          FileHashTime = xattr.getxattr(FileName, f"{Opts.XattrPrefix}.{Opts.Crypto}.time").decode('utf-8','replace')
          if FileHashTime>FileMTime:
            FileHashRead = False
      except:
        FileHash = CalcHashForFile(Opts, FileName)
        if Opts.DateAttr:        
          FileHashTime = bytes(datetime.now().strftime("%Y%m%d%H%M%S"),"ascii")
    else:
      FileHash = CalcHashForFile(Opts, FileName)
      if Opts.DateAttr:
        FileHashTime = datetime.now().strftime("%Y%m%d%H%M%S")
    if Opts.Debug:
      if Opts.DateAttr:
        sys.stderr.write(f"  {FileHash} ({FileHashTime}) {FileName}")
      else:
        sys.stderr.write(f"  {FileHash} {FileName}") # Remove a carriage return
    if ( Opts.StoreAttr and not FileHashRead ) or Opts.ForceCreateAttr or Opts.UseStatTime or Opts.DateAttr:
      try:
        xattr.setxattr(FileName, f"{Opts.XattrPrefix}.{Opts.Crypto}", FileHash)
      except:
        if Opts.Verbose or Opts.Debug:
          sys.stdout.write(f"\n{Opts.PrgName}: Could not write hash xattr for {FileName}!\n")
          sys.stdout.flush()
      if Opts.DateAttr:
        try:
          xattr.setxattr(FileName, f"{Opts.XattrPrefix}.{Opts.Crypto}.time", FileHashTime)
        except IOError as ioe:
          if Opts.Verbose or Opts.Debug:
            sys.stdout.write(f"\n{Opts.PrgName}: Could not write hash time xattr for {FileName}!\n")
            sys.stdout.flush()        
    Hashes = AddToHashList(Hashes, FileName, FileHash)
    Opts.Count+=1
    if Opts.Verbose:
      if Opts.ForceCreateAttr:
        if Opts.ToStdErr:
          sys.stderr.write("+")
        else:
          sys.stdout.write("+")
      elif Opts.UseAttr:
        if Opts.ToStdErr:
          sys.stderr.write("=")
        else:
          sys.stdout.write("=")
      else:
        if Opts.ToStdErr:
          sys.stderr.write("-")
        else:
          sys.stdout.write("-")
      if (Opts.Count % Opts.LineWidth) == 0:
        if Opts.ToStdErr:
          sys.stderr.write(( Opts.Format % Opts.Count )+"\n")
        else:
          sys.stdout.write(( Opts.Format % Opts.Count )+"\n")
      else:
        if (Opts.Count % 10) == 0:
          if Opts.ToStdErr:
            sys.stderr.write(" ")
            sys.stderr.flush()
          else:
            sys.stdout.write(" ")
            sys.stdout.flush()
  else:
    if Opts.Verbose:
      sys.stdout.write("\a\b^")
  if Opts.Debug:
    sys.stderr.write("\n")
    sys.stderr.flush()
  return Hashes, Opts
  
def mycmp( a, b ):
  if a>b:
    r=1
  elif a<b:
    r=-1
  else:
    r=0
  return r

def ExecuteForFile( Opts, OneFile ):
  # Execute script command with one file only
  # OneFile = 'f"{OneFile}"'
  if Opts.Debug:
    sys.stderr.write(f"{Opts.ExecuteCommand=}")
  os.system(Opts.ExecuteCommand.replace(Opts.Replacement, OneFile))

# START OF MAIN FILE
try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] DIR ... FILE ... ")
  parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
  parser.add_option( "-r", "--recursive", dest="Recursive", action="store_true", help="Recurse directories", default=False)
  parser.add_option( "-D", "--duplicates", dest="OnlyDups", action="store_true", help="Show only duplicates", default=False)
  parser.add_option( "-m", "-M", "--mode", dest="Crypto", action="store", type="string", help="Digest algoritm type (defaults to MD5)", default="md5", metavar="MODE" )
  parser.add_option( "--algorithms", "--available", dest="ShowOnlyAlgs", action="store_true", help="Show only algorithm help")
  parser.add_option( "-p", "--parsable", dest="Parsable", action="store_true", help="Parsable listing format", default=False)
  parser.add_option( "-s", "--separated", dest="Separated", action="store_true", help="Separated repeated items", default=False)
  parser.add_option( "-n", "--noshow", dest="ShowHash", action="store_false", help="Don't show the hashes", default=True)
  parser.add_option( "-N", "--nodot", dest="NoDot", action="store_true", help="Don't show initial ./", default=False)
  parser.add_option( "-0", "--null", dest="NullTerminated", action="store_true", help="Null terminated file names", default=False)
  parser.add_option( "-e", "--execute", dest="ExecuteCommand", action="store", type="string", help="Execute command with each duplicated file")
  parser.add_option( "-k", "--ok", dest="ConditionalCommand", action="store", type="string", help="Execute command with each duplicated file, asking first")
  parser.add_option( "-I", "--replace-string", dest="Replacement", action="store", type="string", help="Replacement meta string (defaults to {})", default="{}")
  parser.add_option( "-x", "--xattr", dest="UseAttr", action="store_true", help="Use extended attributes", default=False)
  parser.add_option( "-X", "--store-xattr", dest="StoreAttr", action="store_true", help="Store extended attributes if not found", default=False)
  parser.add_option( "-y", "-Y", "--always-recreate-xattr", dest="ForceCreateAttr", action="store_true", help="Always recreate extended attributes", default=False)
  parser.add_option( "-l", "--skip-symlinks", dest="SkipSymLinks", action="store_true", help="Skip symbolic links", default=False)
  parser.add_option( "-t", "--show-time", dest="ShowTime", action="store_true", help="Show time used", default=False)
  parser.add_option( "-T", "--use-timestamps", dest="UseStatTime", action="store_true", help="Use file timestamps", default=False)
  parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME" )
  parser.add_option( "-d", "--date-attr", dest="DateAttr", action="store_true", help="Store date of hash", default=False)
  parser.add_option( "--DEBUG", dest="Debug", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option( "--BASEFORMAT", "-B", dest="BaseFormat", action="store", default=" [%%%dd]", help=SUPPRESS_HELP)
  parser.add_option( "--digits", "-#", dest="Digits", action="store", type="int", default=4, help=SUPPRESS_HELP)
  parser.add_option( "--width", "-w", dest="LineWidth", action="store", type="int", default=100, help=SUPPRESS_HELP)
  parser.add_option( "--xattr-prefix=", dest="XattrPrefix", action="store", default="user.same-hash", help=SUPPRESS_HELP)
  parser.add_option( "--vscode", dest="VSCode", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option( "--stderr-progress", dest="ToStdErr", action="store_true", default=False, help="Progress indicators on stderr")

  (Options, Args) = parser.parse_args()
  
  if Options.VSCode:
    Options.Debug = True
    Options.Recursive = True
    if len(Args)==0:
      Args = ["/Users/e/Downloads/Software/Other"]
    
  if Options.ShowOnlyAlgs:
    ShowAlgorithms(Options)
    exit(0)
    
  if Options.ForceCreateAttr:
    Options.StoreAttr = True
  if Options.StoreAttr:
    Options.UseAttr = True
  if not Options.UseStatTime:
    Options.DateAttr = False
  # Options.Crypto = string.lower( Options.Crypto )
  # Python3:
  Options.Crypto=Options.Crypto.lower()
  # Initialize file count
  Options.Count = 0
  # Options.PrgName = "same"
  if Options.Parsable:
    Options.ShowHash = False
  Options.Format=Options.BaseFormat % Options.Digits
  if Options.ShowTime:
    import time
    Options.StartTime = time.time()
    Options.EndTime = time.time ()

  # print "Options = %s" % ( Options )
  # print "Args    = %s" % ( Args )
  if Options.Debug:
    Options.ColonSep=""
  else:
    Options.ColonSep=":"  

  MasterHashes = {}
  ExclusionsList = ['.DS_Store', 'Icon\r']
  Options.Exclusions = ExclusionsList

  if len(Args) > 0 :
    import hashlib
    if Options.Verbose:
      # sys.stderr.write( "%s: using %s algoritm\n" % ( Options.PrgName, string.upper( Options.Crypto ) ) )
      # Python3:
      sys.stderr.write(f"{Options.PrgName}: using {Options.Crypto.upper()} algoritm\n")
      if Options.ForceCreateAttr:
        sys.stderr.write(f"{Options.PrgName}: creating and unconditionally recreating extented attributes ({Options.XattrPrefix}.{Options.Crypto})\n")
      elif Options.StoreAttr:
        sys.stderr.write(f"{Options.PrgName}: creating and saving extented attributes ({Options.PrgName}-{Options.Crypto})\n")
      elif Options.UseAttr:
          sys.stderr.write(f"{Options.PrgName}: creating extented attributes ({Options.PrgName}-{Options.Crypto}) without saving\n")
      if Options.DateAttr:
        sys.stderr.write(f"{Options.PrgName}: creating and saving extended date attributes ({Options.PrgName}-{Options.Crypto}.date)\n")
    if Options.Debug:
      sys.stderr.write("  DEBUG: ")
    if Options.ShowTime:
      StartTime = time.localtime(Options.StartTime)
      sys.stderr.write(f"{Options.PrgName}{Options.ColonSep} started at {StartTime[0]:04d}/{StartTime[1]:02d}/{StartTime[2]:02d} {StartTime[3]:02d}:{StartTime[4]:02d}:{StartTime[5]:02d}\n")
    for OneArg in Args:
      if Options.SkipSymLinks:
        if Options.Debug:
          sys.stderr.write("  DEGUG: same skipping symbolic links\n" )
        if (not os.path.islink(OneArg) and os.path.isfile(OneArg)):  # removed or ()
          try:
            if Options.Debug:
              sys.stderr.write(f"{Options.PrgName}: {Options.Count=}\n")
            MasterHashes, Options = ProcessOneFile( MasterHashes, Options, OneArg )
            if Options.Debug:
              sys.stderr.write(f"{Options.PrgName}: {Options.Count=}\n")
          except (IOError, OSError):
            pass
        else:
          if os.path.isfile(OneArg):
            try:
              if Options.Debug:
                sys.stderr.write(f"  DEBUG: {Options.Count=}\n")
              MasterHashes, Options = ProcessOneFile( MasterHashes, Options, OneArg )
              if Options.Debug:
                sys.stderr.write(f"  DEBUG: {Options.Count=}\n")
            except (IOError, OSError):
              pass
      if os.path.isdir(OneArg) and Options.Recursive:
        if not os.path.islink(OneArg):
          for StartDir, Dirs, Files in os.walk(OneArg):
            for OneFile in Files:
              if Options.SkipSymLinks and not os.path.islink(os.path.join(StartDir, OneFile)):
                try:
                  MasterHashes, Options = ProcessOneFile(MasterHashes, Options, os.path.join(StartDir, OneFile))
                except (IOError, OSError):
                  pass
              else:
                if not Options.SkipSymLinks:
                  try:
                    MasterHashes, Options = ProcessOneFile(MasterHashes, Options, os.path.join(StartDir, OneFile))
                  except (IOError, OSError):
                    pass
      if not os.path.isdir(OneArg) and not os.path.islink(OneArg):
        try:
          if Options.Debug:
            sys.stderr.write(f"  DEBUG: {Options.Count=}, OneArg='{OneArg}'\n")
          MasterHashes, Options = ProcessOneFile(MasterHashes, Options, OneArg)
          if Options.Debug:
            sys.stderr.write(f"  DEBUG: {Options.Count=}, OneArg='{OneArg}'\n")
        except (IOError, OSError) as e:
          # pass
          sys.stderr.write(f"SAME: exception raised ({e})!\n")
    if Options.Verbose:
      if Options.ToStdErr:
        sys.stderr.write("\n")
        sys.stderr.flush()
      else:
        sys.stdout.write("\n")
        sys.stdout.flush()
    Options.Count = len(MasterHashes)
    # if Options.Debug:
    #   sys.stderr.write( "  DEBUG: len(MasterHashes)=%d\n" % (len(MasterHashes),))
  
    # Print hash list
    # for OneHash, OneList in MasterHashes.iteritems():
    # Python3
    for OneHash, OneList in MasterHashes.items():
      # Only print hashes with repeated files
      if len(OneList) > 1:
        OneList.sort(key=len)
        # OneList-sorted(OneList, key=lambda x: len(x))
        if Options.ShowHash:
          print(f"{OneHash}: ")
        for i, OneItem in enumerate(OneList):
          if Options.NoDot:
            if OneItem[:2] == "./":
              OneItem = OneItem[2:]
          if ((i==0) and (not Options.OnlyDups)) or (i != 0):
            if Options.NullTerminated:
              if Options.Parsable:
                sys.stdout.write(f"{OneHash}:{OneItem}\0")
              else:
                sys.stdout.write(f"{OneItem}\0")
            else:
              if Options.Parsable:
                print(f"{OneHash}:{OneItem}")
              else:
                print(f"{OneItem} ")
        if Options.Separated:
          print
        # Execute part
        if Options.ExecuteCommand:
          ExecuteForFile(Options, OneItem)
    if Options.Debug:
      sys.stderr.write(" DEBUG: ")
    if Options.ShowTime:
      Options.EndTime = time.time()
      EndTime = time.localtime(Options.EndTime)
      sys.stderr.write(f"{Options.PrgName}{Options.ColonSep} ended at {EndTime[0]:04d}/{EndTime[1]:02d}/{EndTime[2]:02d} {EndTime[3]:02d}:{EndTime[4]:02d}:{EndTime[5]:02d}\n")
      if Options.Debug:
        sys.stderr.write(" DEBUG: ")
      sys.stderr.write(f"{Options.PrgName}{Options.ColonSep} processed {Options.Count} files, in {Options.EndTime-Options.StartTime}s (%fs/file)\n" % (0 if Options.Count==0 else (Options.EndTime-Options.StartTime)/Options.Count))
  else:
    parser.error("one or more arguments are needed!")
    sys.exit(2)
except KeyboardInterrupt:
  sys.stderr.write(f"\n{Options.PrgName}: Process cancelled!\n")
  sys.stderr.flush()