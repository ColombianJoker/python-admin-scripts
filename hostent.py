#!/usr/bin/env python2
# encoding: utf-8
"""
hostent.py: Manage /etc/hosts entries

Created by Ramón Barrios Lascar on 2007-02-20.
Copyright (c) 2007 iKnow. All rights reserved.
"""

import sys
import os
import string
import re
from optparse import OptionParser


def LoadHosts(Opts):
    OpenFile = open(os.path.expanduser(Opts.FileName), "r")
    for Line in OpenFile.readlines():
        Opts.HostsList.append(string.strip(Line))
    # close( OpenFile )


def ExtractNames(HostSpec):
    # HostSpec = re.escape( HostSpec )
    Matched = False
    NewName = ""
    NewFullName = ""
    NewAddress = ""
    HostSpecMatch = re.compile("([a-zA-Z][a-zA-Z0-9_-]*)=((?:[0-9]{1,3}\.){3}[0-9]{1,3})").match(HostSpec)
    HostFullSpecMatch = re.compile("([a-zA-Z][a-zA-Z0-9_-]*),([a-zA-Z][a-zA-Z0-9_-]*)=((?:[0-9]{1,3}\.){3}[0-9]{1,3})").match(HostSpec)
    if HostSpecMatch:
        NewName = HostSpecMatch.group(1)
        NewFullName = ""
        NewAddress = HostSpecMatch.group(2)
    elif HostFullSpecMatch:
        NewName = HostFullSpecMatch.group(1)
        NewFullName = HostFullSpecMatch.group(2)
        NewAddress = HostFullSpecMatch.group(3)
    else:
        return None
    return NewName, NewFullName, NewAddress


def SearchHost(Opts, Host):
    HostFound = False
    HostPattern = re.compile("\\b%s\\b" % (Host,))
    for Line in Opts.HostsList:
        if HostPattern.search(Line):
            HostFound = True
            if Opts.SearchAndPrint:
                print Line
            if Opts.ReturnLine:
                ReturnLine = Line
            break
    if Opts.SearchAndPrint is not None and not HostFound:
        sys.stderr.write("%s: \\\"%s\\\" host not found!\\n" % (Opts.PrgName, Host))
    if Opts.ReturnLine is not None:
        return ReturnLine
    else:
        return HostFound


def SearchAddress(Opts, Address):
    AddressFound = False
    Address = re.escape(Address)
    AddressPattern = re.compile("^\\b%s\\b" % (Address,))
    for Line in Opts.HostsList:
        if AddressPattern.search(Line):
            AddressFound = True
            break
    return AddressFound


def DumpHosts(Opts):
    for Line in Opts.HostsList:
        print Line
    return True


def ListHost(Opts, Host):
    Opts.SearchAndPrint = True
    HostFound = SearchHost(Opts, Host)
    Opts.SearchAndPrint = False
    return HostFound


def IsDisabled(Opts, Host):
    Host = re.escape(Host)
    if SearchHost(Opts, Host):
        Opts.ReturnLine = True
        Line = SearchHost(Opts, Host)
        Opts.ReturnLine = False
        HostPattern = re.compile("^#")
        if HostPattern.search(Line):
            return True   # Host line is disabled
        else:
            return False  # Host line is not disabled


def IsEnabled(Opts, Host):
    return not IsDisabled(Opts, Host)


def DisableHost(Opts, Host):
    Host = re.escape(Host)
    if SearchHost(Opts, Host):
        if IsEnabled(Opts, Host):
            # The host is in the host table and enabled
            HostFound = False
            HostPattern = re.compile("\\b%s\\b" % (Host,))
            for Line in Opts.HostsList:
                if HostPattern.search(Line):
                    HostFound = True
                    # Get host position in host table
                    HostIndex = Opts.HostsList.index(Line)
                    # Set new host line
                    Opts.HostsList[HostIndex] = "# %s\\t## DISABLED ##" % (Line,)
                    if Opts.Verbose:
                        sys.stderr.write("%s: \\\'%s\\\' host disabled.\\n" % (Opts.PrgName, Host))
        else:
            sys.stderr.write("%s: \\\"%s\\\" host is not enabled!\\n" % (Opts.PrgName, Host))
            return False
        return True
    else:
        # Host not found
        sys.stderr.write("%s: \\\"%s\\\" host not found!\\n" % (Opts.PrgName, Host))
        return False


def EnableHost(Opts, Host):
    if SearchHost(Opts, Host):
        if IsDisabled(Opts, Host):
            # The host is in the host table and disabled
            HostFound = False
            HostPattern = re.compile("\\b%s\\b" % (Host,))
            for Line in Opts.HostsList:
                if HostPattern.search(Line):
                    HostFound = True
                    # Get host position in host table
                    HostIndex = Opts.HostsList.index(Line)
                    # Set new host line
                    NewLine = ""
                    NewList = []
                    if Opts.Verbose:
                        print Line
                    LineMatch = re.compile("[# ]*((?:[0-9]{1,3}\.){3}[0-9]{1,3})[ \\t]+([a-zA-Z0-9._]+)(?:[ \\t]+([a-zA-Z0-9._]+))*[ \\t]## DISABLED ##[ \\t]*").match(Line)
                    if LineMatch:
                        for Item in LineMatch.groups():
                            if Opts.Verbose:
                                print "\\\'%s\\\'" % (Item,)
                            if Item is not None:
                                try:
                                    ItemIndex = NewList.index(Item)
                                    if Opts.Verbose:
                                        sys.stderr.write("%s: \\\'%s\\\' is index %d in \\\'%s\\\'\\n" % (Opts.PrgName, Item, ItemIndex, Line))
                                except:
                                    NewLine = "%s\\t%s" % (NewLine, Item)
                                    NewList.append(Item)
                                    sys.stderr.write("%s: \\\'%s\\\' appended.\\n" % (Opts.PrgName, Item))
                        NewLine = re.sub("^\\t", "", NewLine)
                        if Line != NewLine:
                            Opts.HostsList[HostIndex] = NewLine
                            if Opts.Verbose:
                                sys.stderr.write("%s: \\\'%s\\\' host enabled.\\n" % (Opts.PrgName, Host))
                            return True
                        return False
                    else:
                        sys.stderr.write("%s: Line does not match!\\n" % (Opts.PrgName,))
                        return False
                    break
        else:
            sys.stderr.write("%s: \\\"%s\\\" host is not disabled!\\n" % (Opts.PrgName, Host))
            return False
        return True
    else:
        # Host not found
        sys.stderr.write("%s: \\\"%s\\\" host not found!\\n" % (Opts.PrgName, Host))
        return False


def AddHost(Opts, HostSpec):
    Matched = True
    try:
        NewName, NewFullName, NewAddress = ExtractNames(HostSpec)
    except:
        Matched = False
    if not Matched:
        sys.stderr.write("%s: invalid host specification! (%s)\\n" % (Opts.PrgName, HostSpec))
        return False
    else:
        if SearchHost(Opts, NewName):
            sys.stderr.write("%s: \\\'%s\\\' host was found on hosts table, and was not added!\\n" % (Opts.PrgName, NewName))
        elif (NewFullName != "") and SearchHost(Opts, NewFullName):
            sys.stderr.write("%s: \\\'%s\\\' host was found on host table, and was not added!\\n" % (Opts.PrgName, NewFullName))
        elif SearchAddress(Opts, NewAddress):
            sys.stderr.write("%s: \\\'%s\\\' address was found on hosts table, and was not added!\\n" % (Opts.PrgName, NewAddress))
        else:
            if NewFullName != "":
                Opts.HostsList.append("%s\\t%s\\t%s" % (NewAddress, NewFullName, NewName))
            else:
                Opts.HostsList.append("%s\\t%s" % (NewAddress, NewName))
            if Opts.Verbose:
                sys.stderr.write("%s: \\\'%s\\\' host added\\n" % (Opts.PrgName, NewName))
            return True


def RemoveHost(Opts, Host):
    Matched = False
    if SearchHost(Opts, Host):
        HostPattern = re.compile("\\b(%s)[ \\t]*$|\\b(%s)[ \\t]" % (Host, Host))
        for Line in Opts.HostsList:
            if HostPattern.search(Line):
                Opts.HostsList.remove(Line)
                if Opts.Verbose:
                    sys.stderr.write("%s: host \\\'%s\\\' found and deleted.\\n" % (Opts.PrgName, Host))
                return True
                break
        sys.stderr.write("%s: host \\\'%s\\\' not found!\\n" % (Opts.PrgName, Host))
        return False
    else:
        sys.stderr.write("%s: host \\\'%s\\\' not found!\\n" % (Opts.PrgName, Host))
        return False


def UnconditionalAddHost(Opts, HostSpec):
    Matched = True
    try:
        NewName, NewFullName, NewAddress = ExtractNames(HostSpec)
    except:
        Matched = False
    if not Matched:
        sys.stderr.write("%s: invalid host specification! (%s)\\n" % (Opts.PrgName, HostSpec))
        return False
    else:
        if SearchHost(Opts, NewName):
            # The host was found
            if Opts.Verbose:
                sys.stderr.write("%s: \\\'%s\\\' host found!\\n" % (Opts.PrgName, NewName))
            HostFound = False
            HostPattern = re.compile("\\b%s\\b" % (NewName,))
            for Line in Opts.HostsList:
                if HostPattern.search(Line):
                    if Opts.Verbose:
                        sys.stderr.write("%s: \\\'%s\\\' host found!\\n" % (Opts.PrgName, NewName))
                    LineMatch = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3})[ \\t]+(?:()[a-zA-Z0-9._-]+)[ \\t]+)*(#+ *.*)?").match(Line)
                    if LineMatch:
                        if Opts.Verbose:
                            sys.stderr.write("%s: Standard liine matched.\\n" % (Opts.PrgName,))
                        NewLine = ""
                        Groups = len(LineMatch.groups())
                        for ItemNumber in range(1, Groups):
                            if LineMatch.group(ItemNumber) is None:
                                continue
                            NewLine = "%s\\t%s" % (NewLine, LineMatch.group(ItemNumber))
                        NewLine = re.sub("^\\t", "", NewLine)
                        NewLine = "%s\\t%s\\%s" % (NewLine, NewName, LineMatch.group(Groups))
                        Opts.HostsList[Opts.HostsList.index(Line)] = NewLine
#            print "Old Line: \\\'%s\\\'" % ( Line, )
#            print "New Line: \\\'%s\\\'" % ( NewLine, )
                    else:
                        sys.stderr.write("%s: Standard line NOT matched!\\n" % (Opts.PrgName,))
            return True
        elif SearchAddress(Opts, NewAddress):
            # The address was found
            AddressFound = False
            AddressPattern = re.compile("\\b%s\\b" % (NewAddress,))
            for Line in Opts.HostsList:
                if AddressPattern.search(Line):
                    LineMatch = re.compile("^((?:[0-9]{1,3}\.){3}[0-9]{1,3})[ \\t]+(?:([a-zA-Z0-9._-]+)[ \\t]+)(?:([a-zA-Z0-9._-]+)[ \\t]*)?").search(Line)
                    if LineMatch:
                        NewLine = ""
                        Groups = len(LineMatch.groups())
                        for ItemNumber in range(1, Groups + 1):
                            if LineMatch.group(ItemNumber) is not None:
                                NewLine = "%s\\t%s" % (NewLine, LineMatch.group(ItemNumber))
                        NewLine = re.sub("^\\t", "", NewLine)
                        if NewFullName is not None and NewFullName != "":
                            NewLine = "%s\\t%s" % (NewLine, NewFullName)
                        NewLine = "%s\\t%s" % (NewLine, NewName)
                        Opts.HostsList[Opts.HostsList.index(Line)] = NewLine
                        if Opts.Verbose:
                            if NewFullName is not None and NewFullName != "":
                                sys.stderr.write("%s: \\\'%s\\\' and \\\'%s\\\' added to \\\'%s\\\' address.\\n" % (Opts.PrgName, NewName, NewFullName, NewAddress))
                            else:
                                sys.stderr.write("%s: \\\'%s\\\' added to \\\'%s\\\' address.\\n" % (Opts.PrgName, NewName, NewAddress))
                    else:
                        sys.stderr.write("%s: Standard line NOT matched!\\n" % (Opts.PrgName,))
            return True
        else:
            return AddHost(Options, HostSpec)


def UnconditionalRemoveHost(Opts, Host):
    Matched = True
    if SearchHost(Opts, Host):
        Host = re.escape(Host)
        HostFound = False
        HostPattern = re.compile("\\b%s\\b" % (Host,))
        for Line in Opts.HostsList:
            if HostPattern.search(Line):
                AddressMatch = re.compile("^((?:[0-9]{1,3}\.){3}[0-9]{1,3})[ \\t]+").search(Line).group(1)
                NamesMatch = re.compile("^(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})[ \\t]+(.*)").search(Line).group(1)
                NewLine = re.sub("\\b%s[ \\t]*$|\\b%s(?:[ \\t])" % (Host, Host), "", Line, 1)
                NewLine = re.sub("[ \\t]+$", "", NewLine)
                if Line != NewLine:
                    Opts.HostsList[Opts.HostsList.index(Line)] = NewLine
                    if Opts.Verbose:
                        sys.stderr.write("%s: host \\\'%s\\\' deleted!\\n" % (Opts.PrgName, AddressMatch,))
                    return True
                else:
                    return False
                break
        sys.stderr.write("%s: host \\\'%s\\\' not found!\\n" % (Opts.PrgName, Host))
        return False
    else:
        sys.stderr.write("%s: host \\\'%s\\\' not found!\\n" % (Opts.PrgName, Host))
        return False


def SaveHosts(Opts):
    if os.name == "posix":
        import posix
        HostsFile = "/etc/hosts"
        if Opts.OutputFile is None:
            Opts.OutputFile = Opts.FileName[:]
        if Opts.OutputFile == HostsFile:
            if posix.getuid() != 0:
                sys.stderr.write("%s: To process \\\'%s\\\' file in POSIX systems you must be \\\'root\\\' user!\\n" % (Opts.PrgName, HostsFile))
                sys.exit(3)
        OpenHosts = open(os.path.expanduser(Opts.OutputFile), "w")
        OpenHosts.writelines([HostLine + os.linesep for HostLine in Opts.HostsList])
        OpenHosts.close()
        if Opts.Verbose:
            sys.stderr.write("%s: \\\'%s\\\' file saved.\\n" % (Opts.PrgName, Opts.OutputFile))
        return True


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
    parser.add_option("-f", "--file", dest="FileName", action="store", help="File to process", default="/etc/hosts", metavar="FILE")
    parser.add_option("-a", "--add", "--append", dest="AddAddress", action="store", help="Add a host pair (hostname=address)", metavar="HOSTPAIR")
    parser.add_option("-x", "--delete", "--remove", dest="RemoveAddress", action="store", help="Remove a host", metavar="HOST")
    parser.add_option("-e", "--enable", "--activate", dest="EnableAddress", action="store", help="Enable a disabled host", metavar="HOST")
    parser.add_option("-d", "--disable", "--deactivate", dest="DisableAddress", action="store", help="Disable a enabled host", metavar="HOST")
    parser.add_option("-l", "--list", "--show", dest="ListHost", action="store", help="List a host", metavar="HOST")
    parser.add_option("-o", "--output", dest="OutputFile", action="store", help="Save to new file", metavar="FILE")
    parser.add_option("-A", "--unconditional-add", dest="UncAddAddress", action="store", help="Add a hostname to an address", metavar="HOSTPAIR")
    parser.add_option("-X", "--unconditional-delete", dest="UncRemoveAddress", action="store", help="Remove a hostname from an address", metavar="HOST")

    (Options, Args) = parser.parse_args()
    Options.PrgName = "hostent"
    Options.FileChanged = False
    Options.SearchAndPrint = None
    Options.ReturnLine = None
    Options.HostsList = []

    LoadHosts(Options)
    if Options.ListHost is not None:
        ReturnCode = ListHost(Options, Options.ListHost)
    elif Options.AddAddress is not None:
        ReturnCode = AddHost(Options, Options.AddAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    elif Options.RemoveAddress is not None:
        ReturnCode = RemoveHost(Options, Options.RemoveAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    elif Options.DisableAddress is not None:
        ReturnCode = DisableHost(Options, Options.DisableAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    elif Options.EnableAddress is not None:
        ReturnCode = EnableHost(Options, Options.EnableAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    elif Options.UncAddAddress is not None:
        ReturnCode = UnconditionalAddHost(Options, Options.UncAddAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    elif Options.UncRemoveAddress is not None:
        ReturnCode = UnconditionalRemoveHost(Options, Options.UncRemoveAddress)
        if ReturnCode == True:
            SaveHosts(Options)
    else:
        DumpHosts(Options)
        ReturnCode = 0

    if ReturnCode == False:
        ReturnCode = 1
    else:
        ReturnCode = 0
    sys.exit(ReturnCode)
