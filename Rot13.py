#!/usr/bin/env python
# Rot13

import os, sys, string
from optparse import OptionParser, SUPPRESS_HELP

def NameForFile( Opts, FileName ):
  OneDir = os.path.dirname( FileName )
  OneBase = os.path.basename( FileName )
  OneExt = os.path.splitext( FileName )[1]
  if OneExt == ".rot":
    OneBase = os.path.splitext( FileName )[0]
  RotedFile = OneBase.translate(Opts.RotF)
  if OneExt != ".rot":
    FinalFile = os.path.join( OneDir,RotedFile ) + ".rot"
  else:
    FinalFile = os.path.join( OneDir,RotedFile )
  return FinalFile

def ListRottedFile(Opts, OneFile):
  FinalFile = NameForFile( Opts, OneFile)
  sys.stdout.write( "%s: %s\n" % (OneFile, FinalFile))

def RotFile(Opts, OneFile):
  FinalFile = NameForFile( Opts, OneFile )
  try:
    OpenRoted = open( os.path.expanduser( FinalFile), "w" )
    if Opts.DEBUG:
      sys.stderr.write( "%s.%s: %s open W\n" % (Opts.PrgName, "RotFile", FinalFile) )
    OpenOriginal = open( os.path.expanduser( OneFile ) )
    if Opts.DEBUG:
      sys.stderr.write( "%s.%s: %s open R\n" % (Opts.PrgName, "RotFile", OneFile) )
    if Opts.Verbose:
      sys.stdout.write( "%s: %s -> %s\n" % (Opts.PrgName, OneFile, FinalFile) )
    else:
      sys.stdout.write( "." )
    for TextLine in OpenOriginal.readlines():
      RotedLine = TextLine.translate( Opts.RotF )
      OpenRoted.writelines( RotedLine )
    OpenOriginal.close()
    OpenRoted.close()
    if Opts.DEBUG:
      sys.stderr.write( "%s.%s: %s %s C\n" % (Opts.PrgName, "RotFile", OneFile, FinalFile) )
    if Opts.RemoveOriginal:
      try:
        os.unlink( os.path.expanduser( OneFile ) )
      except:
        sys.stderr.write( "%s.%s: error removing\"%s\"\n" % (Opts.PrgName, "RotFile", OneFile) )
  except:
    sys.stderr.write( "%s: Error processing \"%s\"\n" % (Opts.PrgName, OneFile))
    
# Start of main program
parser = OptionParser()
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-R", "--remove", dest="RemoveOriginal", action="store_true", help="Remove original", default=False)
parser.add_option( "-r", "--recursive", "--recurse", dest="Recursive", action="store_true", help="Recursive", default=False)
parser.add_option( "-l", "--list", dest="ListOnly", action="store_true", help="List names only", default=False)
parser.add_option( "--DEBUG", dest="DEBUG", action="store_true", help=SUPPRESS_HELP, default=False)

(Options, Args) = parser.parse_args()
Options.PrgName = "Rot13"
Options.RotF = str.maketrans('ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz','NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm')

if len(Args) > 0:
  # Process all
  for OneArg in Args:
    if os.path.isfile(OneArg):
      if not Options.ListOnly:
        RotFile(Options, OneArg)
      else:
        ListRottedFile(Options, OneArg)
    if os.path.isdir(OneArg):
      for StartDir, Dirs, Files in os.walk(OneArg):
        for OneFile in Files:
          if not Options.ListOnly:
            RotFile(Options,os.path.join(StartDir,OneFile))
          else:
            ListRottedFile(Options,os.path.join(StartDir,OneFile))
  if not Options.Verbose and not Options.ListOnly:
    sys.stdout.write("\n")
    sys.stdout.flush()
else:
  sys.stderr.write("%s: too few arguments!\n" % (Options.PrgName,))
  sys.exit(2)
