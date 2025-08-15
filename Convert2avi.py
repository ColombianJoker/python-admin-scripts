#!/usr/bin/python
# encoding: utf-8
"""
Conver2avi.py: Convert muxed video files to proper .avi files with FFmpeg

Created by Ramón Barrios Lascar on 2008-02-20.
Copyright (c) 2008 iKnow. All rights reserved.
"""

import sys, os
from optparse import OptionParser

def ExtractVideo(File, Opts):
  if not Opts.OutputFile:
    FileDirname = os.path.dirname(File)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(File))
    Opts.VideoFile = os.path.join(FileDirname, FileBasename + "_temp.avi")
  else:
    FileDirname = os.path.dirname(Opts.OutputFile)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(Opts.OutputFile))
    Opts.VideoFile = os.path.join(FileDirname, FileBasename + "_temp.avi")
  try:
    os.remove( Opts.VideoFile )
  except:
    pass
  VideoExtractCommand = "mencoder -quiet \"%s\" -nosound -ovc lavc -lavcopts vcodec=mpeg4 -o \"%s\" 2>&1" % ( File, Opts.VideoFile )
  try:
    p = os.popen( VideoExtractCommand, "r" )
    subprocessOutput = p.readlines()
  # DEBUG
  # sys.stderr.write("%s.ExtractVideo(\"%s\")= \"%s\"\n" % (Opts.PrgName, File, Opts. VideoFile))
  except:
    Opts.VideoFile = False
  return Opts.VideoFile
  
def ExtractAudio(File, Opts):
  if not Opts.OutputFile:
    FileDirname = os.path.dirname(File)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(File))
    Opts.AudioFile = os.path.join(FileDirname, FileBasename + "_temp.wav")
  else:
    FileDirname = os.path.dirname(Opts.OutputFile)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(Opts.OutputFile))
    Opts.AudioFile = os.path.join(FileDirname, FileBasename + "_temp.wav")
  try:
    os.remove( Opts.AudioFile )
  except:
    pass
  AudioExtractCommand = "mplayer -quiet -vo null -ao pcm:file=\"%s\" \"%s\" >/dev/null 2>&1" % ( Opts.AudioFile, File )
  try:
    p = os.popen( AudioExtractCommand, "r" )
    subprocessOutput = p.readlines()
  # DEBUG
  # sys.stderr.write("%s.ExtractVideo(\"%s\")= \"%s\"\n" % (Opts.PrgName, File, Opts. VideoFile))
  except:
    Opts.AudioFile = False
  return Opts.AudioFile

def CombineMediaFiles( File, Video, Audio, Opts ):
  if not Opts.OutputFile:
    FileDirname = os.path.dirname(File)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(File))
    Opts.MediaFile = os.path.join(FileDirname, FileBasename + ".avi")
  else:
    FileDirname = os.path.dirname(Opts.OutputFile)
    FileBasename, FileExtname = os.path.splitext(os.path.basename(Opts.OutputFile))
    Opts.MediaFile = os.path.join(FileDirname, FileBasename + ".avi")
  try:
    os.remove( Opts.MediaFile )
  except:
    pass
  MediaCombineCommand = "ffmpeg -v 0 -i \"%s\" -i \"%s\" -map 0.0 -map 1.0 \"%s\" >/dev/null 2>/dev/null" % ( Video, Audio, Opts.MediaFile )
  try:
    p = os.popen( MediaCombineCommand, "r" )
    subprocessOutput = p.readlines()
  except:
    Opts.MediaFile = False
  try:
    os.remove( Video )
    os.remove( Audio )
  except:
    pass
  return Opts.MediaFile

# Start of main()  
parser = OptionParser()
parser.add_option("-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option("-o", "--output", dest="OutputFile", action="store", help="Filename of AVI file to create")
(Options, Args)= parser.parse_args()

Options.PrgName = os.path.basename(sys.argv[0])
returnCode = 0

if Options.OutputFile and len(Args) > 1:
  sys.stderr.write("%s: syntax error, when NOT using only one input file must NOT use OUTPUT_FILE!\n" % (Options.PrgName,))
  sys.exit(2)
  
if len(Args) == 0:
  sys.stderr.write("%s: syntax error, at least ONE file must be given\n" % (Options.PrgName,))
  sys.exit(2)

for OneArg in Args:
  if os.path.isfile(OneArg):
    ExtractedVideoFile = ExtractVideo(OneArg, Options)
    if not ExtractedVideoFile or not os.path.isfile(ExtractedVideoFile):
      sys.stderr.write("%s: could not extract video file from \"%s\"!\n" % (Options.PrgName, OneArg))
      returnCode = 3
    else:
      if not os.path.getsize(ExtractedVideoFile) > 0:
        sys.stderr.write("%s: a null file was generated extracting video from \"%s\"!\n" % (Options.PrgName, OneArg))
        returnCode = 4
      else:
        ExtractedAudioFile = ExtractAudio(OneArg, Options)
        if not ExtractedAudioFile:
          sys.stderr.write("%s: could not extract audio file from \"%s\"!\n" % (Options.PrgName, OneArg))
          returnCode = 5
        else:
          if not os.path.getsize(ExtractedAudioFile) > 0:
            sys.stderr.write("%s: a null file was generated extracting audio from \"%s\"!\n" % (Options.PrgName, OneArg))
            returnCode = 6
          else:
            FinalAviFile = CombineMediaFiles(OneArg, ExtractedVideoFile, ExtractedAudioFile, Options)
            if not FinalAviFile:
              sys.stderr.write("%s: could not combine audio and video from \"%s\"!\n" % (Options.PrgName, OneArg))
              returnCode = 7
            else:
              if not os.path.getsize(FinalAviFile) > 0:
                sys.stderr.write("%s: a null file eas generated combining audio and video into \"%s\"!\n" % (Options.PrgName, FinalAviFile))
                returnCode = 8
              
                