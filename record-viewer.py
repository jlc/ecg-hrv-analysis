#!/usr/local/bin/python3

import sys
import os
import subprocess
import json
import datetime
import argparse
import csv

import numpy
import pyedflib

from pyedflib import highlevel
import matplotlib.pyplot as plt

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

gDebug = False

"""
read .rr files --> NOT NEEDED ANYMORE : require conversion
def readRR(rrCsvFile, times, sampleValues): # ( [id1, id2, ...], [time1, time2, ...], [value1, value2, ...] )
  recordIds = []
  values = []
  rrTimes = []

  with open(rrCsvFile, newline='') as rrfile:
    reader = csv.reader(rrfile, delimiter="\t")
    for row in reader:
      i = int(row[0].strip())
      t = times[i]
      v = sampleValues[i]
      recordIds.append(i)
      rrTimes.append(t) 
      values.append(v)

  return recordIds, rrTimes, values
"""

def readKubiosRR(rrKubiosCsvFile): # ([time1, time2, ...], [value1, value2, ...])
  rrTimes = []
  values = []
  
  with open(rrKubiosCsvFile, newline='') as rrfile:
    reader = csv.reader(rrfile, delimiter="\t")
    for row in reader:
      t = float(row[0].strip())
      v = float(row[1].strip())
      rrTimes.append(t)
      values.append(v)

  return rrTimes, values

def readSamples(samplesCsvFile): # ( [sec1, sec2, ...], samples{'title': [values, ...], ...} )
  samples = {}
  idToTitles = {}

  with open(samplesCsvFile, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    line = 0
    for row in reader:
      time = row[0]

      # titles
      if line == 0:
        for r in range(len(row)):
          title = row[r].strip()
          samples[title] = []
          idToTitles[r] = title

      # units
      elif line == 1:
        next

      # other lines are data
      else:
        for r in range(len(row)):
          title = idToTitles[r]
          samples[title].append(float(row[r].strip()))

      line += 1

  timeTitle = idToTitles[0]
  times = samples[timeTitle]
  del samples[timeTitle]

  """
  DEBUG:
  timeTitle = idToTitles[0]
  for title in samples:

    print("title: %s" % (title))
    for i in range(10):
      print("time: %f: %f" % (samples[timeTitle][i], samples[title][i]))
  """

  return times, samples

def plotAllSignals(times, samples):

  nbSignals = len(samples.keys())
  fig, ax = plt.subplots(nbSignals)

  sig = 0
  for title in samples.keys():
    ax[sig].plot(times, samples[title])
    ax[sig].set_title("%s" % (title))
    ax[sig].set_xlabel('time')
    ax[sig].set_ylabel('mV')

    sig += 1

  plt.show()

def plotRR(times, sample, rrTimes, rrValues, title, lead, rrLabel):

  yMin = min(sample)
  yMax = max(sample)

  plt.plot(times, sample, label=lead)
  plt.plot(rrTimes, rrValues, 'x', label=rrLabel, color="orange")
  plt.vlines(x=rrTimes, ymin=yMin, ymax=yMax, color="orange")
  plt.xlabel('time')
  plt.ylabel('mV')
  plt.title(title)
  plt.legend()
  plt.show()

def plot2LeadsWithRR(leadTitle, times, samples, rr1Title, rr1Times, rr1Values, rr2Title, rr2Times, rr2Values):
  yMin = min(samples)
  yMax = max(samples)

  fig, ax = plt.subplots(2)
  
  ax[0].plot(times, samples, label=leadTitle)
  ax[0].plot(rr1Times, rr1Values, 'x', label=rr1Title, color="orange")
  ax[0].vlines(x=rr1Times, ymin=yMin, ymax=yMax, color="orange")
  ax[0].set_xlabel('time')
  ax[0].set_ylabel('mV')
  ax[0].set_title(leadTitle + " - " + rr1Title)
  ax[0].legend()

  ax[1].plot(times, samples, label=leadTitle)
  ax[1].plot(rr2Times, rr2Values, 'x', label=rr2Title, color="orange")
  ax[1].vlines(x=rr2Times, ymin=yMin, ymax=yMax, color="orange")
  ax[1].set_xlabel('time')
  ax[1].set_ylabel('mV')
  ax[1].set_title(leadTitle + " - " + rr2Title)
  ax[1].legend()

  plt.show()

  #fig, ax = plt.subplots(1)

  color2 = "green"
  color1 = "red"
  plt.plot(times, samples, label=leadTitle)
  plt.plot(rr1Times, rr1Values, 'x', label=rr1Title, color=color1)
  plt.vlines(x=rr1Times, ymin=yMin, ymax=yMax, color=color1)
  plt.plot(rr2Times, rr2Values, 'x', label=rr2Title, color=color2)
  plt.vlines(x=rr2Times, ymin=yMin, ymax=yMax, color=color2)
  plt.xlabel('time')
  plt.ylabel('mV')
  plt.title(leadTitle + " - " + rr1Title + " - " + rr2Title)
  plt.legend()

  plt.show()


# FUNCTIONS TO IMPLEMENTS:
"""
X plot normal: 6 signals one below the other
X plot normal: lead 1 and 2 with RR
- plot compare: (atc signals &&) edf signals && rdsamp signals
"""


def main():

  ap = argparse.ArgumentParser()
  ap.add_argument("-r", "--recordName", required=True, help="record name") # type=int, default=42, action=
  ap.add_argument("-v", "--verbose", action='store_true', help="print verbose")
  ap.add_argument("-6", "--plot-6-signals", action='store_true', help="Plot 6 signals one below the other")
  ap.add_argument("-2rr", "--plot-leadII-with-rr-gqrs-ecgpu", action="store_true", help="Plot leadII with both GQRS and ECGPU")
  args = vars(ap.parse_args())

  gDebug = args['verbose']
  doPlot6Signals = args['plot_6_signals']
  doPlotLeadIIWithRRs = args['plot_leadII_with_rr_gqrs_ecgpu']

  #print("CURR_DIR: ", CURR_DIR)
  #print("recordName: ", args['recordName'])

  samplesCsvFile = CURR_DIR + "/" + args['recordName'] + ".samples"

  times, samples = readSamples(samplesCsvFile)

  if doPlot6Signals:
    print(" *** Plotting 6 signals")
    plotAllSignals(times, samples)


  if doPlotLeadIIWithRRs:
    print(" *** Plotting LeadII with GQRS and ECGPU")
    rrKubiosGqrsLead1File = CURR_DIR + "/" + args['recordName'] + ".ann-gqrs-s0.rr.kubios.txt"
    rrKubiosGqrsLead2File = CURR_DIR + "/" + args['recordName'] + ".ann-gqrs-s1.rr.kubios.txt"
    rrKubiosEcgpuLead1File = CURR_DIR + "/" + args['recordName'] + ".ann-ecgpu-s0.rr.kubios.txt"
    rrKubiosEcgpuLead2File = CURR_DIR + "/" + args['recordName'] + ".ann-ecgpu-s1.rr.kubios.txt"

    timesGqrsLead1, valuesGqrsLead1 = readKubiosRR(rrKubiosGqrsLead1File)
    timesGqrsLead2, valuesGqrsLead2 = readKubiosRR(rrKubiosGqrsLead2File)
    timesEcgpuLead1, valuesEcgpuLead1 = readKubiosRR(rrKubiosEcgpuLead1File)
    timesEcgpuLead2, valuesEcgpuLead2 = readKubiosRR(rrKubiosEcgpuLead2File)

    print("INFO: LeadII: number of annotations in GQRS: %d" % (len(timesGqrsLead2)))
    print("INFO: LeadII: number of annotations in ECGPU: %d" % (len(timesEcgpuLead2)))

    plot2LeadsWithRR("leadII", times, samples['leadII'],
                      "GQRS", timesGqrsLead2, valuesGqrsLead2,
                      "ECGPU", timesEcgpuLead2, valuesEcgpuLead2)

  """
  plotRR(times, samples['leadI'], timesGqrsLead1, valuesGqrsLead1, "LeadI - GQRS", "leadI", "gqrs")
  plotRR(times, samples['leadII'], timesGqrsLead2, valuesGqrsLead2, "LeadII - GQRS", "leadII", "gqrs")
  plotRR(times, samples['leadI'], timesEcgpuLead1, valuesEcgpuLead1, "LeadI - ECGPU", "leadI", "ecgpu")
  plotRR(times, samples['leadII'], timesEcgpuLead2, valuesEcgpuLead2, "LeadII - ECGPU", "leadII", "ecgpu")
  """
  """
  rrGqrsLead1File = CURR_DIR + "/" + args['recordName'] + ".ann-gqrs-s0.rr"
  rrGqrsLead2File = CURR_DIR + "/" + args['recordName'] + ".ann-gqrs-s1.rr"
  rrEcgpuLead1File = CURR_DIR + "/" + args['recordName'] + ".ann-ecgpu-s0.rr"
  rrEcgpuLead2File = CURR_DIR + "/" + args['recordName'] + ".ann-ecgpu-s1.rr"

  recordIdsGqrsLead1, timesGqrsLead1, valuesGqrsLead1 = readRR(rrGqrsLead1File, times, samples['leadI'])
  recordIdsGqrsLead2, timesGqrsLead2, valuesGqrsLead2 = readRR(rrGqrsLead2File, times, samples['leadII'])
  recordIdsEcgpuLead1, timesEcgpuLead1, valuesEcgpuLead1 = readRR(rrEcgpuLead1File, times, samples['leadI'])
  recordIdsEcgpuLead2, timesEcgpuLead2, valuesEcgpuLead2 = readRR(rrEcgpuLead2File, times, samples['leadII'])
  """


  return 0

if __name__ == "__main__":
  ret = main()
  if not ret: print("done.")
  exit(ret)


#####################################################
#####################################################
#####################################################

def convertAtc2Dict(filename):
  os.environ['GOPATH'] =  CURR_DIR + '/dependencies/atc2json/'

  cmdConvertAtc2Json = "go run %s/dependencies/atc2json/main.go < %s" % (CURR_DIR, filename)

  if gDebug: print(" - converting ATC to json using: '%s'" % (cmdConvertAtc2Json))

  res = subprocess.check_output(cmdConvertAtc2Json, shell=True)
  resJson = res.decode('utf-8')

  d = json.loads(resJson)
  return d 

def convertAtcDict2Edf(edfFilename, atcDict):
  dimension = 'mV'
  sampleRate = atcDict['frequency']
  amplitudeResolution = atcDict['amplitudeResolution']
  mainsFrequency = atcDict['mainsFrequency']
  gain = atcDict['gain']

  def listOfIntToString(data):
    out = ""
    for i in range(len(data)):
      if(data[i] and data[i] is not None): out += chr(data[i])
    return out[:]

  dateRecorded = listOfIntToString(atcDict['Info']['DateRecorded'])
  dateTimeRecorded = datetime.datetime.strptime(dateRecorded, "%Y-%m-%dT%H:%M:%S%z")
  recordingUUID = listOfIntToString(atcDict['Info']['RecordingUUID'])
  phoneUDID = listOfIntToString(atcDict['Info']['PhoneUDID'])
  phoneModel = listOfIntToString(atcDict['Info']['PhoneModel'])
  recorderSoftware = listOfIntToString(atcDict['Info']['RecorderSoftware'])
  recorderHardware = listOfIntToString(atcDict['Info']['RecorderHardware'])
  location = listOfIntToString(atcDict['Info']['Location'])

  def debugInfos():
    print("dateRecorded: " + dateRecorded)
    print("dateTimeRecorded: " + str(dateTimeRecorded))
    print("recordingUUID: " + recordingUUID)
    print("phoneUDID: " + phoneUDID)
    print("phoneModel: " + phoneModel)
    print("recorderSoftware: " + recorderSoftware)
    print("recorderHardware: " + recorderHardware)
    print("location: " + location)
  #debugInfo()
  
  def convertDigitalToAnalog(digitalSamples, amplitudeResolution):
    # from: https://developers.kardia.com/#ecg-samples-object
    # "To convert to millivolts, divide these samples by (1e6 / amplitudeResolution)."
    out = []
    divider = float(1e6) / float(amplitudeResolution)
    for i in range(len(digitalSamples)):
      mV = float(digitalSamples[i]) / divider
      out.append(mV)
    return out

  channels = ['leadI', 'leadII', 'leadIII', 'aVR', 'aVL', 'aVF']
  nbChannelsHere = 0 
  for chan in channels:
    if chan in atcDict['samples']:
      nbChannelsHere += 1 

  f = pyedflib.EdfWriter(edfFilename, nbChannelsHere, file_type=pyedflib.FILETYPE_EDF)

  #f.setEquipment(recorderHardware + " " + recorderSoftware + " (" + phoneModel + ")")
  f.setEquipment(recorderSoftware + "(on " + phoneModel + ")")
  f.setStartdatetime(dateTimeRecorded)
  f.setPatientCode(recordingUUID)

  channelInfo = []
  dataList = []

  edfsignal = 0
  nbChannelsLeft = len(channels)
  channelsAdded = ""

  for chan in channels:
    nbChannelsLeft -= 1

    if chan in atcDict['samples']:
      chDict = {'label':chan, 'dimension':dimension, 'sample_rate':int(sampleRate),
                'physical_max':16.38, 'physical_min':-16.38, 'digital_max':32767, 'digital_min':-32768, 'transducer':'', 'prefilter': ''}

      #print("DEBUG: setSignalHeader( %d, %s)" % (edfsignal, str(chDict)))
      f.setSignalHeader(edfsignal, chDict)
      f.setLabel(edfsignal, chan)
      f.setSamplefrequency(edfsignal, int(sampleRate))

      channelInfo.append(chDict)

      ar = numpy.array(convertDigitalToAnalog(atcDict['samples'][chan], amplitudeResolution))
      dataList.append(ar)

      edfsignal += 1

      channelsAdded += chan + ', ' if nbChannelsLeft else chan 

  #f.setRecordingAdditional()
  #f.setSignalHeaders(channelInfo)
  f.writeSamples(dataList)
  f.close()
  del f 

  print(" - channels %s added" % (channelsAdded))
  print(" - EDF file: '%s'" % (edfFilename))
  return True

def compareEdfs(edfFilename1, edfFilename2, verbose=True):
  highlevel.compare_edf(edfFilename1, edfFilename2, verbose)

def debugEdf(edfFilename):
  signals, signalHeaders, header = highlevel.read_edf(edfFilename)

  print(" -------------------------------------- ")
  print(" DEBUG EDF: '%s'" % (edfFilename))
  print("--------------------------------------- ")
  print("")
  print("HEADERS:")
  print("--------")
  print(header)
  print("")
  print("SIGNAL HEADERS:")
  print("---------------")
  print(signalHeaders)
  print("")
  print("SIGNALS:")
  print("--------")
  print("")
  print(signals)
  """
  for s in signals:
    l = len(s)
    print(" - signal length: %d - signal: %s" % (l, str(s)))
  """

def plotEdfs(edfFilename1, edfFilename2):

  signals1, signalHeaders1, header1 = highlevel.read_edf(edfFilename1)
  signals2, signalHeaders2, header2 = highlevel.read_edf(edfFilename2)
  
  plt.plot(signals1[0], color="green")
  plt.plot(signals2[0], "x", color="blue")
  plt.show()

  plt.plot(signals1[1], color="orange")
  plt.plot(signals2[1], color="red")
  plt.show()


