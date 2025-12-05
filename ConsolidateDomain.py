#!/usr/bin/python
# encoding: utf-8
"""
ConsolidateDomain.py: Manage FQDN lists to consolidated by-domain lists

Created by Ramón Barrios Lascar on 2007-03-20.
Copyright (c) 2007 iKnow. All rights reserved.
"""

import sys
import os
import string
from optparse import OptionParser

def PutInList( AList, Opts, OneName ):
    # Appends an item in the domain list
    SplitName = OneName.split( "." )
    print SplitName
    ReverseDomainUnjoined = SplitName.reverse()
    print ReverseDomainUnjoined
    ReverseDomain = string.join( ReverseDomainUnjoined, "." )
    if Alist.has_key( ReverseDomain ):
        print( "%s is in list" % ReverseDomain )
    else:
        print( "%s added to list" % ReverseDomain )
    # End of PutInList

def ProcessFile( Domains, Opts, Filename ):
    """Consolidates domains read from file into a memory hash"""

    if os.path.getsize( Filename ):
            # Process only sizeable files
            OpenFile = open( Filename )
            Opts.Count = Opts.Count + 1
            for OneLine in OpenFile:
                OneLine = OneLine.strip()
                if OneLine.find( "." ) > 1:
                    # The text line is not a top level domain
                    PutInList( Domains, Opts, OneLine )
            OpenFile.close()
    # End of ProcessFile()

def ConsolidateList( AList, Options ):
    """Leaves only an item"""
    # End of ConsolidateList

def DumpList( MasterList, Options ):
    """Generates a presentation of list"""
    # End of DumpList

parser = OptionParser()
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-o", "--output", dest="OutputFile", action="store", help="Output file" )

(Options, Args) = parser.parse_args()
# Initialize file count
Options.Count = 0
Options.PrgName = "same"
MasterList = {}
DomainList = {}

if len( Args ) > 0 :
    # Start only if files given!
    for OneArg in Args:
        if os.path.isfile( OneArg ):
        MasterList = ProcessFile( MasterList, Options, OneArg )
    DomainList = ConsolidateList( MasterList, Options )
    DumpList( MasterList, Options )
else:
    sys.stderr.write( "%s: too few arguments!\n" % Options.PrgName )
