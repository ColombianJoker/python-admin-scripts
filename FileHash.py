#!/usr/bin/python
# encoding: utf-8
"""
FileHash.py: Manage digital hashes of contents of files for identification purposes

Created by Ramón Barrios Lascar on 2010-07-24.
Copyright (c) 2010 iKnow. All rights reserved.
"""

import sys, os, string, xattr
from optparse import OptionParser, SUPPRESS_HELP

def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  if Opts.DEBUG:
    sys.stderr.write( "%s DEBUG: %s\n" % (Opts.PrgName, sys._getframe().f_code.co_name) )
  hash = hashlib.new( Opts.Crypto )
  OpenFile = open( FileName )
  for OneLine in OpenFile:
    hash.update( OneLine )
  OpenFile.close()
  return hash.hexdigest()

def GetHashForFile( Opts, FileName ):
  # Retrieve stored hash from file
  if Opts.DEBUG:
    sys.stderr.write( "%s DEBUG: %s\n" % (Opts.PrgName, sys._getframe().f_code.co_name) )
  return xattr.getxattr( FileName, Opts.HashName )
  
def DeleteHash( Opts, FileName ):
  # Delete stored hash in file
  if Opts.DEBUG:
    sys.stderr.write( "%s DEBUG: %s\n" % (Opts.PrgName, sys._getframe().f_code.co_name) )
  try:
    xattr.removexattr( FileName, Opts.HashName )
  except:
    if Opts.Verbose:
      sys.stdout.write( "%s: %s has no %s attribute\n" % (Opts.PrgName, FileName, Opts.HashName))
      sys.stdout.flush()

def ListHash( Opts, FileName):
  # List stored hash in file
  if Opts.DEBUG:
    sys.stderr.write( "%s DEBUG: %s\n" % (Opts.PrgName, sys._getframe().f_code.co_name) )
  try:
    StoredFileHash = GetHashForFile( Opts, FileName )
    sys.stdout.write( "%s\t%s\n" % (StoredFileHash, FileName) )
  except KeyError:
    if Opts.Verbose:
      sys.stdout.write( "\t%s\n" % (FileName,) )
  
def ProcessOneFile( Opts, FileName ):
  # Process one file in all modes
  if os.path.basename( FileName )  == ".DS_Store" :
    if Opts.DEBUG:
      sys.stderr.write( "%s DEBUG %s found .DS_Store file\n" % (Opts.PrgName, sys._getframe().f_code.co_name))
    return
  Opts.Count = Opts.Count + 1
  if Opts.DEBUG:
    sys.stderr.write( "%s DEBUG: %s\n" % (Opts.PrgName, sys._getframe().f_code.co_name) )
    sys.stderr.write( "%s DEBUG: %4d %s\n" % (Opts.PrgName, Opts.Count, FileName) )
  if os.path.getsize( FileName ):
    # Process only sizeable files
    
    if Opts.DeleteAttr:
      # Must delete hash attribute
      DeleteHash( Opts, FileName )
    elif Opts.VerifyAttr:
      # Must get and compare hash
      FileHash = CalcHashForFile( Opts, FileName )
      try:
        StoredFileHash = GetHashForFile( Opts, FileName )
      except KeyError:
        StoredFileHash = "#ERROR#"
      if StoredFileHash == "#ERROR#":
        if Opts.Verbose:
          sys.stdout.write( "%s: file \"%s\" has no stored %s attribute. Could not compare.\n" % (Opts.PrgName, FileName, Opts.HashName) )
          sys.stdout.flush()
        else:
          sys.stdout.write( "x" )
      else:
        if FileHash == StoredFileHash:
          # They're the same
          if Opts.Verbose:
            sys.stdout.write( "  %s\tOK\n" % (FileName) )
            sys.stdout.flush()
          else:
            sys.stdout.write( "+" )
        else:
          # They are NOT the same
          if Opts.Verbose:
            sys.stdout.write( "  %s\tDIFFERENT\n" % (FileName) )
            sys.stdout.flush()
          else:
            sys.stdout.write( "-" )
    elif Opts.ListAttr:
      ListHash( Opts, FileName )
    elif Opts.ForceCreateAttr:
      # Must recreate hash
      FileHash = CalcHashForFile( Opts, FileName )
      try:
        xattr.setxattr( FileName, Opts.HashName, FileHash )
      except:
        if Opts.Verbose:
          sys.stdout.write( "\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName) )
          sys.stdout.flush()
        else:
          sys.stdout.write( "x" )
    elif Opts.StoreAttr:
      # Recreate hash if needed
      try:
        StoredFileHash = GetHashForFile( Opts, FileName )
      except KeyError:
        FileHash = CalcHashForFile( Opts, FileName )
        try:
          xattr.setxattr( FileName, Opts.HashName, FileHash )
        except:
          if Opts.Verbose:
            sys.stdout.write( "\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName) )
            sys.stdout.flush()
          else:
            sys.stdout.write( "x" )
    else:
      # List hash
      try:
        FileHash = GetHashForFile( Opts, FileName )
      except KeyError:
        FileHash = CalcHashForFile( Opts, FileName )
      sys.stdout.write( "%s\t%s\n" % (FileName, FileHash) )
      sys.stdout.flush()
  else:
    if Opts.Verbose:
      sys.stdout.write( "^" )
  if ( Opts.Count % 10 ) == 0 :
    sys.stdout.write( " " )
    sys.stdout.flush()
  if ( Opts.Count % 100 ) == 0 :
    sys.stdout.write( " %5s\n" % (Opts.Count,) )
    sys.stdout.flush()
    
parser = OptionParser(usage="%prog [ --OPTIONS ] DIR ... FILE ... ")
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-r", "--recursive", dest="Recursive", action="store_true", help="Recurse directories", default=False)
parser.add_option( "-X", "--store-xattr", dest="StoreAttr", action="store_true", help="Store extended attributes if not found", default=False)
parser.add_option( "-y", "--always-recreate-xattr", dest="ForceCreateAttr", action="store_true", help="Always recreate extended attributes", default=False)
parser.add_option( "-d", "--delete-attr", dest="DeleteAttr", action="store_true", help="Delete stored extended attribute if found", default=False)
parser.add_option( "-c", "--check", dest="VerifyAttr", action="store_true", help="Check file against stored extended attribute", default=False)
parser.add_option( "-L", "--list", dest="ListAttr", action="store_true", help="List stored extended attribute", default=False)
parser.add_option( "-m", "--mode", dest="Crypto", action="store", type="string", help="Digest algoritm type (SHA1, SHA224, SHA256, SHA384, SHA512, MD2, MD4, MD5, MDC2, RMD160, defaults to MD5)", default="md5", metavar="MODE" )
parser.add_option( "-l", "--skip-symlinks", dest="SkipSymLinks", action="store_true", help="Skip symbolic links", default=False)
parser.add_option( "-t", "--show-time", dest="ShowTime", action="store_true", help="Show time used", default=False)
parser.add_option( "-p", "--parsable", dest="Parsable", action="store_true", help="Parsable listing format", default=False)
parser.add_option( "-n", "--noshow", dest="ShowHash", action="store_false", help="Don't show the hashes", default=True)
parser.add_option( "-N", "--nodot", dest="NoDot", action="store_true", help="Don't show initial ./", default=False)
parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME" )
parser.add_option( "--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)

(Options, Args) = parser.parse_args()

if Options.ForceCreateAttr:
  Options.StoreAttr = True
  Options.DeleteAttr = False

if Options.DeleteAttr:
  Options.StoreAttr = False
  Options.ForceCreateAttr = False
  
if Options.ListAttr:
  Options.StoreAttr = False
  Options.ForceCreateAttr = False
  
if Options.DEBUG:
  Options.Verbose = False

if Options.ShowTime or Options.DEBUG:
  import time
  Options.StartTime = time.time()
  Options.EndTime = time.time ()
  
Options.Count = 0
  
Options.HashName = Options.PrgName + "-hash." + Options.Crypto

if len( Args ) > 0 :
  import hashlib
  if Options.Verbose:
    print( "%s using %s algoritm" % ( Options.PrgName, string.upper( Options.Crypto ) ) )
    if Options.ForceCreateAttr:
      print( "%s creating and unconditionally recreating extented attributes (%s)" % (Options.PrgName, Options.HashName) )
    elif Options.StoreAttr:
      print( "%s creating and saving extented attributes (%s)" % (Options.PrgName, Options.HashName) )
    elif Options.DeleteAttr:
        print( "%s deleting extented attributes (%s)" % ( Options.PrgName, Options.HashName) )
  for OneArg in Args:
    if Options.SkipSymLinks:
      if Options.DEBUG:
        sys.stderr.write( "%s DEBUG: SkipSymLinks\n" % (Options.PrgName,) )
      if ( not os.path.islink(OneArg) ) and os.path.isfile(OneArg):
        try:
          ProcessOneFile( Options, OneArg )
        except (IOError, OSError):
          pass
      else:
        if os.path.isfile( OneArg ):
          try:
            ProcessOneFile( Options, OneArg )
          except (IOError, OSError):
            pass
    if os.path.isdir( OneArg ) and Options.Recursive:
      if (not Options.SkipSymLinks) or (not os.path.islink(OneArg)):
        for StartDir, Dirs, Files in os.walk( OneArg ):
          for OneFile in Files:
            try:
              ProcessOneFile( Options, os.path.join( StartDir, OneFile ) )
            except (IOError, OSError):
              pass
    if os.path.isfile(os.path.expanduser(OneArg)):
      try:
        ProcessOneFile(Options, os.path.expanduser(OneArg))
      except ( IOError, OSError ):
        pass
  if Options.ShowTime or Options.DEBUG:
    Options.EndTime = time.time()
    EndTime = time.localtime(Options.EndTime)
    sys.stderr.write( "%s: ended at %04d/%02d/%02d %02d:%02d:%02d\n" % (Options.PrgName, EndTime[0], EndTime[1], EndTime[2], EndTime[3], EndTime[4], EndTime[5]))
    if Options.DEBUG:
      sys.stderr.write( " DEBUG: ")
    sys.stderr.write( "%s: processed %d files, in %fs (%fs/file)\n" % (Options.PrgName, Options.Count, Options.EndTime-Options.StartTime, (Options.EndTime-Options.StartTime)/Options.Count))

  if Options.Verbose:
    print
else:
  parser.error("one or more arguments are needed!")
