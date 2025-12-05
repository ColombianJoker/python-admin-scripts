#!/usr/bin/python
# GetWWW-savvybabes.com.py

import sys, os
from optparse import OptionParser

def GetPhotoFile(URL, File, Options):
  if Options.Verbose:
    sys.stderr.write("  %s\n" % (File,))
  if Options.DEBUG:
    sys.stderr.write("  %s\n" % (URL,))
    
  if File:
    w = os.popen("wget -nv -O " + File + " " + URL)
  else:
    w = os.popen("wget -nv " + URL)
  wgetoutput = w.readlines()
  if Options.DEBUG:
    for line in wgetoutput:
      sys.stderr.write( "%s\n" % (line,))
  w.close()
  if os.path.isfile(File):
    if not Options.Verbose and not Options.DEBUG:
      sys.stdout.write(".")
    return True
  else:
    if not Options.DEBUG:
      sys.stdout.write("!")
    return False
  return False
  
def GetNextUrl(Slide, Options):
  Slide = Slide - 1
  if Slide == 0:
    Slide = 12
    Set = Set - 1
    if Set==0:
      Set = 3
      Month = Month - 1
      if Month == 0:
        Month = 12
        Year = Year - 1
  sMonth = "0%s" % (Month,)
  sMonth = sMonth[-2:]
  sSlide = "0%s" % (Slide)
  sSlide = sSlide[-2:]
  URI = "http://girls.twistys.net/preview/totm/%s-%s/000%s/%s.jpg" % (sMonth, Year, Set, sSlide)
  if Options.DEBUG:
    sys.stderr.write( "%s.GetNextUrl(%s,%s,%s,%s) => %s\n"  % (Options.PrgName, Year, Month, Set, Slide, URI))
  return Year, Month, Set, Slide, URI
  
# Start of main()  
parser = OptionParser()
parser.add_option("-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option("-D", "--DEBUG", dest="DEBUG", action="store_true", default=False, help="Filename of AVI file to create")
(Options, Args)= parser.parse_args()
Options.PrgName = "GetWWW"

FailedCounter = 0

aYear, aMonth, aSet, aSlide, aURI = GetNextUrl( 2006, 7, 3, 13, Options )
while True:
  OutputName = "GirlsTwistysNet-%s-%s-%s-%s.jpg" % (aYear, aMonth, aSet, aSlide)
  if Options.DEBUG:
    sys.stderr.write( "OutputName => %s\n" % (OutputName,))
  GetResult = GetPhotoFile(aURI, OutputName, Options)
  if not GetResult:
    # If could not get file, increase counter
    FailedCounter = FailedCounter + 1
  else:
    # If could get file, reset counter
    FailedCounter = 0
  if FailedCounter >= 3:
    break
  # Calculate next URL
  aYear, aMonth, aSet, aSlide, aURI = GetNextUrl(aYear, aMonth, aSet, aSlide, Options)
  