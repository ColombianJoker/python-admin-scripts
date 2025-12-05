#!/usr/bin/python
"""
SameImages.py identifies and lists repeated image files. Identifies repeated image files using digital
crypto-hashes from reduced image file versions
"""

import sys, os, string, xattr, tempfile, Image
from optparse import OptionParser, SUPPRESS_HELP

# --------------------------------------------------------------------------
def AddToHashList( HashList, FileName, FileHash ):
  """ add to global hash list """
  if HashList.has_key( FileHash ):
    # If the hash is in the hash list add the filename to the list of files with this hash
    HashList[ FileHash ].append( FileName )
  else:
    # If NOT, the hash is NOT in the list add a new keyed element to the hash list
    HashList[ FileHash ] = [ FileName ]
  return HashList

# --------------------------------------------------------------------------
def CheckImageExtension( Opts, FileName ):
  """ check for valid image types """
  FileNameParts = FileName.rsplit('.')
  ExtensionList = ['jpeg', 'jpg', 'gif', 'png']
  if FileNameParts[1].lower() in ExtensionList:
    if Opts.Debug:
      sys.stderr.write( "  DEBUG: %s is a valid image file\n" % (FileName,) )
    ToReturn = True
  else:
    if Opts.Debug:
      sys.stderr.write( "  DEBUG: %s is NOT a valid image file\n" % (FileName,) )
    ToReturn = False
  return ToReturn

# --------------------------------------------------------------------------
def CalcHashForImage( Opts, FileName ):
  # Creates a thumbnailed image and calculate a hash from that
  FileBaseName = os.path.basename( FileName )
  TempFileName = os.path.join( "/tmp", FileBaseName )
  if Opts.Debug:
    sys.stderr.write( "  DEBUG: %s\n" % (TempFileName,) )
  AImage = Image.open( FileName )
  AImageW, AImageH = AImage.size
  if (AImageW <= Opts.ReducedWidth) and (AImageH <= Opts.ReducedHeight ):
    AImage.save( TempFileName )
  else:
    ReducedSize = Opts.ReducedWidth, Opts.ReducedHeight
    AImage.thumbnail( ReducedSize, Image.BILINEAR )
    AImage.save( TempFileName )
  hash = hashlib.new( Opts.Crypto )
  OpenImageFile = open( TempFileName )
  for OneLine in OpenImageFile:
    hash.update( OneLine )
  OpenImageFile.close()
  os.unlink( TempFileName )
  ImageHash = hash.hexdigest()
  return ImageHash

# --------------------------------------------------------------------------
def CalcHashForFile( Opts, FileName ):
  # Calculate hash for one file
  hash = hashlib.new( Opts.Crypto )
  OpenFile = open( FileName )
  for OneLine in OpenFile:
    hash.update( OneLine )
  OpenFile.close()
  return hash.hexdigest()

# --------------------------------------------------------------------------
def ProcessOneFile( Hashes, ImageHashes, Opts, FileName ):
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
      try:
        ImageFileHash = xattr.getxattr( FileName, "same-imagehash." + Opts.Crypto )
        if not Opts.ForceCreateAttr:
          FileHashRead = True
      except KeyError:
        ImageFileHash = CalcHashForImage( Opts, FileName )
    else:
      FileHash = CalcHashForFile( Opts, FileName )
      ImageFileHash = CalcHashForImage( Opts, FileName )
    
    if ( Opts.StoreAttr and not FileHashRead ) or Opts.ForceCreateAttr:
      try:
        xattr.setxattr( FileName, "same-hash." + Opts.Crypto, FileHash )
        xattr.setxattr( FileName, "same-imagehash." + Opts.Crypto, ImageFileHash )
      except:
        if Opts.Verbose:
          sys.stdout.write( "\n%s: Could not write xattr for %s!\n" % (Opts.PrgName, FileName) )
          sys.stdout.flush()
        
    Hashes = AddToHashList( Hashes, FileName, FileHash )
    ImageHashes = AddToHashList( ImageHashes, FileName, ImageFileHash )
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
  return Hashes, ImageHashes, Opts
  
# --------------------------------------------------------------------------
def mycmp( a, b ):
  return cmp( len( a ), len( b ) )
  
# ===============================================================================================================
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
  parser.add_option( "-Y", "--replace-string", dest="Replacement", action="store", type="string", help="Replacement meta string (defaults to {})", default="{}")
  parser.add_option( "-x", "--xattr", dest="UseAttr", action="store_true", help="Use extended attributes", default=False)
  parser.add_option( "-X", "--store-xattr", dest="StoreAttr", action="store_true", help="Store extended attributes if not found", default=False)
  parser.add_option( "-y", "--always-recreate-xattr", dest="ForceCreateAttr", action="store_true", help="Always recreate extended attributes", default=False)
  parser.add_option( "-l", "--skip-symlinks", dest="SkipSymLinks", action="store_true", help="Skip symbolic links", default=False)
  parser.add_option( "-P", "--program-name", dest="PrgName", action="store", default="same", help="Official program name", metavar="PRGNAME" )
  parser.add_option( "-I", "--compare-images", dest="CompareImages", action="store_true", default=False, help="Compare image files" )
  parser.add_option( "-W", "--reduced-width", dest="ReducedWidth", action="store", type="int", default=320, help="Reduced image width" )
  parser.add_option( "-H", "--reduced-height", dest="ReducedHeight", action="store", type="int", default=240, help="Reduced image height" )
  parser.add_option( "--DEBUG", dest="Debug", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option( "--DIGITS", "-#", dest="Digits", action="store", type="int", default=4, help=SUPPRESS_HELP)
  parser.add_option( "--BASEFORMAT", "-B", dest="BaseFormat", action="store", default=" [%%%dd]", help=SUPPRESS_HELP)
  parser.add_option( "--line-width", "-L", dest="LineWidth", action="store", type="int", default=100, help=SUPPRESS_HELP)
  
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
  ImageHashes = {}

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
          sys.stderr.write( "  DEGUG: SkipSymLinks\n" )
          sys.stderr.write( "  DEBUG: %sx%s\n" % (Options.ReducedWidth, Options.ReducedHeight) )
        if ( not os.path.islink( OneArg ) and os.path.isfile( OneArg ) ) or ():  
          try:
            MasterHashes, ImageHashes, Options = ProcessOneFile( MasterHashes, ImageHashes, Options, OneArg )
          except (IOError, OSError):
            pass
        else:
          if os.path.isfile( OneArg ):
            try:
              MasterHashes, ImageHashes, Options = ProcessOneFile( MasterHashes, ImageHashes, Options, OneArg )
            except (IOError, OSError):
              pass
      if os.path.isdir( OneArg ) and Options.Recursive:
        if not os.path.islink( OneArg ):
          for StartDir, Dirs, Files in os.walk( OneArg ):
            for OneFile in Files:
              if Options.SkipSymLinks and not os.path.islink( os.path.join( StartDir, OneFile ) ):
                try:
                  MasterHashes, ImageHashes, Options = ProcessOneFile( MasterHashes, ImageHashes, Options, os.path.join( StartDir, OneFile ) )
                except (IOError, OSError):
                  pass
              else:
                if not Options.SkipSymLinks:
                  try:
                    MasterHashes, ImageHashes, Options = ProcessOneFile( MasterHashes, ImageHashes, Options, os.path.join( StartDir, OneFile ) )
                  except (IOError, OSError):
                    pass
    if Options.Verbose:
      print

    if Options.CompareImages:
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
      # Print image hash list
      for OneHash, OneList in ImageHashes.iteritems():
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
