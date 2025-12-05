#!/usr/bin/python
# encoding: utf-8
"""
Same.py: identifies and lists repeated files. Identifies repeated files using digital crypto-hashes

Created by Ramón Barrios Lascar on 2006-12-15.
Changed 2010-03-29: Changed line 79 "import md5" to "import hashlib"
Changed 2010-03-29: Changed line 32 "import hash=md5.new()" to "hash = hashlib.new('md5')"
Changed 2010-07-23: Enhanced to use and/or store hashes in extended attributes
Changed 2012-09-29: Adjust output in DEBUG mode
Copyright (c) 2007 iKnow. All rights reserved.
"""
import sys, os, string, xattr
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

def ProcessOneFile( Hashes, Opts, FileName ):
  # Calculates secure sum of a file
  if os.path.basename( FileName ) == ".DS_Store":
    if Opts.Debug:
      sys.stderr.write( "  DEBUG: %s: .DS_Store found\n" % (Opts.PrgName,) )
    return Hashes, Opts
  if Opts.Animated:
    Opts.OneSpinner.spin()
  if os.path.getsize( FileName ):
    # Process only sizeable files
    # if Opts.Debug:
    #   sys.stderr.write( "  %s\t" % (FileName,) )
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
    if Opts.Debug:
      # sys.stderr.write("  %s %s\n" % (FileHash, FileName))
      sys.stderr.write("  %s %s" % (FileHash, FileName))
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
  parser.add_option( "-t", "--show-time", dest="ShowTime", action="store_true", help="Show time used", default=False)
  parser.add_option( "-a", "--animated", dest="Animated", action="store_true", help="Show animated progress")
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
  if Options.ShowTime or Options.Debug:
    import time
    Options.StartTime = time.time()
    Options.EndTime = time.time ()
  if Options.Debug:
    Options.Animated = False
  # --------------------------------------------------------------------------------
  if Options.Animated:
    Options.Verbose = False
    import time
    import itertools
    import sys
    import threading

    class Spinner(threading.Thread):
        '''Represent a random work indicator, handled in a separate thread'''

        # Spinner glyphs
        glyphs = ('|', '/', '-', '\\', '|', '/', '-')
        # Output string format
        output_format = '%-78s%-2s'
        # Message to output while spin
        spin_message = ''
        # Message to output when done
        done_message = ''
        # Time between spins
        spin_delay = 0.1

        def __init__(self, *args, **kwargs):
            '''Spinner constructor'''
            threading.Thread.__init__(self, *args, **kwargs)
            self.daemon = True
            self.__started = False
            self.__stopped = False
            self.__glyphs = itertools.cycle(iter(self.glyphs))

        def __call__(self, func, *args, **kwargs):
            '''Convenient way to run a routine with a spinner'''
            self.init()
            skipped = False

            try:
                return func(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                skipped = True
            finally:
                self.stop(skipped)

        def init(self):
            '''Shows a spinner'''
            self.__started = True
            self.start()

        def run(self):
            '''Spins the spinner while do some task'''
            while not self.__stopped:
                self.spin()

        def spin(self):
            '''Spins the spinner'''
            if not self.__started:
                raise NotStarted('You must call init() first before using spin()')

            if sys.stdin.isatty():
                sys.stdout.write('\r')
                sys.stdout.write(self.output_format % (self.spin_message,
                                                       self.__glyphs.next()))
                sys.stdout.flush()
                time.sleep(self.spin_delay)

        def stop(self, skipped=None):
            '''Stops the spinner'''
            if not self.__started:
                raise NotStarted('You must call init() first before using stop()')

            self.__stopped = True
            self.__started = False

            if sys.stdin.isatty() and not skipped:
                sys.stdout.write('\b%s%s\n' % ('\b' * len(self.done_message),
                                               self.done_message))
                sys.stdout.flush()

    class NotStarted(Exception):
        '''Spinner not started exception'''
        pass
    # --------------------------------------------------------------------------------

  # print "Options = %s" % ( Options )
  # print "Args    = %s" % ( Args )

  MasterHashes = {}

  if len( Args ) > 0 :
    import hashlib
    if Options.Verbose:
      sys.stderr.write( "%s: using %s algoritm\n" % ( Options.PrgName, string.upper( Options.Crypto ) ) )
      if Options.ForceCreateAttr:
        sys.stderr.write( "%s: creating and unconditionally recreating extented attributes (%s)\n" % ( Options.PrgName, "same-hash." + Options.Crypto) )
      elif Options.StoreAttr:
        sys.stderr.write( "%s: creating and saving extented attributes (%s)\n" % ( Options.PrgName, "same-hash." + Options.Crypto) )
      elif Options.UseAttr:
          sys.stderr.write( "%s: creating extented attributes (%s) without saving\n" % ( Options.PrgName, "same-hash." + Options.Crypto) )
    if Options.Animated:
       Options.OneSpinner = Spinner ()
       Options.OneSpinner.spin_message = "Scanning..."
       Options.OneSpinner.done_message = "Done" 
    if Options.Debug:
      sys.stderr.write( "  DEBUG: ")
    if Options.ShowTime or Options.Debug:
      StartTime = time.localtime(Options.StartTime)
      sys.stderr.write( "%s: started at %04d/%02d/%02d %02d:%02d:%02d\n" % (Options.PrgName, StartTime[0], StartTime[1], StartTime[2], StartTime[3], StartTime[4], StartTime[5]))
    for OneArg in Args:
      if Options.Animated:
        Options.OneSpinner.init()
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
    if Options.Animated:
      Options.OneSpinner.stop(False)
    if Options.Debug:
      sys.stderr.write( " DEBUG: ")
    if Options.ShowTime or Options.Debug:
      Options.EndTime = time.time()
      EndTime = time.localtime(Options.EndTime)
      sys.stderr.write( "%s: ended at %04d/%02d/%02d %02d:%02d:%02d\n" % (Options.PrgName, EndTime[0], EndTime[1], EndTime[2], EndTime[3], EndTime[4], EndTime[5]))
      if Options.Debug:
        sys.stderr.write( " DEBUG: ")
      sys.stderr.write( "%s: processed %d files, in %fs (%fs/file)\n" % (Options.PrgName, Options.Count, Options.EndTime-Options.StartTime, (Options.EndTime-Options.StartTime)/Options.Count))
  else:
    parser.error("one or more arguments are needed!")
except KeyboardInterrupt:
  if Options.Animated:
    Options.OneSpinner.stop(True)
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
