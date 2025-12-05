#!/usr/bin/python
# encoding: utf-8
"""
FileHash.py: Manage digital hashes of contents of files for identification purposes

Created by Ramón Barrios Lascar on 2010-07-24.
Copyright (c) 2010 iKnow. All rights reserved.
"""

import sys, os, string, xattr
from optparse import OptionParser

def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  hash = hashlib.new( Opts.Crypto )
  OpenFile = open( FileName )
  for OneLine in OpenFile:
    hash.update( OneLine )
  OpenFile.close()
  return hash.hexdigest()

def GetHashForFile( Opts, FileName ):
  return xattr.getxattr( FileName, Opts.HashName )
  
def DeleteHash( Opts, FileName ):
  try:
    xattr.removexattr( FileName, Opts.HashName )
  except:
    if Opts.Verbose:
      sys.stdout.write( "%s: %s has no %s attribute\n" % (Opts.PrgName, FileName, Opts.HashName))
      sys.stdout.flush()
      
def ProcessOneFile( Opts, FileName ):
  # Calculates secure sum of a file
  Opts.Count = Opts.Count + 1
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
parser.add_option( "-m", "--mode", dest="Crypto", action="store", type="string", help="Digest algoritm type (SHA1, SHA224, SHA256, SHA384, SHA512, MD2, MD4, MD5, MDC2, RMD160, defaults to MD5)", default="md5", metavar="MODE" )
parser.add_option( "-p", "--parsable", dest="Parsable", action="store_true", help="Parsable listing format", default=False)
parser.add_option( "-n", "--noshow", dest="ShowHash", action="store_false", help="Don't show the hashes", default=True)
parser.add_option( "-N", "--nodot", dest="NoDot", action="store_true", help="Don't show initial ./", default=False)
parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME" )

(Options, Args) = parser.parse_args()

if Options.ForceCreateAttr:
  Options.StoreAttr = True
  Options.DeleteAttr = False

if Options.DeleteAttr:
  Options.StoreAttr = False
  Options.ForceCreateAttr = False
  
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
    if os.path.isfile( OneArg ):
      try:
        ProcessOneFile( Options, OneArg )
      except (IOError, OSError):
        pass
    if os.path.isdir( OneArg ) and Options.Recursive:
      for StartDir, Dirs, Files in os.walk( OneArg ):
        for OneFile in Files:
          try:
            ProcessOneFile( Options, os.path.join( StartDir, OneFile ) )
          except (IOError, OSError):
            pass
  if Options.Verbose:
    print
else:
  parser.error("one or more arguments are needed!")