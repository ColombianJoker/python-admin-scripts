#!/usr/bin/python

import sys, os, string, optparse
# from optparse import OptionParser

def ProcessOneFile( Opts, FileName ):
  RealFileName = os.path.expanduser( FileName )
  PathName, NameExt = os.path.splitext( RealFileName )
  Opts.Count += 1
  if not NameExt.islower() and string.lower( NameExt ) == ".mp3":
    NewNameExt = string.lower( NameExt )
    NewName = PathName + NewNameExt
    if RealFileName != NewName:
      try:
        os.rename( RealFileName, NewName )
        sys.stdout.write( "%s\n" % ( RealFileName ) )
        Opts.Corrected += 1
      except:
        sys.stderr.write( "%s: problem renaming \'%s\'!\n" % ( Opts.PrgName, RealFileName ) )
    
# Start of main program
parser = optparse.OptionParser()
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)

(Options, Args) = parser.parse_args()
# Initialize file count
Options.Count = 0
Options.Corrected = 0
Options.PrgName = "Mp3Adjust"

if len( Args ) > 0:
  # Process all
  for OneArg in Args:
    if os.path.isfile( OneArg ):
      ProcessOneFile( Options, OneArg )
    if os.path.isdir( OneArg ):
      for StartDir, Dirs, Files in os.walk( OneArg ):
        for OneFile in Files:
          ProcessOneFile( Options, os.path.join( StartDir, OneFile ) )
  sys.stderr.write( "%s: %d files processed, %d files corrected.\n" % ( Options.PrgName, Options.Count, Options.Corrected ) )
else:
  sys.stderr.write( "%s: Too few arguments!\n" % ( Options.PrgName, ) )
  sys.exit( 2 )
