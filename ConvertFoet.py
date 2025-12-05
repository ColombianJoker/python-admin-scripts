#!/usr/bin/python

import os
import string
import sys
from datetime import date, datetime, time, timedelta
from optparse import OptionParser


def LoadFoet(Opts, List):
    OpenFile = open(os.path.expanduser(Opts.InputFile), "r")
    for Line in OpenFile.readlines():
        List.append(string.strip(Line))


def DumpFoet(Opts, List):
    OpenFile = open(os.path.expanduser(Opts.OutputFile), "w")
    OpenFile.writelines([ListLine + os.linesep for ListLine in List])
    OpenFile.close()


def ConvertLine(Opts, List):
    for Line in List:
        Column = Line.split()
        Hour1, Min1, Sec1 = Column[4].split(":")
        StartTime = datetime.strptime(Column[4], "%H:%M:%S")
        StartTime = StartTime - Opts.TimeDelta
        Column[4] = StartTime.strftime("%H:%M:%S")


# MAIN
if __name__ == "__main__":
    parser = OptionParser()

    (Options, Args) = parser.parse_args()
    Options.InputFile, Options.OutputFile = Args

    Options.TimeDelta = timedelta(hours=5, minutes=14, seconds=1)
    InputList = []
    OutputList = []
    # Load File
    OpenFile = open(os.path.expanduser(Options.InputFile), "r")
    for Line in OpenFile.readlines():
        InputList.append(string.strip(Line))

    # Convert
    for Line in InputList:
        Column = Line.split()
        Hour1, Min1, Sec1 = Column[4].split(":")
        StartTime = datetime.strptime(Column[4], "%H:%M:%S")
        StartTime = StartTime - Options.TimeDelta
        NewColumn = StartTime.strftime("%H:%M:%S")
        Sec3 = long(float(Column[12]) * 0.7)
        EndTime = StartTime + timedelta(seconds=Sec3)
        FinalColumn = EndTime.strftime("%H:%M:%S")
        print(
            "%s > %s | %s > %s | %s > %s"
            % (Column[4], NewColumn, Column[8], FinalColumn, Column[12], Sec3)
        )
        # OutputList.append( [ Column[:3], [NewColumn], Column[5:6], [FinalColumn], Column[9:10], [Sec3] , Column[13:] ])
        OutputList.append(
            [
                Column[:4],
                [NewColumn],
                [" * Final   * "],
                [FinalColumn],
                Column[9:12],
                ["      " + str(Sec3)],
                Column[13:],
            ]
        )

    # Save File
    OpenFile = open(os.path.expanduser(Options.OutputFile), "w")
    for ListLine in OutputList:
        ReducedLine = " ".join(reduce(lambda x, y: x + y, ListLine))
        OpenFile.writelines(ReducedLine + os.linesep)
    OpenFile.close()
