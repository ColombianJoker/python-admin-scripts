#!/usr/bin/python
# encoding: utf-8
"""
Mangler.py: Mangles filenames

Created by Ramón Barrios Lascar on 2010-08-23.
Copyright (c) 2010 iKnow. All rights reserved.
"""

import sys, os, string, xattr, hashlib, shutil, traceback
from optparse import OptionParser, SUPPRESS_HELP

def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  hash = hashlib.new( Opts.Crypto )
  hash.update( FileName )
  return hash.hexdigest()

def GetHashForFile( Opts, FileName ):
  return xattr.getxattr( FileName, Opts.AttrName )

def SetHashForFile( Opts, FileName, AttrValue ):
  xattr.setxattr( FileName, Opts.AttrName, AttrValue )
  
def DeleteHash( Opts, FileName ):
  try:
    xattr.removexattr( FileName, Opts.AttrName )
  except:
    if Opts.Verbose:
      sys.stderr.write( "%s: %s has no %s attribute\n" % (Opts.PrgName, FileName, Opts.HashName) )
      sys.stderr.flush()
      
def UnmangleOneFile( Opts, FileName ):
  (FileDir, FileBase) = os.path.split(FileName)
  (FileBase, FileExt) = os.path.splitext(FileBase)
  try:
    # Try to get stored attributes
    StoredAttr = GetHashForFile( Opts, FileName )
    DestName = os.path.join( FileDir, StoredAttr )
    if Opts.Debug:
      print( "DEBUG: StoredAttr=%s DestName=%s" % (StoredAttr, DestName) )
    try:
      shutil.move( FileName, DestName )
    except shutil.Error:
      sys.stderr.write( "%s: could not rename \"%s\"\n" % (Opts.PrgName, FileName) )
    if Opts.Verbose:
      sys.stderr.write("%s: %s -> %s\n" % (Opts.PrgName, FileName, os.path.split(DestName)[1]))
    else:
      sys.stderr.write( "." )
  except Exception as error:
    # if Opts.Verbose:
    #   sys.stderr.write( "%s: file \"%s\" doesn't look to have an stored xattr!\n" % (Opts.PrgName, FileName) )
    # else:
    #   sys.stderr.write( "x" )
    traceback.print_exc()
      
def MangleOneFile( Opts, FileName ):
  ( FileDir, FileBase ) = os.path.split( FileName )
  if Opts.Debug:
    print( "DEBUG: FileDir=%s FileBase=%s" % (FileDir, FileBase))
  ( FileBase, FileExt ) = os.path.splitext( FileBase )
  if Opts.Debug:
    print( "DEBUG: FileBase=%s FileExt=%s" % (FileBase, FileExt))
  if Opts.ForceCreateAttr:
    if Opts.Debug:
      print( "DEBUG: Opts.ForceCreateAttr" )
    try:
      SetHashForFile( Opts, FileName, FileBase + FileExt )
      DestBase = CalcHashForFile( Opts, FileBase + FileExt)
      DestName = os.path.join( FileDir, DestBase + Opts.Extension )
      if Opts.Debug:
        print( "DEBUG: DestBase=%s DestName=%s" % (DestBase, DestName))
      shutil.move( FileName, DestName )
      if Opts.Verbose:
        sys.stderr.write("%s: %s%s -> %s%s\n" % (Opts.PrgName, FileBase, FileExt, DestBase, Opts.Extension))
      else:
        sys.stderr.write(".")
    except:
      if Opts.Verbose:
        sys.stderr.write("\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName))
        sys.stderr.flush()
      else:
        sys.stderr.write( "x" )
  elif Opts.StoreAttr:
    if Opts.Debug:
      print( "DEBUG: Opts.StoreAttr" )
    try:
      # Try first to get xattr
      StoredName = GetHashForFile( Opts, FileName )
      if Opts.Debug:
        print( "DEBUG: StoredName=%s" % (StoredName,) )
      if Opts.Verbose:
        sys.stderr.write( "\n%s: File \"%s\" has attribute, skipped\n" % (Opts.PrgName, FileName) )
    except:
      try:
        SetHashForFile( Opts,  FileName, FileBase + FileExt )
        DestBase = CalcHashForFile( Opts, FileBase + FileExt)
        DestName = os.path.join( FileDir, DestBase + Opts.Extension )
        if Opts.Debug:
          print( "DEBUG: DestBase=%s DestName=%s" % (DestBase, DestName) )
        shutil.move( FileName, DestName )
      except:
        if Opts.Verbose:
          sys.stderr.write( "\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName) )
          sys.stderr.flush()
        else:
          sys.stderr.write( "x" )
  elif Opts.DeleteAttr:
    try:
      # Try to get attr
      StoredName = GetHashForFile( Opts, FileName )
      try:
        DeleteHash( Opts, FileName )
        if Opts.Verbose:
          sys.stderr.write( "%s: %s\n" % (Opts.PrgName, FileName) )
        else:
          sys.stderr.write( "." )
      except:
        if Opts.Verbose:
          sys.stderr.write( "%s: Could not delete xattr for \"%s\"\n" % (Opts.PrgName, FileName) )
        else:
          sys.stderr.write( "x" )
    except:
      if Opts.Verbose:
        sys.stderr.write( "%s: \"%s\" does not have xattr, skipping...\n" % (Opts.PrgName, FileName) )
      else:
        sys.stderr.write( "-" )

parser = OptionParser(usage="%prog [ --OPTIONS ] DIR ... FILE ... ")
parser.add_option( "-u", "--unmangle", dest="Mode", action="store_true", help="Mode: Mangle/Unmangle", default=False)
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-r", "--recursive", dest="Recursive", action="store_true", help="Recurse directories", default=False)
parser.add_option( "-X", "--store-xattr", dest="StoreAttr", action="store_true", help="Store extended attributes if not found", default=True)
parser.add_option( "-y", "--always-recreate-xattr", dest="ForceCreateAttr", action="store_true", help="Always recreate extended attributes", default=False)
parser.add_option( "-c", "--check", dest="VerifyAttr", action="store_true", help="Check file against stored extended attribute", default=False)
parser.add_option( "-d", "--delete-attr", dest="DeleteAttr", action="store_true", help="Delete stored xattr", default=False)
parser.add_option( "-k", "--crypto-alg", dest="Crypto", action="store", help="Crypto hash algorithm", default="md5")
parser.add_option( "-x", "--extension", dest="Extension", action="store", help="Set mangled extension", default=".MM")
parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="mangler", help="Official program name", metavar="PRGNAME" )
parser.add_option( "--DEBUG", dest="Debug", action="store_true", default=False, help=SUPPRESS_HELP)

(Options, Args) = parser.parse_args()

if Options.ForceCreateAttr:
  Options.StoreAttr = True
  Options.DeleteAttr = False
  if Options.Debug:
    print("DEBUG: StoreAttr=True\nDEBUG: DeleteAttr=False\n")

if Options.DeleteAttr:
  Options.StoreAttr = False
  Options.ForceCreateAttr = False
  if Options.Debug:
    print("DEBUG: StoreAttr=False\nDEBUG: ForceCreateAttr=False")
  
Options.AttrName = Options.PrgName + "-name."
if Options.Debug:
  print("DEBUG: AttrName=%s" % (Options.AttrName,))

if len( Args ) > 0 :
  import hashlib
  if Options.Verbose:
    if Options.ForceCreateAttr:
      print( "%s: creating and unconditionally recreating extented attributes (%s)" % (Options.PrgName, Options.AttrName) )
    elif Options.StoreAttr:
      print( "%s: creating and saving extented attributes (%s)" % (Options.PrgName, Options.AttrName) )
  for OneArg in Args:
    if os.path.isfile( OneArg ):
      if Options.Debug:
        print( "DEBUG: OneArg=%s IsFile" % (OneArg,) )
      try:
        if Options.Mode:
          if Options.Debug:
            print( "DEBUG: UnMangle(%s)" % (OneArg) )
          UnmangleOneFile( Options, OneArg )
        else:
          if Options.Debug:
            print( "DEBUG: Mangle(%s)" % (OneArg) )
          MangleOneFile( Options, OneArg )
      except (IOError, OSError):
        pass
    if os.path.isdir( OneArg ) and Options.Recursive:
      for StartDir, Dirs, Files in os.walk( OneArg ):
        for OneFile in Files:
          try:
            if Options.Mode:
              if Options.Debug:
                print( "DEBUG: UnMangle(%s)" % (OneArg) )
              UnmangleOneFile( Options, os.path.join( StartDir, OneFile ) )
            else:
              if Options.Debug:
                print( "DEBUG: Mangle(%s)" % (OneArg) )
              MangleOneFile( Options, os.path.join( StartDir, OneFile ) )
          except (IOError, OSError):
            pass
  if not Options.Verbose:
    sys.stderr.write( "\n" )
else:
  parser.error("one or more arguments are needed!")