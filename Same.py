#!/usr/bin/python
# encoding: utf-8
"""
Same.py: identifies and lists repeated files. Identifies repeated files using digital crypto-hashes

Created by Ramón Barrios Lascar on 2006-12-15.
Changed 2010-03-29: Changed line 79 "import md5" to "import hashlib"
Changed 2010-03-29: Changed line 32 "import hash=md5.new()" to "hash = hashlib.new('md5')"
Copyright (c) 2007 iKnow. All rights reserved.
"""

import sys, os, string
from optparse import OptionParser

def AddToHashList( HashList, FileName, FileHash ):
  if HashList.has_key( FileHash ):
    # If the hash is in the hash list add the filename to the list of files with this hash
    HashList[ FileHash ].append( FileName )
  else:
    # If NOT, the hash is NOT in the list add a new keyed element to the hash list
    HashList[ FileHash ] = [ FileName ]
  return HashList

def ProcessOneFile( Hashes, Opts, FileName ):
  # Calculates secure sum of a file
  if os.path.getsize( FileName ):
    # Process only sizeable files
    # hash = Opts.Crypto.Opts.Crypto() GENERAL
    hash = hashlib.new( Opts.Crypto )
    OpenFile = open( FileName )
    for OneLine in OpenFile:
      hash.update( OneLine )
    OpenFile.close()
    FileHash = hash.hexdigest()
    Hashes = AddToHashList( Hashes, FileName, FileHash )
    Opts.Count = Opts.Count + 1
    if Opts.Verbose:
      sys.stdout.write( "." )
      if (Opts.Count % 100) == 0:
        print( " %d" % Opts.Count )
      else:
        if (Opts.Count % 10) == 0:
          sys.stdout.write( " " )
          sys.stdout.flush()
  return Hashes, Opts
    
def mycmp( a, b ):
  return cmp( len( a ), len( b ) )
  
def ExecuteForFile( Opts, OneFile ):
  # Execute script command with one file only
  OneFile = '"' + OneFile + '"'
  os.system(string.replace( Opts.ExecuteCommand, Opts.Replacement, OneFile))

parser = OptionParser()
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-r", "--recursive", dest="Recursive", action="store_true", help="Recurse directories", default=False)
parser.add_option( "-D", "--duplicates", dest="OnlyDups", action="store_true", help="Show only duplicates", default=False)
parser.add_option( "-m", "--mode", dest="Crypto", action="store", type="string", help="Digest algoritm type (md5 or sha, defaults to md5)", default="md5", metavar="MODE" )
parser.add_option( "-p", "--parsable", dest="Parsable", action="store_true", help="Parsable listing format", default=False)
parser.add_option( "-s", "--separated", dest="Separated", action="store_true", help="Separated repeated items", default=False)
parser.add_option( "-n", "--noshow", dest="ShowHash", action="store_false", help="Don't show the hashes", default=True)
parser.add_option( "-N", "--nodot", dest="NoDot", action="store_true", help="Don't show initial ./", default=False)
parser.add_option( "-0", "--null", dest="NullTerminated", action="store_true", help="Null terminated file names", default=False)
parser.add_option( "-e", "--execute", dest="ExecuteCommand", action="store", type="string", help="Execute command with each duplicated file")
parser.add_option( "-k", "--ok", dest="ConditionalCommand", action="store", type="string", help="Execute command with each duplicated file, asking first")
parser.add_option( "-I", "--replace-string", dest="Replacement", action="store", type="string", help="Replacement meta string (defaults to {})", default="{}")

(Options, Args) = parser.parse_args()
# Initialize file count
Options.Count = 0
Options.PrgName = "same"
if Options.Parsable:
  Options.ShowHash = False

# print "Options = %s" % ( Options )
# print "Args    = %s" % ( Args )

MasterHashes = {}

if len( Args ) > 0 :
  import hashlib
  if Options.Verbose:
    print( "%s using %s algoritm" % ( Options.PrgName, string.upper( Options.Crypto ) ) )
  for OneArg in Args:
    if os.path.isfile( OneArg ):
      try:
        MasterHashes, Options = ProcessOneFile( MasterHashes, Options, OneArg )
      except (IOError, OSError):
        pass
    if os.path.isdir( OneArg ) and Options.Recursive:
      for StartDir, Dirs, Files in os.walk( OneArg ):
        for OneFile in Files:
          try:
            MasterHashes, Options = ProcessOneFile( MasterHashes, Options, os.path.join( StartDir, OneFile ) )
          except (IOError, OSError):
            pass
  if Options.Verbose:
    print
  
  # Print hash list
  for OneHash, OneList in MasterHashes.iteritems():
    # Only print hashes with repeated files
    if len( OneList ) > 1:
      OneList.sort( mycmp )
      if Options.ShowHash:
        print( "%s: " % OneHash )
      for i, OneItem in enumerate( OneList ):
        if Options.NoDot:
          if OneItem[:2] == "./":
            OneItem = OneItem[2:]
        if (( i==0 ) and ( not Options.OnlyDups )) or ( i != 0 ):
          if Options.NullTerminated:
            if Options.Parsable:
              sys.stdout.write( "%s:%s\0" % (OneHash, OneItem))
            else:
              sys.stdout.write( "%s\0" % (OneItem,))
          else:
            if Options.Parsable:
              print( "%s:%s" % ( OneHash, OneItem ) )
            else:
              print( "%s " % OneItem )
      if Options.Separated:
        print
      # Execute part
      if Options.ExecuteCommand:
        ExecuteForFile( Options, OneItem )
        