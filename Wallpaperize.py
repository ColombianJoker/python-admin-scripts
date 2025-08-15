#!/usr/bin/env python3
# encoding: utf-8
"""
Wallpaperize creates wallpapers with screen dimensions from JPG images
Created by Ramón Barrios Láscar on 2015/03/18
Last mod by Ramón Barrios Láscar on 2015/03/18
Copyright (c) 2015 Ínodo. All rights reserved
"""
import sys, os, subprocess,logging, logging.handlers
#import sys, os, platform, inspect, subprocess, time, random, re, logging, logging.handlers
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn():
  if Opts.DEBUG:
    Opts.Log.debug(" * %s"%(inspect.stack()[1][3]),)

def SetLogging():
  if Opts.DoLog:
    Opts.Log=logging.getLogger('INODO')
    if Opts.DEBUG:
      Opts.Log.setLevel(logging.DEBUG)
    elif Opts.Verbose:
      Opts.Log.setLevel(logging.INFO)
    else:
      Opts.Log.setLevel(logging.WARNING)
    LogHandler=logging.handlers.TimedRotatingFileHandler(Opts.LogFile,'Midnight',1,backupCount=30)
    ScreenHandler=logging.StreamHandler()
    LogFormatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s',datefmt='%Y/%m/%d %H:%M:%S')
    ScreenFormatter=logging.Formatter('%(levelname)s %(message)s')
    LogHandler.setFormatter(LogFormatter)
    ScreenHandler.setFormatter(ScreenFormatter)
    Opts.Log.addHandler(LogHandler)
    Opts.Log.addHandler(ScreenHandler)
    return Opts.Log

def GetDimensions(ImageName):
  """Return image size tuple"""
  IMCommand=[Opts.IdentifyCommand, ImageName]
  Opts.Log.debug(" ** IMCommand=%s"%(IMCommand,))
  try:
    IMLines=""
    ImageWidth=0
    ImageHeight=0
    IMLines=subprocess.check_output(IMCommand,shell=False)
    IMLines=IMLines.decode('utf-8')
    Opts.Log.debug(" >>> GetDimensions <<< ------------------------")
    Opts.Log.debug(str(IMLines.splitlines()[0]))
    Opts.Log.debug(" >>> GetDimensions <<< ------------------------")
    if len(IMLines)>0 and len(IMLines.splitlines())>0:
      IMLine=IMLines.splitlines()[0]
      if len(IMLine)>0 and len(IMLine.split())>0:
        DimensionText=IMLines.split()[len(IMLines.split())-7]
        ImageWidth=int(DimensionText.split("x")[0])
        ImageHeight=int(DimensionText.split("x")[1])
        Opts.Log.debug("Dimensions=%dx%d"%(ImageWidth,ImageHeight))
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  return ImageWidth,ImageHeight

def ConvertImage(Background,NewWidth,NewHeight,ResizeWidth,ResizeHeight,InputFile,OutputFile):
  """ConvertImage force converts one image using ImageMagick "convert" """
  IMCommand=[Opts.ConvertCommand]
  IMCommand.extend(["-background","%s"%(Background,)])
  IMCommand.extend(["-extent","%dx%d+0+0"%(NewWidth,NewHeight)])
  IMCommand.extend(["%s"%(os.path.expanduser(InputFile),)])
  IMCommand.extend(["-resize","%dx%d+0+0"%(ResizeWidth,ResizeHeight)])
  IMCommand.extend(["%s"%(os.path.expanduser(OutputFile),)])
  Opts.Log.debug(" ** IMCommand=%s"%(IMCommand,))
  try:
    IMLines=""
    IMLines=subprocess.check_output(IMCommand,shell=False)
    IMLines=IMLines.decode('utf-8')
    Opts.Log.debug(" >>> ConvertImage <<< ------------------------")
    Opts.Log.debug(str(IMLines))
    Opts.Log.debug(" >>> ConvertImage <<< ------------------------")
    if len(IMLines)>0:
      Opts.Log.debug(str(IMLines))
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  return True

def ProcessImage(ImageName):
  """Process/convert one image"""
  SourceDir,BaseName=os.path.split(ImageName)
  BaseFile,Extension=os.path.splitext(BaseName)
  Opts.Log.debug("%s %s %s"%(SourceDir,BaseFile,Extension))
  ImageWidth,ImageHeight=GetDimensions(ImageName)
  ImageProp=1.00*ImageWidth/ImageHeight
  if len(Opts.DestDir)>0:
    OutputWallpaper=os.path.join(Opts.DestDir,BaseFile+Opts.Suffix+Opts.Ext)
  else:
    OutputWallpaper=os.path.join(BaseFile+Opts.Suffix+Opts.Ext)
  if (ImageProp!=Opts.SProp) or Opts.Force:
    if ImageProp>Opts.SProp:
      TargetWidth=ImageWidth
      TargetHeight=Opts.Correction*ImageWidth/Opts.SProp
      Opts.Log.debug("X=%d Y=%d W=%d *H=%d"%(ImageWidth,ImageHeight,TargetWidth,TargetHeight))
    else:
      TargetHeight=ImageHeight
      TargetWidth=ImageHeight*Opts.SProp/Opts.Correction
      Opts.Log.debug("X=%d Y=%d *W=%d H=%d"%(ImageWidth,ImageHeight,TargetWidth,TargetHeight))
    Opts.Log.debug("ImageProp=%0.3f SProp=%0.3f W=%d H=%d"%(ImageProp, Opts.SProp, TargetWidth,TargetHeight,))
    ConvertImage(Background=Opts.Background,NewWidth=TargetWidth,NewHeight=TargetHeight,ResizeWidth=Opts.Width,ResizeHeight=Opts.Height,InputFile=ImageName,OutputFile=OutputWallpaper)
  return True

# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"

try:
  parser=OptionParser(usage="%prog [ --OPTIONS ]",conflict_handler="resolve")
  parser.add_option("-q", "--quiet", dest="Verbose", action="store_false", default=True, help="Quiet mode. Don't show messages")
  parser.add_option("-b", "--background", dest="Background", action="store", type="string", default="black", help="Background color")
  parser.add_option("-d", "--destination-dir", dest="DestDir", action="store", type="string", help="Target directory to copy to", default="~/Pictures/Wallpapers")
  parser.add_option("-w", "-x", "--width", dest="Width", action="store", type="int", help="Image width in pixels", default=1440)
  parser.add_option("-h", "-y", "--height", dest="Height", action="store", type="int", help="Image height in pixels", default=900)
  parser.add_option("-f", "--force", dest="Force", action="store_true", default=False, help="Force convert")
  parser.add_option("-s", "--suffix", dest="Suffix", action="store", type="string", default="_adj", help="Selects file suffix")
  parser.add_option("-m", "--move", dest="MoveOriginal", action="store_true", default=False, help="Move originals")
  parser.add_option("-i", "--image-format", "--format", dest="ImageFormat", action="store", type="string", default="JPG", help="Selects image type/format")
  parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--no-log", dest="DoLog", action="store_false", help="No log to a file", default=True)
  parser.add_option("-o", "--output", dest="LogFile", action="store", type="string", help="Log execution into file name", default="%s.log"%(PrgName,))
  parser.add_option("--identify-command", dest="IdentifyCommand", action="store", type="string", default="identify", help=SUPPRESS_HELP)
  parser.add_option("--convert-command", dest="ConvertCommand", action="store", type="string", default="convert", help=SUPPRESS_HELP)
  
  (Opts, Args)=parser.parse_args()
  Opts.PrgName=PrgName
  Opts.Correction=100.0
  Opts.SProp=Opts.Correction*Opts.Width/Opts.Height
  Opts.Raise=True
  Opts.Ext="."
  Opts.ImageFormat=Opts.ImageFormat.upper()

  Log=SetLogging()

  if Opts.ImageFormat=="JPG":
    Opts.Ext+="jpg"
  elif Opts.ImageFormat=="PNG":
    Opts.Ext+="png"
  elif Opts.ImageFormat=="TIFF":
    Opts.Ext+="tiff"
  else:
    logging.error("%s: Unknown image format specification (%s)!\n"%(Opts.PrgName,Opts.ImageFormat))
    sys.stderr.write("%s: Unknown image format specification (%s)!\n"%(Opts.PrgName,Opts.ImageFormat))
    sys.exit(1)

  # Do forever
  if len(Args)>0:
  #The End
    for ImageName in Args:
      Opts.Log.info(ImageName)
      ProcessImage(os.path.expanduser(ImageName))
  else:
    Log.critical("no file arguments given!")
  # sys.exit(0)

except KeyboardInterrupt:
  logging.info("%s: Process cancelled (keyboard interrupt)!"%(Opts.PrgName,))
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n"%(Opts.PrgName,))
  sys.stderr.flush()
except IOError:
  logging.error("%s: IO Error changing directory to %s!"%(Opts.PrgName,Opts.WorkDir))
  sys.stderr.write("\n%s: IO Error changing directory to %s!\n"%(Opts.PrgName,Opts.WorkDir))
  sys.stderr.flush()
except SyntaxError:
  logging.error("%s: Syntax error compiling/running!"%(Opts.PrgName,))
  sys.stderr.write("\n%s: Syntax error compiling/running!\n"%(Opts.PrgName,))
  sys.stderr.flush()
except SystemExit as e:
  if e!=0:
    sys.stderr.write("%s: exit.\n"%(PrgName,))
  sys.exit(e)
  
# --------------------------------------------------------------------------------
# Ramon Barrios Lascar, 2015, Ínodo S.A.S.
# --------------------------------------------------------------------------------
