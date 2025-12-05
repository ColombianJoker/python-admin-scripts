#!/usr/bin/python
# encoding: utf-8
"""
SshHost.py: Tool to manage host signatures in ~/.ssh/known_hosts

Created by Ramón Barrios Lascar on 2006-11-17.
Copyright (c) 2007 iKnow. All rights reserved.
"""

import os
import string
import sys
from optparse import OptionParser


def LoadSshHosts(Opts, TheList):
    """Load the file in the master list"""
    if Opts.DEBUG:
        sys.stderr.write("*DEBUG* Into LoadSshHosts(%s,%s)\n" % (Opts, TheList))
    OpenFile = open(os.path.expanduser(Opts.HostsFile))
    for TextLine in OpenFile.readlines():
        #    if Opts.DEBUG:
        #      sys.stderr.write("  *DEBUG LoadSshHosts* TextLine=%s\n" % (TextLine,))
        KnownHost, SshEncription, SshFingerprint = TextLine.split(None, 2)
        RealHost = KnownHost.split(",")
        TheList[RealHost[0]] = "%s %s %s" % (KnownHost, SshEncription, SshFingerprint)
    if Opts.DEBUG:
        sys.stderr.write("  *DEBUG LoadSshHosts* TheList=%s\n" % (TheList.keys(),))
    # Return


def ListHosts(Opts, TheList):
    """List hosts in known_hosts file"""
    if Opts.DEBUG:
        sys.stderr.write("*DEBUG* Into ListHosts(%s,%s)\n" % (Opts, TheList))
    LoadSshHosts(Opts, TheList)
    if Opts.OutputFile:
        if Opts.Verbose:
            sys.stderr.write(
                '%s: creating "%s" ...\n' % (Opts.PrgName, Opts.OutputFile)
            )
        OutputFile = open(os.path.expanduser(Opts.OutputFile), "w")
    for i, Item in enumerate(TheList):
        if Opts.OutputFile:
            OutputFile.write(TheList[Item])
        else:
            if Opts.Verbose:
                sys.stdout.write("%d %s\n" % (i, TheList[Item]))
            else:
                sys.stdout.write("%d - %s\n" % (i, Item))
    # Return


def DisableHost(Opts, TheList):
    """Disable a host prepending a # to it"""
    LoadSshHosts(Opts, TheList)
    if Opts.OutputFile:
        if Opts.Verbose:
            sys.stderr.write(
                '%s: creating "%s" ...\n' % (Opts.PrgName, Opts.OutputFile)
            )
        OutputFile = open(os.path.expanduser(Opts.OutputFile), "w")
    for i, Item in enumerate(TheList):
        if Opts.Verbose:
            sys.stderr.write("  %s\n" % (Item,))
        if Opts.DisableHost == Item:
            sys.stderr.write("  %s is disabled.\n" % (Item,))
            if Opts.OutputFile:
                OutputFile.write("# %s" % (TheList[Item],))
        else:
            if Opts.OutputFile:
                OutputFile.write("%s" % (TheList[Item],))
    if Opts.OutputFile:
        OutputFile.close()


def EnableHost(Opts, TheList):
    """Enable a disabled host removing the # prepended in the line"""
    if Opts.OutputFile:
        if Opts.Verbose:
            sys.stderr.write(
                '%s: creating "%s" ...\n' % (Opts.PrgName, Opts.OutputFile)
            )
        OutputFile = open(os.path.expanduser(Opts.OutputFile), "w")
    for i, Item in enumerate(TheList):
        if Opts.Verbose:
            sys.stderr.write("  %s\n" % (Item,))
        if ("# " + Opts.DisableHost) == Item:
            sys.stderr.write("  %s is enabled.\n" % (Item,))
            if Opts.OutputFile:
                OutputFile.write("# %s" % (TheList[Item][2:],))
        else:
            if Opts.OutputFile:
                OutputFile.write("%s" % (TheList[Item],))
    if Opts.OutputFile:
        OutputFile.close()


def DeleteHost(Opts, TheList):
    """Disable a host prepending a # to it"""
    LoadSshHosts(Opts, TheList)
    if Opts.OutputFile:
        if Opts.Verbose:
            sys.stderr.write(
                '%s: creating "%s" ...\n' % (Opts.PrgName, Opts.OutputFile)
            )
        OutputFile = open(os.path.expanduser(Opts.OutputFile), "w")
    for i, Item in enumerate(TheList):
        if Opts.DeleteHost != Item:
            if Opts.OutputFile:
                OutputFile.write(TheList[Item])
            elif Opts.Verbose:
                sys.stdout.write(TheList[Item])
        elif not Opts.Verbose:
            sys.stderr.write("%s: %s deleted\n" % (Opts.PrgName, Item))
        elif Opts.Verbose and Opts.OutputFile:
            sys.stderr.write("%s: %s deleted\n" % (Opts.PrgName, Item))


def ShowHost(Opts, TheList):
    """Show information for a host"""
    LoadSshHosts(Opts, TheList)
    for i, Item in enumerate(TheList):
        if Opts.ShowHost == Item:
            sys.stdout.write(TheList[Item])
            break
    else:
        sys.stderr.write('%s: host "%s" not found!\n' % (Opts.PrgName, Opts.ShowHost))


parser = OptionParser()
parser.add_option(
    "-v",
    "--verbose",
    dest="Verbose",
    action="store_true",
    help="Verbose mode",
    default=False,
)
parser.add_option(
    "-f",
    "--file",
    dest="HostsFile",
    action="store",
    help="SSH known hosts file",
    default="~/.ssh/known_hosts",
)
parser.add_option(
    "-d", "--disable", dest="DisableHost", action="store", help="Disable a host"
)
parser.add_option(
    "-e", "--enable", dest="EnableHost", action="store", help="Enable a host"
)
parser.add_option(
    "-x", "--delete", dest="DeleteHost", action="store", help="Delete a host"
)
parser.add_option(
    "-s", "--show", dest="ShowHost", action="store", help="Show information for a host"
)
parser.add_option(
    "-o",
    "--output",
    dest="OutputFile",
    action="store",
    help="Output file for processed known_hosts",
)
parser.add_option(
    "-O",
    "--default-output",
    dest="DefaultOutput",
    action="store_true",
    help="Use default .ssh/known_hosts",
    default=False,
)
parser.add_option(
    "-S",
    "--search",
    dest="SearchFor",
    action="store",
    help="Search and show information for hosts",
)
parser.add_option(
    "--DEBUG", dest="DEBUG", action="store_true", help=False, default=False
)

(Options, Args) = parser.parse_args()
# Initialize file count
Options.Count = 0
Options.PrgName = "SshHosts"
MasterList = {}

if Options.DefaultOutput:
    Options.OutputFile = os.path.expanduser("~/.ssh/known_hosts")

if Options.DEBUG:
    sys.stderr.write(
        "*DEBUG* %s: Options.OutPutFile=%s\n" % (Options.PrgName, Options.OutputFile)
    )

if Options.DisableHost:
    DisableHost(Options, MasterList)
elif Options.EnableHost:
    EnableHost(Options, MasterList)
elif Options.DeleteHost:
    DeleteHost(Options, MasterList)
elif Options.ShowHost:
    ShowHost(Options, MasterList)
elif Options.SearchFor:
    SearchFor(Options, MasterList)
else:
    ListHosts(Options, MasterList)
