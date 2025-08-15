#!/usr/bin/python
# encoding: utf-8
# Gets or sets EXIF comments of image files

import os
import sys
import re
from optparse import OptionParser

def GetFromImage(Opts, ImageFile):
  """Gets and shows EXIF image comments for file"""
  CommandLine = Opts.Identify + " -verbose '" + ImageFile + "'"
  if Opts.DEBUG:
    sys.stderr.write(CommandLine + "\n")
  chp = os.popen(CommandLine,"r")
  CommandLines = chp.readlines()
  chp.close()
  if Opts.DEBUG:
    sys.stderr.write( "%s  got %d lines from %s\n" % (Opts.PrgName,len(CommandLines),CommandLine))
  for CommandLineOutput in CommandLines:
    CommentMatch = Opts.CommentRe.match( CommandLineOutput )
    if CommentMatch:
      if Opts.DEBUG:
        sys.stderr.write("  match!\n")
      # SpecialMatch = Opts.SpecialRe.match( CommentMatch.group(1))
      # if SpecialMatch:
      #   if Opts.DEBUG:
      #     sys.stderr.write("  special match\n")
      #   sys.stdout.write(Opts.FormatString % (SpecialMatch.group(1), SpecialMatch.group(2) + " : " + SpecialMatch.group(3)))
      # else:
      sys.stdout.write(Opts.FormatString % (ImageFile, CommentMatch.group(1)))
      ReturnCode = False
    else:
      if Opts.Verbose:
        sys.stderr.write("%s: Could not get comment for %s\n" % (Opts.PrgName, ImageFile))
      if not Opts.Verbose and Opts.DEBUG:
        sys.stderr.write(" not match!\n")
      ReturnCode = False

def SetIntoImage(Opts, ImageFile):
  """Puts EXIF comments into a file"""
  try:
    CommandLine = Opts.Mogrify + " -comment '" + Opts.Set + "' '" + ImageFile + "'"
    if Opts.DEBUG:
      sys.stderr.write(CommandLine + "\n")
    chp = os.popen(CommandLine,"r")
    CommandLines = chp.readline()
    chp.close()
    CommandLine = "chmod a-x '" + ImageFile + "'"
    chp = os.popen(CommandLine,"r")
    chp.close()
  except:
    sys.stderr.write("%s: Problem writing into \"%s\"!\n" % (Opts.PrgName,ImageFile))
  if Opts.MoveFile:
    try:
      if not os.path.isdir("Done"):
        if Opts.DEBUG:
          sys.stderr.write("mkdir Done ...")
        chp = os.popen("mkdir Done","r")
        if Opts.DEBUG:
          sys.stderr.write(" done!\n")
        chp.close()
      CommandLine = Opts.Move + " '" + ImageFile + "' Done"
      chp = os.popen(CommandLine,"r")
      if Opts.DEBUG:
        sys.stderr.write(CommandLine + "\n")
      chp.close()
    except:
      if Opts.Verbose:
        sys.stderr.write("%s: Could not move \"%s\" to Done!\n" % (Opts.PrgName,ImageFile))
  return True

if __name__ == "__main__" :
  parser = OptionParser()
  parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False )
  parser.add_option( "-g", "--get", dest="Get", action="store_true", help="Get comment from file", default=True )
  parser.add_option( "-s", "--set", dest="Set", action="store", help="Store comment in file", default=False )
  parser.add_option( "-m", "--move", dest="MoveFile", action="store_true", help="Move files to \"Done\" directory", default=False )
  parser.add_option( "--DEBUG", dest="DEBUG", action="store_true", default=False)
  ( Options, Args ) = parser.parse_args()
  Options.PrgName = "ImageComment"
  if Options.Set and Options.Get:
    Options.Get = False
  Options.FormatString = "%s : %s\n"

  Options.CommentRe = re.compile("^    [Cc]omment: (.*)")
  Options.SpecialRe = re.compile("(.*) : (.*) : (.*)")
  Options.Mogrify = "/opt/local/bin/mogrify"
  Options.Identify = "/opt/local/bin/identify"
  Options.Move = "/usr/bin/mv"
  
  # Now process the files
  for OneArg in Args:
    if os.path.isfile(OneArg):
      if Options.Get:
        ResultCode = GetFromImage(Options, OneArg)
      if Options.Set:
        ResultCode = SetIntoImage(Options, OneArg)
    else:
      sys.stderr.write("%s: file \"%s\" not found!\n" %( Options.PrgName, OneArg))