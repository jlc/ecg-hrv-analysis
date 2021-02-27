#!/usr/local/bin/python3

import sys
import os
import subprocess
import argparse
import csv
import datetime
import re

import sqlite3

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

gDebug = False


# Finder
# --------------------------------------------------------------------------------------------
class Finder:
  def __init__(self, directory, extension, recursive=True):
    self.extension = extension
    self.filesDirectory = directory
    self.recursive = recursive # if False => NOT IMPLEMENTED!

  def getFilesWithoutExt(self):
    fileList = []

    for root, dirs, files in os.walk(self.filesDirectory):
      for file in files:
        if file.endswith(self.extension.lower()):
          fileNoExtension = '.'.join( file.split('.')[:-1] )
          fileList.append( os.path.join(root, fileNoExtension) )

    return fileList


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
             'date',
             'durationMs',
             'dateWithOffset',
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
    self.date = 0
    self.dateWithOffset = 0
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
            self.date,
            self.dateWithOffset,
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
      print("ERROR: CSVOutput.write: output file (%s) already exists." % (self.outputFilename))
      return False

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
    SQL_LOAD_RECORD = "SELECT ZDURATION_MS, ZDATERECORDED, ZDATERECORDEDWITHOFFSET, ZHEARTRATE, ZCOMMENT, ZFILENAME from ZECG where ZFILENAME='%s'" % (atcFilename)
    cursor = self.conn.execute(SQL_LOAD_RECORD)

    row = cursor.fetchone()
    if row is None:
      #print("ERROR: AliveECG Database doesn't have record with ATC filename '%s'" % (atcFilename))
      return None

    record.durationMs = int(row[0])
    record.date = int(row[1])
    record.dateWithOffset = int(row[2])
    record.heartRate = float(row[3])
    record.comment = row[4]

    return record

# RecordsBuilder
# --------------------------------------------------------------------------------------------
class RecordsLoader:
  WorkingDirectory = 'work'

  def __init__(self, recordNames, aliveEcgDb=None):
    self.recordNames = recordNames
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

    for recordName in self.recordNames:
      print("Info: Loading record: %s" % (recordName))

      atcFilename = toolsBox.getRecordId(recordName) + '.atc'

      rec = Record()

      # From Alive Database
      if self.aliveEcgDb is not None:
        rec = self.updateRecordFromAliveDb(atcFilename, rec) 
        if rec is None:
          print("ERROR: Record '%s' does not exists in Alive ECG SQLitew database." % (atcFilename))
          break

      # GQRS
      gqrsGetHrvLead1Filename = toolsBox.getRecordWorkFilename(recordName, 'gqrs.gethrv.txt')
      if not os.path.isfile(gqrsGetHrvLead1Filename):
        print("ERROR: get_hrv GQRS one line file not found (%s)" % (gqrsGetHrvLead1Filename))
      else:
        r = self.updateRecordFromGetHrvFile('GQRS', 'physionet-get_hrv', gqrsGetHrvLead1Filename, rec)
        records.append(r)

      # ECGPU
      ecgpuGetHrvLead1Filename = toolsBox.getRecordWorkFilename(recordName, 'ecgpu.gethrv.txt')
      if not os.path.isfile(ecgpuGetHrvLead1Filename):
        print("ERROR: get_hrv ECPU one line file not found (%s)" % (ecgpuGetHrvLead1Filename))
      else:
        r = self.getRecordFromGetHrvFile('ECGPU', 'physionet-get_hrv', ecgpuGetHrvLead1Filename, rec)
        records.append(r)

    return records



# --------------------------------------------------------------------------------------------
class SQLLightDatabase:
  def __init__(self, filename):
    self.dbFilename = filename


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

  def loadAndWriteCSV(self, atcFilesDirectory, aliveDbFilename=None):

    aliveDb = None
    if aliveDbFilename is not None:
      aliveDb = AliveECGDB(aliveDbFilename)

    atcFinder = Finder(atcFilesDirectory, 'atc')
    recordNames = atcFinder.getFilesWithoutExt()

    print("Debug: Loading hrv records...")
    recordsLoader = RecordsLoader(recordNames, aliveDb)
    records = recordsLoader.loadRecords()

    print("Debug: Writing CSV output file '%s'" % (self.csvFilename))
    csvOutput = CSVOutput(self.csvFilename)
    csvOutput.write(records)



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
    aliveDbFilename = args['alive_ecg_filename']
    if not os.path.isfile(aliveDbFilename):
      print("ERROR: Alive ECG SQLite database '%s' does not exists." % (aliveDbFilename))
      return 1
    print("Info: using Alive ECG SQLite database '%s'" % (aliveDbFilename))

  if doProcessATCFiles:
    print("Info: loading and processing atc files in '%s'" % (atcDirectory))
    p = Processor()
    p.loadAndWriteCSV(atcDirectory, aliveDbFilename)

  return 0

if __name__ == "__main__":
  ret = main()
  if not ret: print("Done.")
  exit(ret)
