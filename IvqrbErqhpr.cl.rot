#!/usr/bin/python
# encoding: utf-8
"""
VideoReduce.py: Convert a video to a .mp4 reduced version suitable for cell phone playing

Created by Ramón Barrios Lascar on 2007-08-20.
Copyright (c) 2007 iKnow. All rights reserved.
"""

import sys
import os
from optparse import OptionParser

def getBaseName(File):
  """getBaseName returns the simple name of video file without an extension or path"""
  return os.path.splitext(os.path.basename(File))[0]

def getDirName(File):
  """getDirName returns the dirname of file"""
  return os.path.dirname(File)

def extractVideo(Opts, File):
  """extractVideo extract a video-only file from a muxed audio-videofile
  using MPlayer-mencoder"""
  Opts.TempOutputVideo = Opts.TempDir+"/"+getBaseName(File)+".avi"
  CommandLine = Opts.mEncoder+" "+Opts.mEncoderFmt%(File, Opts.TempOutputVideo)
  if Opts.Debug:
    sys.stderr.write("%s\n"%(CommandLine,))
  p = os.popen(CommandLine, "r")
  if p:
    suppressOutput = p.readlines()
  p.close()
  if Opts.Debug:
    for lineItem in suppressOutput:
      sys.stderr.write(lineItem+"\n")
  if os.path.isfile(Opts.TempOutputVideo) and os.path.getsize(Opts.TempOutputVideo)>0:
    returnCode = True
  else:
    returnCode = False
    if os.path.isfile(Opts.TempOutputVideo):
      os.unlink(Opts.TempOutputVideo)
  return returnCode

def extractAudio(Opts, File):
  """extractAudio extract a audio-only file from a muxed audio-videofile
  using MPlayer-mplayer"""
  Opts.TempOutputAudio = Opts.TempDir+"/"+getBaseName(File)+".wav"
  CommandLine = Opts.mPlayer+" "+Opts.mPlayerFmt%(Opts.TempOutputAudio, File)
  if Opts.Debug:
    sys.stderr.write("%s\n"%(CommandLine,))
  p = os.popen(CommandLine, "r")
  if p:
    suppressOutput = p.readlines()
  p.close()
  if Opts.Debug:
    for lineItem in suppressOutput:
      sys.stderr.write(lineItem+"\n")
  if os.path.isfile(Opts.TempOutputAudio) and os.path.getsize(Opts.TempOutputAudio)>0:
    returnCode = True
  else:
    returnCode = False
    if os.unlink(Opts.TempOutputAudio):
      os.unlink(Opts.TempOutputAudio)
  return returnCode

def mediaCombine(Opts, File):
  """mediaCombine renders an media file with audio and video using ffmpeg"""
  returnCode = False
  if len(getDirName(File))>0:
    Opts.FinalVideo = getDirName(File)+"/"+getBaseName(File)+Opts.OutputExtension
  else:
    Opts.FinalVideo = getBaseName(File)+Opts.OutputExtension
  if os.path.isfile(Opts.TempOutputVideo) and os.path.getsize(Opts.TempOutputVideo)>0 and os.path.isfile(Opts.TempOutputAudio) and os.path.getsize(Opts.TempOutputAudio)>0:
    CommandLine = Opts.ffMpeg+" "+Opts.ffMpegFmt%(Opts.TempOutputVideo, Opts.TempOutputAudio, Opts.FinalVideo)
    if Opts.Debug:
      sys.stderr.write("%s\n"%(CommandLine,))
    p = os.popen(CommandLine, "r")
    if p:
      suppressOutput = p.readlines()
    p.close()
    if Opts.Debug:
      for lineItem in suppressOutput:
        sys.stderr.write(lineItem+"\n")
    if os.path.isfile(Opts.FinalVideo) and os.path.getsize(Opts.FinalVideo):
      returnCode = True
    else:
      returnCode = False
      os.unlink(Opts.FinalVideo)
  return returnCode

def processOneMediaFile(Opts, File):
  """processOneMediaFile extracts audio and video from one file and recombines them
  using mplayer and ffmpeg"""
  
  returnCode = True
  # Extract video stream from file
  if not extractVideo(Opts,File):
    sys.stderr.write("%s: Could not get video from '%s'!\n"%(Opts.PrgName, File))
    returnCode = False
  else:
    if Opts.Verbose:
      sys.stdout.write("%s: Video extracted from '%s'.\n"%(Opts.PrgName,File))
    
    # Extract audio stream from file
    if not extractAudio(Opts,File):
      sys.stderr.write("%s: Could not get audio from '%s'!\n"%(Opts.PrgName, File))
      returnCode = False
    else:
      if Opts.Verbose:
        sys.stdout.write("%s: Audio extracted from '%s'.\n"%(Opts.PrgName,File))
      
      # Combine/render media file
      if not mediaCombine(Opts,File):
        sys.stderr.write("%s: Could not recombine audio and video into \"%s\"!\n"%(Opts.PrgName,Opts.FinalVideo))
        returnCode = False
      else:
        if Opts.Verbose:
          sys.stdout.write("%s: Media file recombined into \"%s\".\n"%(Opts.PrgName,Opts.FinalVideo))
  return returnCode

def main():
  pass
  parser = OptionParser()
  parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False )
  parser.add_option( "-T", "--tempdir", dest="TempDir", action="store", help="Temporary work directory", default="/tmp" )
  parser.add_option( "-D", "--debug", dest="Debug", action="store_true", help="Debug mode", default=False )
  parser.add_option( "-E", "--ext", "--extension", dest="OutputExtension", action="store", default=".avi", help="Default extension of created video files")
  parser.add_option( "-n", "--nokia", dest="NokiaSize", action="store_true", default=False, help="Create a small Nokia sized video")
  (Options, Args) = parser.parse_args()
  Options.PrgName = "VideoReduce"
  Options.mEncoder = "mencoder"
  Options.mPlayer = "mplayer"
  Options.ffMpeg = "ffmpeg"
  if Options.NokiaSize:
    Options.mEncoderFmt = "\"%s\" -nosound -ovc lavc -lavcopts vcodec=mpeg4 -vop expand=176:144,scale=176:-2 -ofps 15  -o \"%s\""
                        # First input file, Second output file
    Options.mPlayerFmt = "-vo null -ao pcm:file=\"%s\" -af resample=8000,volume=+4db:sc \"%s\""
                        # First output file, Second input file
    Options.ffMpegFmt = "-i \"%s\" -i \"%s\" -b 48 -ac 1 -ab 12 -map 0.0 -map 1.0 \"%s\""
                        # First video input, Second audio input, Third output
  else:
    Options.mEncoderFmt = "\"%s\" -nosound -ovc lavc -lavcopts vcodec=mpeg4 -vop expand=480:320,scale=480:-2 -ofps 30  -o \"%s\""
                        # First input file, Second output file
    Options.mPlayerFmt = "-vo null -ao pcm:file=\"%s\" -af resample=16000,volume=+4db:sc \"%s\""
                        # First output file, Second input file
    Options.ffMpegFmt = "-i \"%s\" -i \"%s\" -b 48 -ac 1 -ab 12 -map 0.0 -map 1.0 \"%s\""
                        # First video input, Second audio input, Third output
  if Options.OutputExtension[0] != ".":
    Options.OutputExtension = "." + Options.OutputExtension
  Options.CountSuccessful = 0
  Options.CountProcessed = 0
  
  if len(Args) > 0:
    for OneFile in Args:
      if os.path.isfile(OneFile):
        if processOneMediaFile(Options,OneFile):
          Options.CountProcessed = Options.CountProcessed+1
          Options.CountSuccessful = Options.CountSuccessful+1
        else:
          Options.CountProcessed = Options.CountProcessed+1
      else:
        sys.stderr.write("%s: \"%s\" is not a known file!\n"%(Options.PrgName,OneFile))

if __name__ == '__main__':
  main()

