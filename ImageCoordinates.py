#!/usr/bin/env python

import pyexiv2
import getopt
import sys
from fractions import Fraction
from functools import partial

usage = """Usage: coordinate [options] [files]

Options:
  -g filename       photo file with GPS coordinates
  -n ddd:mm:ss.ss   north coordinate
  -s ddd:mm:ss.ss   south coordinate
  -e ddd:mm:ss.ss   east coordinate
  -w ddd:mm:ss.ss   west coordinate
  -h                show this help message

Add location metadata to each of the listed files. The location
can come from either the photo associated with the -g option or
with a -n, -s, -e, -w pair given on the command line."""

# Functions for manipulating coordinates.
def makecoord(coordstring):
  """Make a coordinate list from a coordinate string.

  The string is of the form ddd:mm:ss.ss and the list comprises
  three Fractions."""

  angle = coordstring.split(':', 2)
  loc = [ Fraction(x).limit_denominator(1000) for x in angle ]
  return loc

def setcoord(metadata, direction, coordinate):
  """Set the latitude or longitude coordinate.

  Latitude is set if direction is 'N' or 'S', longitude if 'E' or 'W'.
  The coordinate is a list of the form [dd, mm, ss], where the degrees,
  minutes, and seconds are Fractions."""

  tags = {'lat': ('Exif.GPSInfo.GPSLatitudeRef', 'Exif.GPSInfo.GPSLatitude'),
          'lon': ('Exif.GPSInfo.GPSLongitudeRef', 'Exif.GPSInfo.GPSLongitude')}
  if direction in ('N', 'S'):
    coord = 'lat'
  else:
    coord = 'lon'
  metadata[tags[coord][0]] = direction
  metadata[tags[coord][1]] = coordinate


# Get the command line options.
try:
  options, filenames = getopt.getopt(sys.argv[1:], 'g:n:s:e:w:h')
except getopt.GetoptError, err:
  print str(err)
  sys.exit(2)

# Set the option values.
gpsphoto = north = south = east = west = False       # defaults
for o, a in options:
  if o == '-g':
    gpsphoto = a
  elif o == '-n':
    north = makecoord(a)
  elif o == '-s':
    south = makecoord(a)
  elif o == '-e':
    east = makecoord(a)
  elif o == '-w':
    west = makecoord(a)
  else:
    print usage
    sys.exit()

# Valid option combinations.
ne = (north and east) and not (south or west or gpsphoto)
nw = (north and west) and not (south or east or gpsphoto)
se = (south and east) and not (north or west or gpsphoto)
sw = (south and west) and not (north or east or gpsphoto)
gps = gpsphoto and not (north or south or east or west)

if not (ne or nw or se or sw or gps):
  print "invalid location"
  sys.exit()


# Create the coordinate setter functions.
if ne:
  setlat = partial(setcoord, direction='N', coordinate=north)
  setlon = partial(setcoord, direction='E', coordinate=east)
elif nw:
  setlat = partial(setcoord, direction='N', coordinate=north)
  setlon = partial(setcoord, direction='W', coordinate=west)
elif se:
  setlat = partial(setcoord, direction='S', coordinate=south)
  setlon = partial(setcoord, direction='E', coordinate=east)
elif sw:
  setlat = partial(setcoord, direction='S', coordinate=south)
  setlon = partial(setcoord, direction='W', coordinate=west)
elif gps:
  basemd = pyexiv2.ImageMetadata(gpsphoto)
  basemd.read()
  latref = basemd['Exif.GPSInfo.GPSLatitudeRef']
  lat = basemd['Exif.GPSInfo.GPSLatitude']
  lonref = basemd['Exif.GPSInfo.GPSLongitudeRef']
  lon = basemd['Exif.GPSInfo.GPSLongitude']
  setlat = partial(setcoord, direction=latref.value, coordinate=lat.value)
  setlon = partial(setcoord, direction=lonref.value, coordinate=lon.value)
else:
  print "coordinate setter failed"
  sys.exit()

# Cycle through the files.
for f in filenames:
  md = pyexiv2.ImageMetadata(f)
  md.read()
  setlat(md)
  setlon(md)
  md.write()