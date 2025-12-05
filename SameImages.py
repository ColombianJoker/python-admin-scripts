#!/usr/bin/python
# encoding: utf-8
"""
Same.py: identifies and lists repeated files. Identifies repeated files using digital crypto-hashes

Created by Ramón Barrios Lascar on 2006-12-15.
Changed 2010-03-29: Changed line 79 "import md5" to "import hashlib"
Changed 2010-03-29: Changed line 32 "import hash=md5.new()" to "hash = hashlib.new('md5')"
Changed 2010-07-23: Enhanced to use and/or store hashes in extended attributes
Copyright (c) 2007 iKnow. All rights reserved.
"""
import sys, os, string, xattr, tempfile, Image
# from optparse import OptionParser
from optparse import OptionParser, SUPPRESS_HELP

def AddToHashList( HashList, FileName, FileHash ):
  if HashList.has_key( FileHash ):
    # If the hash is in the hash list add the filename to the list of files with this hash
    HashList[ FileHash ].append( FileName )
  else:
    # If NOT, the hash is NOT in the list add a new keyed element to the hash list
    HashList[ FileHash ] = [ FileName ]
  return HashList

def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  hash = hashlib.new( Opts.Crypto )
  OpenFile = open( FileName )
  for OneLine in OpenFile:
    hash.update( OneLine )
  OpenFile.close()
  return hash.hexdigest()
  
def CalcReducedImage( Opts, Filename ):
   # Create reduced image for one file
   return True

def ProcessOneFile( Hashes, Opts, FileName ):
  # Calculates secure sum of a file
  if os.path.getsize( FileName ):
    # Process only sizeable files
    if Opts.Debug:
      sys.stderr.write( "  %s\t" % (FileName,) )
    if not Opts.ForceCreateAttr or Opts.UseAttr:
      FileHashRead = False
      # If working with extended attributes then read attribute
      try:
        FileHash = xattr.getxattr( FileName, "same-hash." + Opts.Crypto )
        if not Opts.ForceCreateAttr:
          FileHashRead = True
      except KeyError:
        FileHash = CalcHashForFile( Opts, FileName )
    else:
      FileHash = CalcHashForFile( Opts, FileName )
    
    if ( Opts.StoreAttr and not FileHashRead ) or Opts.ForceCreateAttr:
      try:
        xattr.setxattr( FileName, "same-hash." + Opts.Crypto, FileHash )
      except:
        if Opts.Verbose:
          sys.stdout.write( "\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName) )
          sys.stdout.flush()
        
    Hashes = AddToHashList( Hashes, FileName, FileHash )
    Opts.Count = Opts.Count + 1
    if Opts.Verbose:
      if Opts.ForceCreateAttr:
        sys.stdout.write( "+" )
      elif Opts.UseAttr:
        sys.stdout.write( "=" )
      else:
        sys.stdout.write( "-" )
      if (Opts.Count % Opts.LineWidth) == 0:
        print( Opts.Format % Opts.Count )
      else:
        if (Opts.Count % 10) == 0:
          sys.stdout.write( " " )
          sys.stdout.flush()
  else:
    if Opts.Verbose:
      sys.stdout.write( "\a\b^" )
  if Opts.Debug:
    sys.stderr.write( "\n" )
    sys.stderr.flush()
  return Hashes, Opts
  
def mycmp( a, b ):
  return cmp( len( a ), len( b ) )

def ExecuteForFile( Opts, OneFile ):
  # Execute script command with one file only
  OneFile = '"' + OneFile + '"'
  os.system(string.replace( Opts.ExecuteCommand, Opts.Replacement, OneFile))

try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] DIR ... FILE ... ")
  parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
  parser.add_option( "-r", "--recursive", dest="Recursive", action="store_true", help="Recurse directories", default=False)
  parser.add_option( "-D", "--duplicates", dest="OnlyDups", action="store_true", help="Show only duplicates", default=False)
  parser.add_option( "-m", "--mode", dest="Crypto", action="store", type="string", help="Digest algoritm type (SHA1, SHA224, SHA256, SHA384, SHA512, MD2, MD4, MD5, MDC2, RMD160, defaults to MD5)", default="md5", metavar="MODE" )
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
  parser.add_option( "-y", "--always-recreate-xattr", dest="ForceCreateAttr", action="store_true", help="Always recreate extended attributes", default=False)
  parser.add_option( "-l", "--skip-symlinks", dest="SkipSymLinks", action="store_true", help="Skip symbolic links", default=False)
  parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME" )
  parser.add_option( "--DEBUG", dest="Debug", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option( "--DIGITS", "-#", dest="Digits", action="store", type="int", default=4, help=SUPPRESS_HELP)
  parser.add_option( "--BASEFORMAT", "-B", dest="BaseFormat", action="store", default=" [%%%dd]", help=SUPPRESS_HELP)
  parser.add_option( "--width", "-w", dest="LineWidth", action="store", type="int", default=100, help=SUPPRESS_HELP)

  (Options, Args) = parser.parse_args()
  if Options.ForceCreateAttr:
    Options.StoreAttr = True
  if Options.StoreAttr:
    Options.UseAttr = True
  Options.Crypto = string.lower( Options.Crypto )
  # Initialize file count
  Options.Count = 0
  # Options.PrgName = "same"
  if Options.Parsable:
    Options.ShowHash = False
  Options.Format=Options.BaseFormat % Options.Digits

  # print "Options = %s" % ( Options )
  # print "Args    = %s" % ( Args )

  MasterHashes = {}

  if len( Args ) > 0 :
    import hashlib
    if Options.Verbose:
      print( "%s using %s algoritm" % ( Options.PrgName, string.upper( Options.Crypto ) ) )
      if Options.ForceCreateAttr:
        print( "%s creating and unconditionally recreating extented attributes (%s)" % ( Options.PrgName, "same-hash." + Options.Crypto) )
      elif Options.StoreAttr:
        print( "%s creating and saving extented attributes (%s)" % ( Options.PrgName, "same-hash." + Options.Crypto) )
      elif Options.UseAttr:
          print( "%s creating extented attributes (%s) without saving" % ( Options.PrgName, "same-hash." + Options.Crypto) )
    for OneArg in Args:
      if Options.SkipSymLinks:
        if Options.Debug:
          sys.stderr.write("  DEGUG: SkipSymLinks\n" )
        if ( not os.path.islink( OneArg ) and os.path.isfile( OneArg ) ) or ():  
          try:
            MasterHashes, Options = ProcessOneFile( MasterHashes, Options, OneArg )
          except (IOError, OSError):
            pass
        else:
          if os.path.isfile( OneArg ):
            try:
              MasterHashes, Options = ProcessOneFile( MasterHashes, Options, OneArg )
            except (IOError, OSError):
              pass
      if os.path.isdir( OneArg ) and Options.Recursive:
        if not os.path.islink( OneArg ):
          for StartDir, Dirs, Files in os.walk( OneArg ):
            for OneFile in Files:
              if Options.SkipSymLinks and not os.path.islink( os.path.join( StartDir, OneFile ) ):
                try:
                  MasterHashes, Options = ProcessOneFile( MasterHashes, Options, os.path.join( StartDir, OneFile ) )
                except (IOError, OSError):
                  pass
              else:
                if not Options.SkipSymLinks:
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
  else:
    parser.error("one or more arguments are needed!")
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
