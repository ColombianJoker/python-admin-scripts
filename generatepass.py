#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GeneratePassword, copyright Ramon Barrios Lascar, 2012
# Changed 2025-05-16 Magic line from /usr/bin/python to /usr/bin/env python3
#                    from print to print()

from os import urandom
from optparse import OptionParser


charsets={ "a":"abcdefghijklmnopqrstuvwxyz", "A":"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0":"0123456789", "!":"~!@#$%^&*()_+`-={}[]|\\:;\"'<>?/,." }

def GeneratePassword(length=5,charset="aA0"):
	password="";lc="";charset_string=""
	for c in charset:
		if c in charsets.keys():
			charset_string+=charsets[c]
	while len(password)<length:
		c=str(urandom(1))
		if c in charset_string and c!=lc:
			password+=c;lc=c
	return password

if __name__=="__main__":

  parser = OptionParser()
  parser.add_option("-s", "--charset", dest="CharsetString", action="store", type="string", help="Charset string, from aA0!", default="aA")
  parser.add_option("-l", "--length", dest="PasswordLength", action="store", type="int", help="Password length", default=16)
  parser.add_option("-v", "--verbose", dest="Verbose", action="store_true", help="Show banner", default=False)
  (Opts, Args) = parser.parse_args()
  Opts.PrgName = "GeneratePassword"
  
  if (Opts.Verbose):
    print( "%s: %s [%s,\"%s\"]" % (Opts.PrgName, GeneratePassword(Opts.PasswordLength,Opts.CharsetString), Opts.PasswordLength, Opts.CharsetString))
  else:
    print( "%s" % (GeneratePassword(Opts.PasswordLength,Opts.CharsetString),))
