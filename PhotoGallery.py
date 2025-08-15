#!/usr/bin/env python3
# encoding: utf-8
"""
PhotoGallery.py: processes photo download queue

Created by Ramón Barrios Lascar on 2017-07-12.
Copyright (c) 2017 Ínodo S.A.S. All rights reserved.
"""
import sys, os, string, sqlite3
from optparse import OptionParser, SUPPRESS_HELP

def ProcessQueue(Opts):
  return True

def ListQueue(Opts,Dw):
  """List the queue to process"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    if Opts.Filter:
      sys.stderr.write("%s: using filter \"URL LIKE '%%%s%%'\"\n"%(Opts.PrgName,Opts.Filter))
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  if Opts.Filter:
    SQLsentence="SELECT page, url FROM Queue WHERE downloaded==%d AND url LIKE '%%%s%%';"%(Dw,Opts.Filter)
  else:
    SQLsentence="SELECT page, url FROM Queue WHERE downloaded==%d;"%(Dw,)
  for SQLrow in SQLcur.execute(SQLsentence):
    SQLfmt="%%%ds\t%%s\n"%(Opts.Digits,)
    sys.stdout.write(SQLfmt%(SQLrow[0],SQLrow[1]))
  else:
    if not SQLrow:
      if Dw==0:
        Desc="queue"
      elif Dw==1:
        Desc="log"
      sys.stderr.write("%s: the %s is empty.\n"%(Desc,Opts.PrgName,))
    sys.stdout.flush()
  SQLcx.commit()
  SQLcx.close()

def ListFuture(Opts):
  """List the queue to process"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    if Opts.Filter:
      sys.stderr.write("%s: using filter \"URL LIKE '%%%s%%'\"\n"%(Opts.PrgName,Opts.Filter))
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  if Opts.Filter:
    SQLsentence="SELECT * FROM FuturePages WHERE url LIKE '%%%s%%';"%(Opts.Filter)
  else:
    SQLsentence="SELECT * FROM FuturePages;"
  for SQLrow in SQLcur.execute(SQLsentence):
    SQLfmt="%%%ds\t%%s\n"%(Opts.Digits,)
    sys.stdout.write(SQLfmt%(SQLrow[0],SQLrow[1]))
  else:
    try:
      SQLrow=SQLrow
    except UnboundLocalError:
      if Opts.Filter:
        sys.stderr.write("%s: nothing found in the FuturePages table with filter \"URL LIKE '%%%s%%'\"\n"%(Opts.PrgName,Opts.Filter))
      else:
        sys.stderr.write("%s: the FuturePages table is empty.\n"%(Opts.PrgName,))
    sys.stdout.flush()
  SQLcx.commit()
  SQLcx.close()

def OpenDir(Opts,Do):
  """Open or show temporary directory for images"""
  if Opts.DEBUG and Do:
    sys.stderr.write("%s: trying to open %s in the GUI\n"%(Opts.PrgName,Opts.Temp))
  if Do:
    import platform
    if platform.system()=="Darwin":
      # MacOS
      OpenCommand="open"
    elif platform.system()=="win32" or platform.system()=="win64":
      OpenCommand="start"
    os.system(OpenCommand+" "+Opts.Temp)
  else:
    sys.stdout.write(Opts.Temp+"\n")
  
def EnableURL(Opts):
  """Enable items in the queue"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.Enable='%s'\n"%(Opts.PrgName,Opts.Enable))
  try:
    EnableInt=int(Opts.Enable)
  except ValueError:
    EnableInt=0
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  if EnableInt>0:
    SQLsentence="SELECT COUNT(*) FROM Queue WHERE page==%d;"%(EnableInt,)
  else:
    SQLsentence="SELECT COUNT(*) FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Enable,)
  SQLres=SQLcur.execute(SQLsentence)
  if Opts.DEBUG:
    for SQLrow in SQLcur:
      sys.stderr.write("%s: found %d pages to enable with filter '%s'.\n"%(Opts.PrgName,SQLrow[0],SQLsentence))
      if EnableInt>0:
        SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE page==%d;"%(EnableInt,))
      else:
        SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Enable,))
      for SQLdebugrow in SQLdebugres:
        SQLfmt="%%%ds\t%%s\n"%(Opts.Digits,)
        sys.stdout.write(SQLfmt%(SQLdebugrow[0],SQLdebugrow[2]))
  else:
    if EnableInt>0:
      SQLres=SQLcur.execute("UPDATE Queue SET downloaded=0 WHERE page==%d;"%(EnableInt,))
    else:
      SQLres=SQLcur.execute("UPDATE Queue SET downloaded=0 WHERE url LIKE \"%%%s%%\";"%(Opts.Enable,))
    SQLcx.commit()
    SQLcx.close()
      
def DeleteURL(Opts):
  """Delete items from the queue"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.Delete='%s'\n"%(Opts.PrgName,Opts.Delete))
  try:
    DeleteInt=int(Opts.Delete)
  except ValueError:
    DeleteInt=0
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  if DeleteInt>0:
    SQLsentence="SELECT COUNT(*) FROM Queue WHERE page==%d;"%(DeleteInt,)
  else:
    SQLsentence="SELECT COUNT(*) FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Delete,)
  SQLres=SQLcur.execute(SQLsentence)
  if Opts.DEBUG:
    for SQLrow in SQLcur:
      sys.stderr.write("%s: found %d pages to delete with filter '%s'.\n"%(Opts.PrgName,SQLrow[0],SQLsentence))
      if DeleteInt>0:
        SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE page==%d;"%(DeleteInt,))
      else:
        SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Delete,))
      for SQLdebugrow in SQLdebugres:
        SQLfmt="%%%ds\t%%s\n"%(Opts.Digits,)
        sys.stdout.write(SQLfmt%(SQLdebugrow[0],SQLdebugrow[2]))
  else:
    if DeleteInt>0:
      SQLres=SQLcur.execute("DELETE FROM Queue WHERE page==%d;"%(DeleteInt,))
    else:
      SQLres=SQLcur.execute("DELETE FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Delete,))
    SQLcx.commit()
    SQLcx.close()
      
def OpenURL(Opts,Queue):
  """Open page with items from the queue"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.Open='%s', Queue=%s\n"%(Opts.PrgName,Opts.Open,Queue))
  try:
    OpenInt=int(Opts.Open)
  except ValueError:
    OpenInt=0
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  if OpenInt>0:
    if Queue:
      SQLsentence="SELECT COUNT(*) FROM Queue WHERE page==%d;"%(OpenInt,)
    else:
      SQLsentence="SELECT COUNT(*) FROM FuturePages WHERE page==%d;"%(OpenInt,)
  else:
    if Queue:
      SQLsentence="SELECT COUNT(*) FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Open,)
    else:
      SQLsentence="SELECT COUNT(*) FROM FuturePages WHERE url LIKE \"%%%s%%\";"%(Opts.Open,)
  SQLres=SQLcur.execute(SQLsentence)
  if Opts.DEBUG:
    for SQLrow in SQLcur:
      sys.stderr.write("%s: found %d pages to open with filter '%s'.\n"%(Opts.PrgName,SQLrow[0],SQLsentence))
      if OpenInt>0:
        if Queue:
          SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE page==%d;"%(OpenInt,))
        else:
          SQLdebugres=SQLcur.execute("SELECT * FROM FuturePages WHERE page==%d;"%(OpenInt,))
      else:
        if Queue:
          SQLdebugres=SQLcur.execute("SELECT * FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Open,))
        else:
          SQLdebugres=SQLcur.execute("SELECT * FROM FuturePages WHERE url LIKE \"%%%s%%\";"%(Opts.Open,))
      for SQLdebugrow in SQLdebugres:
        SQLfmt="%%%ds\t%%s\n"%(Opts.Digits,)
        if Queue:
          sys.stdout.write(SQLfmt%(SQLdebugrow[0],SQLdebugrow[2]))
        else:
          sys.stdout.write(SQLfmt%(SQLdebugrow[0],SQLdebugrow[1]))
  else:
    if OpenInt>0:
      if Queue:
        SQLres=SQLcur.execute("SELECT * FROM Queue WHERE page==%d;"%(OpenInt,))
      else:
        SQLres=SQLcur.execute("SELECT * FROM FuturePages WHERE page==%d;"%(OpenInt,))
    else:
      if Queue:
        SQLres=SQLcur.execute("SELECT * FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Open,))
      else:
        SQLres=SQLcur.execute("SELECT * FROM Queue WHERE url LIKE \"%%%s%%\";"%(Opts.Open,))        
    import platform
    if platform.system()=="Darwin":
      # MacOS
      OpenCommand="open"
    elif platform.system()=="win32" or platform.system()=="win64":
      OpenCommand="start"
    if OpenCommand:
      for SQLrow in SQLres:
        if Queue:
          os.system(OpenCommand+" "+SQLrow[2])
        else:
          os.system(OpenCommand+" "+SQLrow[1])
    SQLcx.commit()
    SQLcx.close()
   
def AddFuture(Opts):
  """Add URL to FuturePages table"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.AddFuture='%s'\n"%(Opts.PrgName,Opts.AddFuture))
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  SQLsentence="SELECT MAX(page) FROM FuturePages;"
  SQLres=SQLcur.execute(SQLsentence)
  if SQLres:
    for SQLrow in SQLcur:
      try:
        MaxPage=int(SQLrow[0])
      except ValueError:
        MaxPage=0
      break
    SQLsentence="INSERT INTO FuturePages VALUES (%d,'%s');"%(MaxPage+1,Opts.AddFuture)
    try:
      SQLres=SQLcur.execute(SQLsentence)
      if SQLres:
        sys.stdout.write("%s: '%s' added to FuturePages\n"%(Opts.PrgName,Opts.AddFuture))
      else:
        sys.stderr.write("%s: error adding '%s' to FuturePages\n"%(Opts.PrgName,Opts.AddFuture))
    except sqlite3.IntegrityError:
      sys.stderr.write("%s: not added, '%s' previously in FuturePages\n"%(Opts.PrgName,Opts.AddFuture))
  SQLcx.commit()
  SQLcx.close()
  
def DeleteFuture(Opts):
  """Remove URL from FuturePages table"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.DeleteFuture='%s'\n"%(Opts.PrgName,Opts.DeleteFuture))
  SQLcx=sqlite3.connect(Opts.DB)
  SQLcur=SQLcx.cursor()
  try:
    DeleteInt=int(Opts.DeleteFuture)
  except ValueError:
    DeleteInt=0
  if DeleteInt>0:
    SQLsentence="SELECT * FROM FuturePages WHERE page==%d;"%(DeleteInt)
  else:
    SQLsentence="SELECT * FROM FuturePages WHERE url LIKE '%%%s%%';"%(Opts.DeleteFuture)
  try:
    SQLres=SQLcur.execute(SQLsentence)
    if SQLres.rowcount==0:
      sys.stderr.write("%s: nothing found with '%s' in FuturePages table.\n"%(Opts.PrgName,Opts.DeleteFuture))
    else:
      if DeleteInt>0:
        SQLsentence="DELETE FROM FuturePages WHERE page==%d;"%(DeleteInt)
      else:
        SQLsentence="DELETE FROM FuturePages WHERE url LIKE '%%%s%%';"%(Opts.DeleteFuture)
      try:
        SQLres=SQLcur.execute(SQLsentence)
        if SQLres:
          sys.stdout.write("%s: '%s' removed from FuturePages table\n"%(Opts.PrgName,Opts.DeleteFuture))
      except sqlite3.IntegrityError:
        sys.stderr.write("%s: error removing '%s' from FuturePages table.\n"%(Opts.PrgName,Opts.DeleteFuture))
  except sqlite3.IntegrityError:
    sys.stderr.write("%s: error searching with '%s' in FuturePages table.\n"%(Opts.PrgName,Opts.DeleteFuture))
  SQLcx.commit()
  SQLcx.close()

def MoveToFuture(Opts):
  """Move URL to FuturePages table"""
  if Opts.DEBUG:
    sys.stderr.write("%s: using DB '%s'\n"%(Opts.PrgName,Opts.DB))
    sys.stderr.write("%s: Opts.Futurize='%s'\n"%(Opts.PrgName,Opts.Futurize))
    sys.stderr.write("%s: Opts.Filter='%s'\n"%(Opts.PrgName,Opts.Filter))
  SQLcx=sqlite3.connect(Opts.DB)
  SQLselquecur=SQLcx.cursor()
  SQLdelquecur=SQLcx.cursor()
  SQLfutcur=SQLcx.cursor()
  try:
    FilterLen=len(Opts.Filter)
  except ValueError:
    FilterLen=0
  if FilterLen==0:
    SQLquesent="SELECT * FROM Queue WHERE Downloaded=0"
  else:
    SQLquesent="SELECT * FROM Queue WHERE Downloaded=0 AND url LIKE '%%%s%%';"%(Opts.Filter)
  if Opts.DEBUG:
    sys.stderr.write("%s: reading Queue rows with '%s'\n"%(Opts.PrgName,SQLquesent))
  try:
    SQLselqueres=SQLselquecur.execute(SQLquesent)
    if SQLselqueres:
      if FilterLen>0:
        sys.stdout.write("%s: rows read from Queue using filter '%s'\n"%(Opts.PrgName,Opts.Filter))
      else:
        sys.stdout.write("%s: rows read from Queue\n"%(Opts.PrgName,))
      InsertCounter=0
      for SQLselquerow in SQLselqueres:
        if Opts.DEBUG:
          sys.stderr.write("%s: got '%s'\n"%(Opts.PrgName,SQLselquerow))
        SQLfutsent="SELECT MAX(page) FROM FuturePages;"
        SQLfutres=SQLfutcur.execute(SQLfutsent)
        MaxPage=SQLfutres.fetchone()[0]
        if Opts.DEBUG:
          sys.stderr.write("%s: '%s' gave MaxPage=%d\n"%(Opts.PrgName,SQLfutsent,MaxPage))
        SQLfutsent="INSERT INTO FuturePages (page,url) VALUES (%d,'%s');"%(MaxPage+1,SQLselquerow[2])
        if Opts.DEBUG:
          sys.stderr.write("%s: trying to insert with '%s'\n"%(Opts.PrgName,SQLfutsent))
        try:
          SQLfutres=SQLfutcur.execute(SQLfutsent)
          SQLcx.commit()
          InsertCounter=InsertCounter+1
        except sqlite3.IntegrityError:
          sys.stderr.write("%s: error trying to insert using '%s'\n"%(Opts.PrgName,SQLfutsent))
        SQLdelquesent="DELETE FROM Queue WHERE url=='%s';"%(SQLselquerow[2])
        try:
          SQLdelqueres=SQLdelquecur.execute(SQLdelquesent)
          SQLcx.commit()
        except sqlite3.IntegrityError:
          sys.stderr.write("%s: error trying to delete with '%s'\n"%(Opts.PrgName,SQLquedelsent))
      else:
        sys.stdout.write("%s: %d inserted into FuturePages\n"%(Opts.PrgName,InsertCounter))
    else:
      sys.stderr.write("%s: error getting resuls of execution of '%s'\n"%(Opts.PrgName,SQLquesent))
  except sqlite3.IntegrityError:
    sys.stderr.write("%s: error executing '%s'\n"%(Opts.PrgName,SQLquesent))
  
# START OF MAIN FILE
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])

try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] URL ...")
  parser.add_option("-p","--process",dest="Action",action="store_const",const="PROCESS",help="Process the queue")
  parser.add_option("-l","--list","--show-queue",dest="Action",action="store_const",const="LIST", help="List queue only")
  parser.add_option("-L", "--history","--show-log",dest="Action",action="store_const",const="LOG",help="List history log only")
  parser.add_option("-o", "--open-dir",dest="Action",action="store_const",const="OPEN",help="Open temporary directory in GUI")
  parser.add_option("-d", "--show-dir",dest="Action",action="store_const",const="DIR",help="Show temporary directory path")
  parser.add_option("-r", "--reenable-url",dest="Enable",action="store",type="string",help="Reenable with URL filter or integer ID",metavar="URL_OR_INT")
  parser.add_option("-x", "--delete",dest="Delete",action="store",type="string",help="Delete with URL filter or integer ID",metavar="URL_OR_INT")
  parser.add_option("--list-future",dest="Action",action="store_const",const="FUTURE",help="List future pages")
  parser.add_option("--filter",dest="Filter",action="store",type="string",help="Filter listings with argument")
  parser.add_option("-O", "--open",dest="Open",action="store",type="string",help="Open with URL filter or integer ID",metavar="URL_OR_INT")
  parser.add_option("--open-future",dest="OpenFuture",action="store",type="string",help="Open future page with URL filter or integer ID",metavar="URL_OR_INT")
  parser.add_option("--add-future",dest="AddFuture",action="store",type="string",help="Add future page with URL",metavar="URL")
  parser.add_option("--delete-future","--del-future",dest="DeleteFuture",action="store",type="string",help="Delete future page with URL filter or integer ID",metavar="URL_OR_INT")
  parser.add_option("--future", "--move-to-future",dest="Futurize",action="store_true",default=False,help="Move all/filtered URLs from queue to future list")
  parser.add_option("--DB",dest="DB",type="string",default="$HOME/Library/Application Support/PhotoGalleries/PhotoGalleryQueue.db",help=SUPPRESS_HELP)
  parser.add_option( "--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option( "--DIGITS", "-#", dest="Digits", action="store", type="int", default=4, help=SUPPRESS_HELP)
  parser.add_option( "--BASEFORMAT", "-B", dest="BaseFormat", action="store", default=" [%%%dd]", help=SUPPRESS_HELP)
  parser.add_option( "--width", "-w", dest="LineWidth", action="store", type="int", default=100, help=SUPPRESS_HELP)

  (Options, Args)=parser.parse_args()
  Options.PrgName=PrgName
  Options.DB=os.path.expanduser(os.path.expandvars(Options.DB))
  Options.Temp=os.path.expanduser(os.path.expandvars("$HOME/Downloads/Images"))
  if Options.Action=="PROCESS":
    ProcessQueue(Options)
  elif Options.Action=="LIST":
    ListQueue(Options,Dw=0)
  elif Options.Action=="LOG":
    ListQueue(Options,Dw=1)
  elif Options.Action=="OPEN":
    OpenDir(Options,Do=True)
  elif Options.Action=="DIR":
    OpenDir(Options,Do=False)
  elif Options.Action=="FUTURE":
    ListFuture(Options)
  elif Options.Enable:
    EnableURL(Options)
  elif Options.Delete:
    DeleteURL(Options)
  elif Options.Open:
    OpenURL(Options,Queue=True)
  elif Options.OpenFuture:
    Options.Open=Options.OpenFuture
    OpenURL(Options,Queue=False)
  elif Options.AddFuture:
    AddFuture(Options)
  elif Options.DeleteFuture:
    DeleteFuture(Options)
  elif Options.Futurize:
    MoveToFuture(Options)
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
