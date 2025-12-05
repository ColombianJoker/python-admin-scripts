#!/usr/bin/env python
# encoding: utf-8
"""
SshConfig manipulates .ssh/config and /etc/ssh/ssh_config files
"""
import sys, os, subprocess,logging, logging.handlers, itertools
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn():
    if Opts.DEBUG:
        Opts.Log.debug(" * %s"%(inspect.stack()[1][3]),)

def SetLogging():
    if Opts.DoLog:
        Opts.Log=logging.getLogger('INODO')
        if Opts.DEBUG:
            Opts.Log.setLevel(logging.DEBUG)
        elif Opts.Verbose:
            Opts.Log.setLevel(logging.INFO)
        else:
            Opts.Log.setLevel(logging.WARNING)
        LogHandler=logging.handlers.TimedRotatingFileHandler(Opts.LogFile,'Midnight',1,backupCount=30)
        ScreenHandler=logging.StreamHandler()
        LogFormatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s',datefmt='%Y/%m/%d %H:%M:%S')
        ScreenFormatter=logging.Formatter('%(levelname)s %(message)s')
        LogHandler.setFormatter(LogFormatter)
        ScreenHandler.setFormatter(ScreenFormatter)
        Opts.Log.addHandler(LogHandler)
        Opts.Log.addHandler(ScreenHandler)
        return Opts.Log

def ProcessFile(AFile):
    Data=open(AFile,"r").readlines()
    Records=(Lines for Valid,Lines in itertools.groupby(Data, lambda L : L != '\n') if Valid)
    try:
            Output = [tuple(Field.split('	')[1].strip() for Field in itertools.islice(Record, 1, None)) for Record in Records]
            print Output
    except IndexError:
            pass

# You can change output to generator by
# output = (tuple(field.split(':')[1].strip() for field in itertools.islice(record, 1, None)) for record in records)

# output = [('X', 'Y', '20'), ('H', 'F', '23'), ('S', 'Y', '13'), ('M', 'Z', '25')]
#You can iterate and change the order of elements in the way you want
# [(elem[1], elem[0], elem[2]) for elem in output] as required in your output  Records
# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"

try:
    parser=OptionParser(usage="%prog [ --OPTIONS ]",conflict_handler="resolve")
    parser.add_option("--verbose", "-v", dest="Verbose", action="store_true", default=False, help="Verbose mode")
    parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
    parser.add_option("--no-log", dest="DoLog", action="store_false", help="No log to a file", default=True)
    parser.add_option("-o", "--output", dest="LogFile", action="store", type="string", help="Log execution into file name", default="%s.log"%(PrgName,))

    (Opts, Args)=parser.parse_args()
    Opts.PrgName=PrgName

    Log=SetLogging()

    if len(Args)>0:
            for File in Opts.Args:
                if os.path.isfile(File):
                        File=os.path.realpath(File)
                        sys.stdout.write("%s: %s\n"%(PrgName,File))
                        ProcessFile(File)
    else:
            if os.path.isfile(os.path.expanduser("~/.ssh/config")):
                File=os.path.expanduser("~/.ssh/config")
                sys.stdout.write("%s: %s\n"%(PrgName,File))
                ProcessFile(File)

except KeyboardInterrupt:
    logging.info("%s: Process cancelled (keyboard interrupt)!"%(Opts.PrgName,))
    sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n"%(Opts.PrgName,))
    sys.stderr.flush()
except IOError:
    logging.error("%s: IO Error changing directory to %s!"%(Opts.PrgName,Opts.WorkDir))
    sys.stderr.write("\n%s: IO Error changing directory to %s!\n"%(Opts.PrgName,Opts.WorkDir))
    sys.stderr.flush()
except SyntaxError:
    logging.error("%s: Syntax error compiling/running!"%(Opts.PrgName,))
    sys.stderr.write("\n%s: Syntax error compiling/running!\n"%(Opts.PrgName,))
    sys.stderr.flush()
except SystemExit as e:
    if e!=0:
        sys.stderr.write("%s: exit.\n"%(PrgName,))
    sys.exit(e)

# --------------------------------------------------------------------------------
# Ramon Barrios Lascar, 2015, Ínodo S.A.S.
# --------------------------------------------------------------------------------
