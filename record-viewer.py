#!/usr/local/bin/python3

import sys
import os
import subprocess
import json
import argparse
import csv
import datetime

import numpy
import pyedflib

from pyedflib import highlevel
import matplotlib.pyplot as plt

from hrvanalysis import remove_outliers, remove_ectopic_beats, interpolate_nan_values, get_time_domain_features, get_frequency_domain_features, get_poincare_plot_features, plot_poincare


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

def plotLeadWithRR(leadTitle, times, samples, rr1Title, rr1Times, rr1Values, rr2Title, rr2Times, rr2Values):
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

  color2 = "red"
  color1 = "orange"
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

def hrvAnalysis(times, samples, rrTimes, rrValues):

  def listSecToMsec(secs):
    msecs = []
    for i in range(len(secs)):
      msecs.append( int(secs[i] * 1000) )
    return msecs

  def listMsecToSec(msecs):
    secs = []
    for i in range(len(msecs)):
      secs.append( float(msecs[i]) / 1000)
    return secs

  rrValuesMsec = listSecToMsec(rrValues)
 
  """
  # This remove outliers from signal
  rr_intervals_without_outliers = remove_outliers(rr_intervals=rrValuesMsec,
                                                  low_rri=300, high_rri=2000)

  # This replace outliers nan values with linear interpolation
  interpolated_rr_intervals = interpolate_nan_values(rr_intervals=rr_intervals_without_outliers,
                                                     interpolation_method="linear")


  # This remove ectopic beats from signal
  nn_intervals_list = remove_ectopic_beats(rr_intervals=interpolated_rr_intervals, method="malik")

  # This replace ectopic beats nan values with linear interpolation
  interpolated_nn_intervals = interpolate_nan_values(rr_intervals=nn_intervals_list)

  time_domain_features = get_time_domain_features(interpolated_nn_intervals)
  """

  time_domain_features = get_time_domain_features(rrValuesMsec)

  print("")
  print("TIME DOMAIN FEATURES:")
  for k in time_domain_features.keys():
    v = time_domain_features[k]
    print(" %s : %f" % (k, v))

  freq_domain_features = get_frequency_domain_features(rrValuesMsec)

  print("")
  print("FREQUENCY DOMAIN FEATURES:")
  for k in freq_domain_features.keys():
    v = freq_domain_features[k]
    print(" %s : %f" % (k, v))

  poincare_plot_features = get_poincare_plot_features(rrValuesMsec)

  print("")
  print("POINCARE PLOT FEATURES:")
  for k in poincare_plot_features.keys():
    v = poincare_plot_features[k]
    print(" %s : %f" % (k, v))

  plot_poincare(rrValuesMsec, plot_sd_features=True)

  """
  def rrToTimes(rrList):
    times = []
    prevTime = 0.0 
    for i in range(len(rrList)):
      t = prevTime + rrList[i]
      times.append(t)
      prevTime = t 
    return times

  timesInterpolatedNNIntervals = rrToTimes(interpolated_nn_intervals)
  """

  """
  plotLeadWithRR("leadII", times, samples,
                    "ECGPU", rrTimes, rrValues,
                    "clean", listMsecToSec(timesInterpolatedNNIntervals), rrValues)
  """


  return True 

def main():

  ap = argparse.ArgumentParser()
  ap.add_argument("-r", "--recordName", required=True, help="record name") # type=int, default=42, action=
  ap.add_argument("-v", "--verbose", action='store_true', help="print verbose")
  ap.add_argument("-6", "--plot-6-signals", action='store_true', help="Plot 6 signals one below the other")
  ap.add_argument("-2rr", "--plot-leadII-with-rr-gqrs-ecgpu", action="store_true", help="Plot leadII with both GQRS and ECGPU")
  ap.add_argument("-hrv", "--print-hrv-features", action="store_true", help="Show HRV features (by hrv-analysis lib)")
  args = vars(ap.parse_args())

  gDebug = args['verbose']
  doPlot6Signals = args['plot_6_signals']
  doPlotLeadIIWithRRs = args['plot_leadII_with_rr_gqrs_ecgpu']
  doPrintHrvFeatures = args['print_hrv_features']

  #print("CURR_DIR: ", CURR_DIR)
  #print("recordName: ", args['recordName'])

  samplesCsvFile = CURR_DIR + "/" + args['recordName'] + ".output.samples.txt"
  rrKubiosGqrsLead2File = CURR_DIR + "/" + args['recordName'] + ".gqrs-lead1.rr.kubios.txt"
  rrKubiosEcgpuLead2File = CURR_DIR + "/" + args['recordName'] + ".ecgpu-lead1.rr.kubios.txt"

  times, samples = readSamples(samplesCsvFile)

  timesGqrsLead2, valuesGqrsLead2 = readKubiosRR(rrKubiosGqrsLead2File)
  timesEcgpuLead2, valuesEcgpuLead2 = readKubiosRR(rrKubiosEcgpuLead2File)

  if doPlot6Signals:
    print(" *** Plotting 6 signals")
    plotAllSignals(times, samples)


  if doPlotLeadIIWithRRs:
    print(" *** Plotting LeadII with GQRS and ECGPU")

    print("INFO: LeadII: number of annotations in GQRS: %d" % (len(timesGqrsLead2)))
    print("INFO: LeadII: number of annotations in ECGPU: %d" % (len(timesEcgpuLead2)))


    plotLeadWithRR("leadI", times, samples['leadI'],
                      "GQRS", timesGqrsLead2, valuesGqrsLead2,
                      "ECGPU", timesEcgpuLead2, valuesEcgpuLead2)
    """
    plotLeadWithRR("leadII", times, samples['leadII'],
                      "GQRS", timesGqrsLead2, valuesGqrsLead2,
                      "Filtered GQRS", filtTimesGqrsLead2, filtValuesGqrsLead2)

    plotLeadWithRR("leadII", times, samples['leadII'],
                      "ECGPU", timesEcgpuLead2, valuesEcgpuLead2,
                      "Filtered ECGPU", filtTimesEcgpuLead2, filtValuesEcgpuLead2)
    """

  if doPrintHrvFeatures:
    print(" *** HRV Features")

    hrvAnalysis(times, samples['leadII'], timesEcgpuLead2, valuesEcgpuLead2)


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

