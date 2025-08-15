#!/usr/bin/python

import os, sys, urllib

def TextDecrypt( cText ):
  key = 6L
  actual = ""
  #actual = actual  + "0=" + cText[0] + " ult=" + cText[ len( cText )-1 ]
  for i in range( 0, len( cText ) ):
    actual = actual + chr( key ^ ord( cText[i] ) )
  return actual
    
for FileArgument in sys.argv[1:]:
  OpenFile = open( FileArgument )
  TextLine = []
  for FileLine in OpenFile.readlines():
    TextLine.append( TextDecrypt( urllib.unquote( FileLine ) ) )
    print TextLine
  OpenFile.close()
