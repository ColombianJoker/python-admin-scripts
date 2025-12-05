#!/usr/bin/env python3.11
# encoding: utf-8
"""
ZaiTrack: Helps with tracking packages in ZaiCargo

Created by Ramón Barrios Lascar on 2019-05-24.
Copyright (c) 2020 Ínodo S.A.S. All rights reserved.
Changed: 2023-04-15, python3.11
"""

import os
import sqlite3
import string
import sys
from datetime import date
from optparse import SUPPRESS_HELP, OptionParser


def DeletePackage(Opts):
    """Deletes some packages given the ids"""

    SQLcx = sqlite3.connect(Opts.DB)
    SQLcurs = SQLcx.cursor()
    SQLcurd = SQLcx.cursor()
    import re

    for OneArg in Args:
        m = re.search("^[0-9]{4}(/?[0-9]{2}){2}$", OneArg)
        if m:  # matches
            SQLselect = "SELECT * FROM ZaiCargoTrack WHERE pkgdate=='%s'" % (
                OneArg.replace("/", ""),
            )
        else:
            SQLselect = "SELECT * FROM ZaiCargoTrack WHERE id LIKE '%%%s%%'" % (OneArg,)
        if Opts.DEBUG:
            sys.stderr.write("%s: search using [%s]\n" % (Opts.PrgName, SQLselect))
        for SQLrow in SQLcurs.execute(SQLselect):
            SQLdelete = "DELETE FROM ZaiCargoTrack WHERE id=='%s'" % (SQLrow[0],)
            if Opts.DEBUG:
                sys.stderr.write("%s: using [%s]\n" % (Opts.PrgName, SQLdelete))
            try:
                SQLcurd.execute(SQLdelete)
                sys.stdout.write(
                    "%s: package '%s' deleted!\n" % (Opts.PrgName, SQLrow[0])
                )
            except sqlite3.IntegrityError:
                sys.stderr.write(
                    "%s: error deleting with [%s]\n" % (Opts.PrgName, SQLdelete)
                )
    SQLcx.commit()
    SQLcx.close()
    return True


def ListPackages(Opts):
    """List ZaiCargo full queue on debug, unchecked queue normally"""
    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    if Opts.DEBUG:
        SQLsentence = "SELECT * FROM ZaiCargoTrack;"
    else:
        SQLsentence = "SELECT * FROM ZaiCargoTrack WHERE NOT CHECKED;"
    SQLfmt = "%-11s\t%-4s/%2s/%2s\n"
    SQLfmtd = "%-11s\t%-4s/%2s/%2s%s\n"
    Empty = True
    for SQLrow in SQLcur.execute(SQLsentence):
        if Opts.DEBUG:
            sys.stdout.write(
                SQLfmtd
                % (
                    SQLrow[0],
                    SQLrow[1][0:4],
                    SQLrow[1][4:6],
                    SQLrow[1][6:8],
                    "\tchecked" if SQLrow[2] == 1 else "",
                )
            )
        else:
            sys.stdout.write(
                SQLfmt % (SQLrow[0], SQLrow[1][0:4], SQLrow[1][4:6], SQLrow[1][6:8])
            )
        Empty = False
    if Empty:
        sys.stderr.write(
            "%s: the ZaiCargo table list result was empty.\n" % (Opts.PrgName,)
        )
    SQLcx.commit()
    SQLcx.close()
    return True


def CheckPackages(Opts, Args):
    """Marks some packages 'checked' or 'unchecked'"""
    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    for OneArg in Args:
        if Opts.check:
            SQLsentence = (
                "UPDATE ZaiCargoTrack SET checked=1 WHERE id LIKE '%%%s%%';" % (OneArg,)
            )
        elif Opts.uncheck:
            SQLsentence = (
                "UPDATE ZaiCargoTrack SET checked=0 WHERE id LIKE '%%%s%%';" % (OneArg,)
            )
        if Opts.DEBUG:
            sys.stderr.write("%s: using [%s]\n" % (Opts.PrgName, SQLsentence))
        SQLcur.execute(SQLsentence)
    SQLcx.commit()
    SQLcx.close()
    return True


def CleanString(Text):
    """Clean string of straneous chars"""
    NoDict = {SP_Char: "" for SP_Char in Options.NoChars}
    NoDict[" "] = ""
    # if Options.DEBUG:
    #   sys.stderr.write("%s: Text='%s' NoChars='%s' NoDict='%s'\n"%(Options.PrgName,Text,Options.NoChars,NoDict,))
    NoTable = str.maketrans(NoDict)
    return Text.translate(NoTable)


def AddPackage(Opts, Args):
    """Add some packages, unchecked"""
    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    Checked = 0
    RC = True
    SQLsentence = "INSERT INTO ZaiCargoTrack VALUES('%s','%s',%d)" % (
        Opts.add,
        CleanString(Opts.pkgdate),
        Checked,
    )
    if Opts.DEBUG:
        sys.stderr.write(
            "%s: using [%s]\n"
            % (
                Opts.PrgName,
                SQLsentence,
            )
        )
    try:
        RC = SQLcur.execute(SQLsentence)
    except sqlite3.IntegrityError:
        sys.stderr.write(
            "%s: error inserting using '%s' package id! (may be exists?)\n"
            % (Opts.PrgName, Opts.add)
        )
    if len(Args) > 0:
        for OneArg in Args:
            SQLsentence = "INSERT INTO ZaiCargoTrack VALUES('%s','%s',%d)" % (
                OneArg,
                CleanString(Opts.pkgdate),
                Checked,
            )
            if Opts.DEBUG:
                sys.stderr.write(
                    "%s: using [%s]\n"
                    % (
                        Opts.PrgName,
                        SQLsentence,
                    )
                )
            try:
                RC = RC and SQLcur.execute(SQLsentence)
            except sqlite3.IntegrityError:
                sys.stderr.write(
                    "%s: error inserting using '%s' package id! (may be exists?)\n"
                    % (Opts.PrgName, OneArg)
                )
    SQLcx.commit()
    SQLcx.close()
    return RC


def SearchPackage(Opts):
    """Search package by ID or by date, and open a browser with the track id copied"""

    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    if Opts.DEBUG:
        strres = Opts.search.find("/")
        if strres > -1:
            # search includes "/"
            SQLsentence = "SELECT * FROM ZaiCargoTrack WHERE pkgdate=='%s';" % (
                Opts.search.replace("/", ""),
            )
            sys.stderr.write("%s: search using [%s]\n" % (Opts.PrgName, SQLsentence))
        else:
            strres = Opts.search.find("BOG")
            if strres == 0 and len(Opts.search) == 11:
                SQLsentence = "SELECT * FROM ZaiCargoTrack WHERE id=='%s';" % (
                    Opts.search,
                )
                sys.stderr.write(
                    "%s: search using [%s]\n" % (Opts.PrgName, SQLsentence)
                )
            else:
                SQLsentence = "SELECT * FROM ZaiCargoTrack WHERE id LIKE '%%%s%%';" % (
                    Opts.search,
                )
                sys.stderr.write(
                    "%s: search using [%s]\n" % (Opts.PrgName, SQLsentence)
                )
    else:
        strres = Opts.search.find("/")
        if strres > -1:
            # search includes "/"
            SQLsentence = (
                "SELECT * FROM ZaiCargoTrack WHERE pkgdate=='%s' AND NOT checked;"
                % (Opts.search.replace("/", ""),)
            )
        else:
            strres = Opts.search.find("BOG")
            if strres == 0 and len(Opts.search) == 11:
                SQLsentence = (
                    "SELECT * FROM ZaiCargoTrack WHERE id=='%s' AND NOT checked;"
                    % (Opts.search,)
                )
            else:
                SQLsentence = (
                    "SELECT * FROM ZaiCargoTrack WHERE id LIKE '%%%s%%' AND NOT checked;"
                    % (Opts.search,)
                )
    SQLfmt = "%-11s\t%-4s/%2s/%2s\n"
    LastRow = ""
    RowCount = 0
    for SQLrow in SQLcur.execute(SQLsentence):
        sys.stdout.write(
            SQLfmt % (SQLrow[0], SQLrow[1][0:4], SQLrow[1][4:6], SQLrow[1][6:8])
        )
        RowCount += 1
        LastRow = SQLrow[0]
    # else:
    #   if RowCount==0:
    #     sys.stderr.write("%s: '%s' not found in unchecked packages\n"%(Opts.PrgName,Opts.search))
    SQLcx.commit()
    SQLcx.close()
    Opts.RecordsFound = RowCount
    return LastRow


def ShowFirst(Opts):
    """Show first unchecked package only"""

    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    if Opts.DEBUG:
        SQLsentence = "SELECT id FROM ZaiCargoTrack ORDER BY id ASC LIMIT 1;"
    else:
        SQLsentence = (
            "SELECT id FROM ZaiCargoTrack WHERE checked==0 ORDER BY id ASC LIMIT 1;"
        )
    RC = True
    try:
        for SQLrow in SQLcur.execute(SQLsentence):
            sys.stdout.write("%s\n" % (SQLrow[0],))
    except sqlite3.Error as e:
        sys.stderr.write("%s: An error occurred: %s\n" % (Opts.PrgName, e.args[0]))
        RC = False
    SQLcx.commit()
    SQLcx.close()
    return RC


def ShowLast(Opts):
    """Show last unchecked package only"""

    SQLcx = sqlite3.connect(Opts.DB)
    SQLcur = SQLcx.cursor()
    if Opts.DEBUG:
        SQLsentence = "SELECT id FROM ZaiCargoTrack ORDER BY id DESC LIMIT 1;"
    else:
        SQLsentence = (
            "SELECT id FROM ZaiCargoTrack WHERE checked==0 ORDER BY id DESC LIMIT 1;"
        )
    RC = True
    try:
        for SQLrow in SQLcur.execute(SQLsentence):
            sys.stdout.write("%s\n" % (SQLrow[0],))
    except sqlite3.Error as e:
        sys.stderr.write("%s: An error occurred: %s\n" % (Opts.PrgName, e.args[0]))
        RC = False
    SQLcx.commit()
    SQLcx.close()
    return RC


def TogglePackages(Opts, Args):
    """Toggles checked status of packages"""

    import re

    SQLcx = sqlite3.connect(Opts.DB)
    SQLcurs = SQLcx.cursor()
    SQLcuru = SQLcx.cursor()
    for OneArg in Args:
        m = re.search("^[0-9]{4}(/?[0-9]{2}){2}$", OneArg)
        if m:  # matches
            SQLselect = "SELECT * FROM ZaiCargoTrack WHERE pkgdate=='%s'" % (
                OneArg.replace("/", ""),
            )
        else:
            SQLselect = "SELECT * FROM ZaiCargoTrack WHERE id LIKE '%%%s%%'" % (OneArg,)
        if Opts.DEBUG:
            sys.stderr.write("%s: search using [%s]\n" % (Opts.PrgName, SQLselect))
        for SQLrow in SQLcurs.execute(SQLselect):
            SQLupdate = "UPDATE ZaiCargoTrack SET checked=%d WHERE id=='%s';" % (
                0 if SQLrow[2] == 1 else 1,
                SQLrow[0],
            )
            if Opts.DEBUG:
                sys.stderr.write("%s: using [%s]\n" % (Opts.PrgName, SQLupdate))
            try:
                SQLcuru.execute(SQLupdate)
                sys.stdout.write(
                    "%s: package '%s' toggled to %s\n"
                    % (
                        Opts.PrgName,
                        SQLrow[0],
                        "checked" if SQLrow[2] == 1 else "unchecked",
                    )
                )
            except sqlite3.IntegrityError:
                sys.stderr.write(
                    "%s: error updating with [%s]\n" % (Opts.PrgName, SQLupdate)
                )
    SQLcx.commit()
    SQLcx.close()
    return True


# START OF MAIN FILE
ScriptFile = os.path.realpath(__file__)
PrgName = os.path.basename(os.path.splitext(ScriptFile)[0])
today = date.today()
pkgdate = today.strftime("%Y%m%d")

try:
    parser = OptionParser(
        usage="%prog [ -l ] [ [ -d DATE ] -a PKGID ... ] [ -x | -t | -c | -u  PKGID ... ] | -s TEXT ..."
    )
    parser.add_option(
        "-a",
        "--add",
        action="store",
        metavar="PKGID",
        help="Store new track id with ID",
    )
    parser.add_option(
        "-d",
        "--date",
        action="store",
        dest="pkgdate",
        help="Store with package date (defaults=today)",
    )
    parser.add_option(
        "-l",
        "--list",
        action="store_true",
        default=True,
        help="List all registered packages",
    )
    parser.add_option(
        "-s",
        "--search",
        metavar="TEXT",
        action="store",
        default=False,
        help="Search for registered package",
    )
    parser.add_option(
        "-x",
        "--delete",
        metavar="PKGID",
        action="store_true",
        default=False,
        help="Delete registered package",
    )
    parser.add_option(
        "-t",
        "--toggle",
        action="store_true",
        metavar="PKGID",
        default=False,
        help="Toggle registered packages",
    )
    parser.add_option(
        "-c",
        "--check",
        action="store_true",
        metavar="PKGID",
        default=False,
        help="Mark 'checked' some packages",
    )
    parser.add_option(
        "-u",
        "--uncheck",
        action="store_true",
        metavar="PKGID",
        default=False,
        help="Mark 'unchecked' some packages",
    )
    parser.add_option(
        "-U",
        "--FirstUnchecked",
        action="store_true",
        metavar="PKGID",
        default=False,
        help="Show first unchecked only",
    )
    parser.add_option(
        "-A",
        "--LastUnchecked",
        action="store_true",
        metavar="PKGID",
        default=False,
        help="Show last unchecked only",
    )
    parser.add_option(
        "--zaidb",
        dest="DB",
        action="store",
        default="~/Documents/Comercial/ZaiCargo.db",
        help=SUPPRESS_HELP,
    )
    parser.add_option(
        "--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP
    )

    (Options, Args) = parser.parse_args()
    Options.PrgName = PrgName
    Options.RecordsFound = 0
    Options.DB = os.path.expanduser(os.path.expandvars(Options.DB))
    Options.NoChars = ["/", ":", "-", "_", ".", "\\"]

    if Options.delete:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG DELETE '%s'\n" % (Options.PrgName, Options.delete)
            )
        DeletePackage(Options)
    elif Options.check:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG check '%s'\n" % (Options.PrgName, Options.check)
            )
        if len(Args) > 0:
            CheckPackages(Options, Args)
        else:
            sys.stderr.write(
                "%s: too few arguments (package ids), exiting...\n" % (Options.PrgName,)
            )
            sys.exit(2)
    elif Options.uncheck:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG uncheck '%s'\n" % (Options.PrgName, Options.uncheck)
            )
        if len(Args) > 0:
            CheckPackages(Options, Args)
        else:
            sys.stderr.write(
                "%s: too few arguments (package ids), exiting...\n" % (Options.PrgName,)
            )
            sys.exit(2)
    elif Options.add:
        if not Options.pkgdate:
            if Options.DEBUG:
                sys.stderr.write(
                    "%s: no date given, using today\n" % (Options.PrgName,)
                )
            Options.pkgdate = pkgdate
        if Options.DEBUG:
            sys.stderr.write("%s: DEBUG ADD '%s'\n" % (Options.PrgName, Options.add))
        AddPackage(Options, Args)
    elif Options.search:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG SEARCH '%s'\n" % (Options.PrgName, Options.search)
            )
        SearchResult = SearchPackage(Options)
        if Options.DEBUG:
            sys.stderr.write("%s: SearchResult=%s\n" % (Options.PrgName, SearchResult))
        if len(Args) > 0:
            for OneArg in Args:
                Options.search = OneArg
                SearchResult = SearchPackage(Options)
        if Options.RecordsFound > 0:
            import subprocess

            import pasteboard

            subprocess.call(
                ["open", "-a", "Safari", "http://www.zaicargo.com/"], shell=False
            )
            pasteboard.Pasteboard().set_contents(SearchResult)
        else:
            sys.stderr.write(
                "%s: '%s' unchecked packages not found!\n"
                % (Options.PrgName, Options.search)
            )
            sys.exit(1)
    elif Options.toggle:
        if len(Args) > 0:
            if Options.DEBUG:
                sys.stderr.write("%s: DEBUG TOGGLE '[%s]\n" % (Options.PrgName, Args))
            TogglePackages(Options, Args)
            sys.exit(0)
        else:
            sys.stderr.write(
                "%s: too few arguments given (no package ids!).\n" % (Options.PrgName,)
            )
            sys.exit(2)
    elif Options.FirstUnchecked:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG show first unchecked only\n" % (Options.PrgName,)
            )
        if len(Args) > 0:
            sys.stderr.write("%s: too many arguments [%s]\n" % (Options.PrgName, Args))
            sys.exit(2)
        else:
            ShowFirst(Options)
            sys.exit(0)
    elif Options.LastUnchecked:
        if Options.DEBUG:
            sys.stderr.write(
                "%s: DEBUG show last unchecked only\n" % (Options.PrgName,)
            )
        if len(Args) > 0:
            sys.stderr.write("%s: too many arguments [%s]\n" % (Options.PrgName, Args))
            sys.exit(2)
        else:
            ShowLast(Options)
            sys.exit(0)
    elif Options.list:
        if Options.DEBUG:
            sys.stderr.write("%s: DEBUG LIST\n" % (Options.PrgName,))
        ListPackages(Options)
        sys.exit(0)
except KeyboardInterrupt:
    sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
    sys.stderr.flush()

# CREATE TABLE ZaiCargoTrack(id varchar(12) not null, pkgdate char(8), checked integer not null, unique (id) on conflict fail);
