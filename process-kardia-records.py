#!/usr/local/bin/python3

import sys
import os
import subprocess
import argparse
import csv
import datetime
import re
import copy

import sqlite3

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

gDebug = False

# Finder
# --------------------------------------------------------------------------------------------
class Finder:
  def __init__(self, directory, extensionToFind, recursive=True):
    self.extension = extensionToFind
    self.filesDirectory = directory
    self.recursive = recursive # if False => NOT IMPLEMENTED!

  # removeExt: contain extension to remove
  def getFiles(self, removeExt=False): # return {filepath: filename, ...}
    d = {}

    for root, dirs, files in os.walk(self.filesDirectory):
      for file in files:
        if file.endswith(self.extension.lower()):
          path = os.path.join(root, file)
          if removeExt:
            fileNoExt = '.'.join( file.split('.')[:-1] )
            d[path] = fileNoExt
          else:
            path = os.path.join(root, file)
            d[path] = file

    return d

class ToolsBox:
  def __init__(self): pass 

  def getRecordWorkFilename(self, recordName, extension):
      # e.g. recordName blah/data/b6 - extesion: "ann-12"
      recordId = recordName.split('/')[-1:][0] # b6
      recordFile = CURR_DIR + '/' + recordName # curr_dir + blah/data/b6
      recordFileDir = '/'.join( recordFile.split('/')[:-1] ) # curr_dir + blah/data
      recordWorkDir = os.path.join(recordFileDir, RecordsLoader.WorkingDirectory) # curr_dir + blah/data/work
      recordWorkFilename = os.path.join(recordWorkDir, recordId ) + '.' + extension # curr_dir + blah/data/work/b6.extension
      return recordWorkFilename

  def getRecordId(self, recordName):
      # e.g. recordName blah/data/b6
      recordId = recordName.split('/')[-1:][0] # b6
      return recordId

  def filenameToRecordName(self, filename):
    # ensure letters, digits and underscores only

    def isValid(filename):
      r = re.compile(r'^[\w\d_]*$')
      m = r.match(filename) 
      if m is None: return False
      else: return True

    if len(filename) > 40:
      toomuch = len(filename) - 40
      filename = 'S' + filename[toomuch:]

    if isValid(filename): return filename

    withoutMinus = filename.replace('-', '')
    if isValid(withoutMinus): return withoutMinus

    print("ERROR: filenameToRecordName: Unable to convert filename (%s)" % (filename))
    return None

toolsBox = ToolsBox()



# Kardia Record
# --------------------------------------------------------------------------------------------
class Record:
  # HRV parameters
  # ------------------------------------------------------------------------------------------
  class HRV:
    headers = ['nn_rr',
               'avnn',
               'sdnn',
               'rmssd',
               'pnn50',
               'ulf_pwr',
               'vlf_pwr',
               'lf_pwr',
               'hf_pwr',
               'lfhf_ratio']
    def __init__(self):
      self.nnRr = 0
      self.avnn = 0
      self.sdnn = 0
      self.rmssd = 0
      self.pnn50 = 0
      self.ulfPwr = 0
      self.vlfPwr = 0
      self.lfPwr = 0
      self.hfPwr = 0
      self.lfhfRatio = 0
    def asList(self):
      return [self.nnRr,
              self.avnn,
              self.sdnn,
              self.rmssd,
              self.pnn50,
              self.ulfPwr,
              self.vlfPwr,
              self.lfPwr,
              self.hfPwr,
              self.lfhfRatio]

  headers = ['recordName',
             'patientId',
             'group',
             'prePost',
             'drOrPt',
             'durationMs',
             'datetime',
             'heartRate',
             'comment',
             'atcFilename',
             'hrvQrsAlgo',
             'hrvCalculator'] + HRV.headers
  def __init__(self):
    self.recordName = ''
    self.patientId = ''
    self.group = ''
    self.prePost = ''
    self.drOrPt = ''
    self.durationMs = 0
    self.datetime = ''
    self.heartRate = 0
    self.comment = ''
    self.atcFilename = ''
    self.hrvQrsAlgo = ''
    self.hrvCalculator = ''
    self.hrv = Record.HRV()
  def asList(self): 
    return [self.recordName,
            self.patientId,
            self.group,
            self.prePost,
            self.drOrPt,
            self.durationMs,
            self.datetime,
            self.heartRate,
            self.comment,
            self.atcFilename,
            self.hrvQrsAlgo,
            self.hrvCalculator] + self.hrv.asList()

# KardiaRecords
# All Kardia Records
# --------------------------------------------------------------------------------------------
class KardiaRecords:
  def __init__(self):
    self.records = []

  def add(self, record):
    self.records.append(record)

  def getRecords(self): return self.records

# CSVOutput
# Write KardiaRecords in a CSV file
# --------------------------------------------------------------------------------------------
class CSVOutput:
  def __init__(self, filename):
    self.outputFilename = filename

  def write(self, records):

    if os.path.isfile(self.outputFilename):
      print("Info: CSVOutput.write: output file (%s) already exists, recreating it." % (self.outputFilename))
      os.remove(self.outputFilename)

    with open(self.outputFilename, mode='w') as file:
      writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

      # Headers
      writer.writerow( Record.headers )
      # Records
      for rec in records:
        writer.writerow( rec.asList() )
        
    return True

# AliveECGDB
# --------------------------------------------------------------------------------------------
class AliveECGDB:

  def __init__(self, sqliteFilename):
    self.conn = sqlite3.connect(sqliteFilename)

  def __del__(self):
    self.conn.close()

  def updateRecord(self, atcFilename, record): # return the updated record
    # IMPORTANT NOTE: Kardia store ZDATERECORDED starting from 2001-01-01 --> we add this constant to get it from now (constant found in Kardia SQLite database too)
    SQL_LOAD_RECORD = "select ZDURATION_MS, datetime(ZDATERECORDEDWITHOFFSET + 978307200, 'unixepoch') as Z_DATETIME,  ZHEARTRATE, ZCOMMENT, ZFILENAME from ZECG where ZFILENAME='%s' or ZENHANCEDFILENAME='%s'" % (atcFilename, atcFilename)
    cursor = self.conn.execute(SQL_LOAD_RECORD)

    row = cursor.fetchone()
    if row is None:
      #print("ERROR: AliveECG Database doesn't have record with ATC filename '%s'" % (atcFilename))
      return None

    record.durationMs = int(row[0])
    record.datetime = str(row[1])
    record.heartRate = float(row[2])
    record.comment = row[3]
    record.atcFilename = atcFilename

    return record

# RecordsBuilder
# --------------------------------------------------------------------------------------------
class RecordsLoader:
  WorkingDirectory = 'work'

  def __init__(self, recordNamesDict, aliveEcgDb=None):
    self.recordNamesDict = recordNamesDict # {recordName: (atcFilename, atcFilepath), ..}
    self.aliveEcgDb = aliveEcgDb 

  def updateRecordFromAliveDb(self, atcFilename, rec): # return the update rec: Record()
    if self.aliveEcgDb is None:
      return rec
    
    record = self.aliveEcgDb.updateRecord(atcFilename, rec)
    return record

  def updateRecordFromGetHrvFile(self, qrsAlgo, hrvCalculator, filename, rec): # return the updated rec: Record()
    with open(filename, mode='r',) as f:
      line = f.readline()
      gethrvRe = re.compile(r'^([\w/]+) : ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) : ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)')
      m = gethrvRe.match(line)

      if m is None:
        print("Error: get_hrv GQRS one line does _not_ match the regular expression.")
        return None

      rec.recordName = m.group(1) # record_name
      #rec.patientId
      #rec.group
      #rec.prePost
      #rec.drOrPt
      #rec.date
      rec.hrvQrsAlgo = qrsAlgo
      rec.hrvCalculator = hrvCalculator
      rec.hrv.nnRr = m.group(2) # nn_rr
      rec.hrv.avnn = m.group(3) # avnn
      rec.hrv.sdnn = m.group(4) # sdnn
      #m.group(5) # sdann
      #m.group(6) # sdnnidx
      rec.hrv.rmssd = m.group(7) # rmssd
      rec.hrv.pnn50 = m.group(8) # pnn50
      # m.group(9) # tot_pwr
      rec.hrv.ulfPwr = m.group(10) # ulf_pwr
      rec.hrv.vlfPwr = m.group(11) # vlf_pwr
      rec.hrv.lfPwr = m.group(12) # lf_pwr
      rec.hrv.hfPwr = m.group(13) # hf_pwr
      rec.hrv.lfhfRatio = m.group(14) # lf_hf_ratio

      return rec

  def loadRecords(self): # return [Record(), ...]
    records = []

    if self.aliveEcgDb is not None:
        print("Info: loadRecords: also loading records from Alive SQLite Database")

    for recordName in self.recordNamesDict.keys():
      print("Info: Loading record: %s" % (recordName))
      (atcFilename, atcFilepath) = self.recordNamesDict[recordName] 
      #print("Debug:   atcFilename: %s - atcFilepath: %s" % (atcFilename, atcFilepath))

      rec = Record()

      # From Alive Database
      if self.aliveEcgDb is not None:
        rec = self.updateRecordFromAliveDb(atcFilename, rec) 
        if rec is None:
          print("ERROR: Record '%s' does not exists in Alive ECG SQLitew database." % (atcFilename))
          break

      # GQRS
      copyRec = copy.deepcopy(rec)
      gqrsGetHrvLead1Filename = toolsBox.getRecordWorkFilename(recordName, 'output.gethrv-gqrs-lead1.txt')
      if not os.path.isfile(gqrsGetHrvLead1Filename):
        print("ERROR: get_hrv GQRS one line file not found (%s)" % (gqrsGetHrvLead1Filename))
      else:
        gqrs = self.updateRecordFromGetHrvFile('GQRS', 'physionet-get_hrv', gqrsGetHrvLead1Filename, copyRec)
        records.append(gqrs)

      # ECGPU
      copyRec = copy.deepcopy(rec)
      ecgpuGetHrvLead1Filename = toolsBox.getRecordWorkFilename(recordName, 'output.gethrv-ecgpu-lead1.txt')
      if not os.path.isfile(ecgpuGetHrvLead1Filename):
        print("ERROR: get_hrv ECPU one line file not found (%s)" % (ecgpuGetHrvLead1Filename))
      else:
        ecgpu = self.updateRecordFromGetHrvFile('ECGPU', 'physionet-get_hrv', ecgpuGetHrvLead1Filename, copyRec)
        records.append(ecgpu)

    return records


# Processor()
# --------------------------------------------------------------------------------------------
# Jobs:
# - find all .atc files
# - find and open sqlight database
# - open CSV output file
# - for each record
#   - convert to edf (atc2edf.py)
#   - calculate HRV 
#   - read SQLLight database record + parse comments
#   - add record to CSV file
class Processor:
  def __init__(self):
    self.csvFilename = CURR_DIR + '/' + 'output.process-kardia.csv'
    self.logFile = CURR_DIR + '/' + 'output.process-kardia.log'

    if os.path.isfile(self.logFile):
      print("Info: erasing previous log file (%s)" % (self.logFile)) 
      os.remove(self.logFile)

  def loadAndWriteCSV(self, atcFilesDirectory, aliveDbFilename=None):

    aliveDb = None
    if aliveDbFilename is not None:
      aliveDb = AliveECGDB(aliveDbFilename)

    atcFinder = Finder(atcFilesDirectory, 'atc')
    atcFiles = atcFinder.getFiles(False)
    atcFilesNoExt = atcFinder.getFiles(True)

    """
    print("DEBUG: atcFiles:")
    for k in atcFiles.keys(): print(" %s: %s" % (k, atcFiles[k]))
    print("DEBUG: atcFilesNoExt:")
    for k in atcFilesNoExt.keys(): print(" %s: %s" % (k, atcFilesNoExt[k])) 
    """

    recordNamesDict = {} # {recordNames: (atcFilename, atcFilepath), ..}
    for atcFilepath in atcFiles.keys():
      atcFilename = atcFiles[atcFilepath] 
      atcFiledir = '/'.join( atcFilepath.split('/')[:-1] )
      atcFilenameNoExt = atcFilesNoExt[atcFilepath]

      recordName = atcFiledir + '/' + toolsBox.filenameToRecordName(atcFilenameNoExt)
      if recordName is None: return False

      recordNamesDict[recordName] = (atcFilename, atcFilepath)


    error = False
    print("Info: Convert ATC -> EDF, and calculate HRVs...")
    for rname in recordNamesDict.keys():
      (atcfile, atcfilepath) = recordNamesDict[rname]

      print("Info: processing ATC (%s) to record (%s)" % (atcfilepath, rname))
      print("------ - %s - ---------------------------------" % (rname), file=open(self.logFile, 'a'))

      cmd = "./atc2edf.py -i %s -r %s 1>>%s 2>&1" % (atcfilepath, rname, self.logFile)
      #print("DEBUG: executing: ", cmd)
      if os.system(cmd):
        print("ERROR: Unable to convert atc (%s) (recordName: %s)" % (atcfilepath, rname))
        error = True
      else:
        cmd = "./calculate.sh %s 1>>%s 2>&1" % (rname, self.logFile)
        #print("DEBUG: executing: ", cmd)
        if os.system(cmd):
          print("ERROR: Unable to calculate recordName (%s)" % (rname))
          error = True

    if error:
      print("ERROR: There were errors converting and/or calculating HRVs.")
      return False 


    print("Debug: Loading hrv records...")
    recordsLoader = RecordsLoader(recordNamesDict, aliveDb)
    records = recordsLoader.loadRecords()

    print("Debug: Writing CSV output file '%s'" % (self.csvFilename))
    csvOutput = CSVOutput(self.csvFilename)
    csvOutput.write(records)

    return True


def main():

  ap = argparse.ArgumentParser()
  ap.add_argument("-d", "--atcFilesDirectory", required=True, help="Source directory with .ATC files in.")
  ap.add_argument("-v", "--verbose", action='store_true', help="print verbose")
  ap.add_argument("-o", "--output-csv-filename", required=False, help="output CSV filename.")
  ap.add_argument("-a", "--alive-ecg-filename", required=False, help="Alive ECG Database filename.")
  ap.add_argument("-P", "--process-atc-files", action="store_true", required=False, help="process ATC files, load records (HRV and SQL) and write CSV output")
  #ap.add_argument("-hrv", "--print-hrv-features", action="store_true", help="Show HRV features (by hrv-analysis lib)")
  args = vars(ap.parse_args())

  gDebug = args['verbose']
  doProcessATCFiles = args['process_atc_files']

  # add CURR_DIR + "/"
  atcDirectory = args['atcFilesDirectory']

  aliveDbFilename = None
  if 'alive_ecg_filename' in args.keys():
    dbfilename = args['alive_ecg_filename']
    if dbfilename is not None:
      if os.path.isfile(dbfilename):
        print("Info: using Alive ECG SQLite database '%s'" % (dbfilename))
        aliveDbFilename = dbfilename
      else:
        print("ERROR: Alive ECG SQLite database '%s' does not exists." % (aliveDbFilename))
        return 1

  r = 0
  if doProcessATCFiles:
    print("Info: loading and processing atc files in '%s'" % (atcDirectory))
    p = Processor()
    r = p.loadAndWriteCSV(atcDirectory, aliveDbFilename)

  return r

if __name__ == "__main__":
  ret = main()
  if not ret: print("Done.")
  exit(ret)
