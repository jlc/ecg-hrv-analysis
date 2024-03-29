#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Help: $0 <record name>"
    exit 1
    fi

RECORD=$1

MYPATH=`dirname $0`
RECORD_ID=`basename $RECORD`
RECORD_DIR=`dirname $RECORD`
RECORD_FILE=$MYPATH/$RECORD
RECORD_WORK_FILE=$MYPATH/$RECORD_DIR/work/$RECORD_ID
RECORD_WORK_ID=$RECORD_DIR/work/$RECORD_ID

echo "record_id: $RECORD_ID - record_dir: $RECORD_DIR - record_work_file: $RECORD_WORK_FILE"

RECORD_FILE_HEA=$RECORD_WORK_FILE.hea
RECORD_FILE_DAT=$RECORD_WORK_FILE.dat

# .atc.edf is generated by Alive File Converter
#EDF_FILE=$RECORD_FILE.atc.edf
# .edf is generated by me :)
EDF_FILE=$RECORD_FILE.edf
if [[ ! -e $EDF_FILE ]]; then echo "Error: edf file ($EDF_FILE) does not exist."; exit 1; fi

# annotation files (contain data stream annotation (eg. where is the QRS)
ANN_GQRS_LEAD1=gqrs-lead1
ANN_GQRS_LEAD2=gqrs-lead2
ANN_ECGPU_LEAD1=ecgpu-lead1
ANN_ECGPU_LEAD2=ecgpu-lead2
# OUTPUTS (in data/work)
ANN_GQRS_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD1
ANN_GQRS_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD2
#ANN_ECGPU_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD1
#ANN_ECGPU_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD2

# RR intervals files
RR_GQRS_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD1.rr
RR_GQRS_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD2.rr
#RR_ECGPU_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD1.rr
#RR_ECGPU_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD2.rr

# Filtered RR intervals files
RR_FILT_GQRS_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD1.frr 
RR_FILT_GQRS_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD2.frr 
#RR_FILT_ECGPU_LEAD1_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD1.frr
#RR_FILT_ECGPU_LEAD2_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD2.frr

# RR intervals files for kubios
RR_GQRS_LEAD1_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD1.rr.kubios.txt
RR_GQRS_LEAD2_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD2.rr.kubios.txt
#RR_ECGPU_LEAD1_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD1.rr.kubios.txt
#RR_ECGPU_LEAD2_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD2.rr.kubios.txt

#RR_FILT_GQRS_LEAD1_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_GQRS_LEAD1.frr.kubios.txt
#RR_FILT_ECGPU_LEAD1_KUBIOS_FILE=$RECORD_WORK_FILE.$ANN_ECGPU_LEAD1.frr.kubios.txt

GETHRV_GQRS_LEAD1_FILE=$RECORD_WORK_FILE.output.gethrv-gqrs-lead1.txt
GETHRV_GQRS_LEAD2_FILE=$RECORD_WORK_FILE.output.gethrv-gqrs-lead2.txt
#GETHRV_ECGPU_LEAD1_FILE=$RECORD_WORK_FILE.output.gethrv-ecgpu-lead1.txt
#GETHRV_ECGPU_LEAD2_FILE=$RECORD_WORK_FILE.output.gethrv-ecgpu-lead2.txt

SAMPLES_FILE=$RECORD_WORK_FILE.output.samples.txt

# OUTPUTS (in data/)
WFDB_DESC_FILE=$RECORD_WORK_FILE.output.desc.txt

OUTPUT_FILE=$RECORD_WORK_FILE.output.gethrv-gqrs-lead1.verbose.txt
#OUTPUT_FILTERED_FILE=$RECORD_WORK_FILE.output-hrv.filtered.txt

OUTPUT_COMMANDS=$RECORD_WORK_FILE.output.cmds.txt
DATE=`date`
echo " -- ($DATE) -- Commands exectuted to calculate the HRV." > $OUTPUT_COMMANDS
echo " -- " >> $OUTPUT_COMMANDS


if [[ -e $RECORD_FILE_HEA &&
      -e $RECORD_FILE_DAT ]]; then
    echo "INFO: Record '$RECORD_ID' already calculated, do nothing."
    exit 0 
    fi

#echo ""
#echo " ---------------------------------------------------------"
#echo " * removing previous analyses..."
#echo " ---------------------------------------------------------"
#if [[ -e $RECORD_FILE_HEA ]]; then rm -vf $RECORD_FILE_HEA; fi 
#if [[ -e $RECORD_FILE_DAT ]]; then rm -vf $RECORD_FILE_DAT; fi 
#if [[ -e $ANN_GQRS_LEAD0_FILE ]]; then rm -vf $ANN_GQRS_LEAD0_FILE; fi 
#if [[ -e $ANN_GQRS_LEAD1_FILE ]]; then rm -vf $ANN_GQRS_LEAD1_FILE; fi 
#if [[ -e $ANN_ECGPU_LEAD0_FILE ]]; then rm -vf $ANN_ECGPU_LEAD0_FILE; fi 
#if [[ -e $ANN_ECGPU_LEAD1_FILE ]]; then rm -vf $ANN_ECGPU_LEAD1_FILE; fi 
#if [[ -e $RR_GQRS_LEAD0_FILE ]]; then rm -vf $RR_GQRS_LEAD0_FILE; fi 
#if [[ -e $RR_GQRS_LEAD1_FILE ]]; then rm -vf $RR_GQRS_LEAD1_FILE; fi 
#if [[ -e $RR_ECGPU_LEAD0_FILE ]]; then rm -vf $RR_ECGPU_LEAD0_FILE; fi 
#if [[ -e $RR_ECGPU_LEAD1_FILE ]]; then rm -vf $RR_ECGPU_LEAD1_FILE; fi 
#if [[ -e $OUTPUT_FILE ]]; then rm -vf $OUTPUT_FILE; fi 


echo ""
echo " * edf2mit... (Convert EDF to MIT format)"
echo " ---------------------------------------------------------"
edf2mit -i $EDF_FILE -r $RECORD_WORK_ID
echo "edf2mit -i $EDF_FILE -r $RECORD_WORK_ID" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: edf2mit"; exit 1; fi 

echo ""
echo " * wfdbdesc... (Describe freshly converted WFDB)"
echo " ---------------------------------------------------------"
wfdbdesc $RECORD_WORK_ID > $WFDB_DESC_FILE
echo "wfdbdesc $RECORD_WORK_ID > $WFDB_DESC_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: wfdbdesc failed"; exit 1; fi 

echo ""
echo " * rdsamp... (read samples to text)"
echo " ---------------------------------------------------------"
# -p: convert to sample unit (including time in sec)
# -P          same as -p, but with greater precision
# -v: print column headings
# -s X: only for one signals (we want them all)
# all samples in one files
rdsamp -r $RECORD_WORK_ID -P -v > $SAMPLES_FILE
echo "rdsamp -r $RECORD_WORK_ID -P -v > $SAMPLES_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: rdsamp lead 0"; exit 1; fi 

HAS_LEAD1=`wfdbsignals $RECORD_WORK_ID | grep '^leadI$' | wc -l`

HAS_LEAD2=`wfdbsignals $RECORD_WORK_ID | grep '^leadII$' | wc -l`

if [[ $HAS_LEAD1 -eq 0 ]]; then
    echo "ERROR: no 'leadI' in signals, cannot continue."
    exit 1
    fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    echo "Info: leadI and leadII signals are present, process both."
    fi

echo ""
echo " * gqrs..."
echo " ---------------------------------------------------------"
gqrs -r $RECORD_WORK_ID -o $ANN_GQRS_LEAD1 -s leadI 
echo "gqrs -r $RECORD_WORK_ID -o $ANN_GQRS_LEAD1 -s leadI" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: gqrs leadI"; exit 1; fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    gqrs -r $RECORD_WORK_ID -o $ANN_GQRS_LEAD2 -s leadII 
    echo "gqrs -r $RECORD_WORK_ID -o $ANN_GQRS_LEAD2 -s leadII" >> $OUTPUT_COMMANDS
    if [[ $? -ne 0 ]]; then echo "Error: gqrs leadII"; exit 1; fi 
    fi

# ECGPU is DISABLED
#echo ""
#echo " * ecgpu..."
#echo " ---------------------------------------------------------"
#ecgpuwave -r $RECORD_WORK_ID -a $ANN_ECGPU_LEAD1 -s 0 # 0: leadI
#if [[ $? -ne 0 ]]; then echo "Error: ecgpu leadI"; exit 1; fi 
#rm fort.20 fort.21
#if [[ $HAS_LEAD2 -eq 1 ]]; then
#    ecgpuwave -r $RECORD_WORK_ID -a $ANN_ECGPU_LEAD2 -s 1 # 1: leadII
#    if [[ $? -ne 0 ]]; then echo "Error: ecgpu leadII"; exit 1; fi 
#    fi


# format of the RR files:
# 3 columns (T, RR, A)
# 2 columns (RR, A)
# 2 columns (T, RR)
# 1 column (RR)
#
# where T is the time of occurrence of the beginning of the RR interval,
# RR is the duration of the RR interval, 
# and A is a beat label. 
# Normal sinus beats are labeled N.
#
# ann2rr and rrlist do not display the exact same list !!
#

echo ""
echo " * ann2rr to list RR in ms"
echo " ---------------------------------------------------------"
#
# -i FMT  print intervals using format FMT (see below for values of FMT)
# -V FMT  print times of beginnings of intervals using format FMT (see below)
# IMPORTANT: if '-p N'' => only NN intervals
#
ann2rr -r $RECORD_WORK_ID -a $ANN_GQRS_LEAD1 -V s -i s8 > $RR_GQRS_LEAD1_KUBIOS_FILE
echo "ann2rr -r $RECORD_WORK_ID -a $ANN_GQRS_LEAD1 -V s -i s8 > $RR_GQRS_LEAD1_KUBIOS_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: ann2rr leadI"; exit 1; fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    ann2rr -r $RECORD_WORK_ID -a $ANN_GQRS_LEAD2 -V s -i s8 > $RR_GQRS_LEAD2_KUBIOS_FILE
    echo "ann2rr -r $RECORD_WORK_ID -a $ANN_GQRS_LEAD2 -V s -i s8 > $RR_GQRS_LEAD2_KUBIOS_FILE" >> $OUTPUT_COMMANDS
    if [[ $? -ne 0 ]]; then echo "Error: ann2rr leadII"; exit 1; fi 
    fi

# ECGPU is DISABLED
#ann2rr -r $RECORD_WORK_ID -a $ANN_ECGPU_LEAD1 -V s -i s8 > $RR_ECGPU_LEAD1_KUBIOS_FILE
#if [[ $? -ne 0 ]]; then echo "Error: ecgpu leadI"; exit 1; fi 
#if [[ $HAS_LEAD2 -eq 1 ]]; then
#    ann2rr -r $RECORD_WORK_ID -a $ANN_ECGPU_LEAD2 -V s -i s8 > $RR_ECGPU_LEAD2_KUBIOS_FILE
#    if [[ $? -ne 0 ]]; then echo "Error: ecgpu leadII"; exit 1; fi 
#    fi

### NOTE: Filtering may not be used
###
### echo ""
### echo " * rrlist... (extract rr from GQRS and ECGPUS annotations)"
### echo " ---------------------------------------------------------"
### # for record-viewer (same rr tools as get_hrv is using)
### # rrlist
### # -s: use rrlist -s and format like:
### #       28.433 1.327 N
### # -t: time in sec (1st column)
### # -M: output intervals in msec
### #
### # ann2rr
### # By default, the output contains the RR intervals only
### 
### rrlist $ANN_GQRS_LEAD1 $RECORD_WORK_ID -s > $RR_GQRS_LEAD1_FILE
### if [[ $? -ne 0 ]]; then echo "Error: ann2rr lead 1"; exit 1; fi 
### rrlist $ANN_ECGPU_LEAD1 $RECORD_WORK_ID -s > $RR_ECGPU_LEAD1_FILE
### if [[ $? -ne 0 ]]; then echo "Error: ecgpu lead 0"; exit 1; fi 
### 
### echo ""
### echo " * filtnn... (filter RRs)"
### echo " ---------------------------------------------------------"
### 
### # filtnn:
### # -n : print ratio of nnout to nnin to rrin
### # -p : print excluded data at start/end of hwin buffer
### #
### # filt: 0.2 (=20%) min dist(?) | 20 samples before and after point | -x amplitude min and max
### #FILT="0.2 20 -x 0.4 2.0"
### FILT="0.5 5 -x 0.4 2.0"
### 
### cat $RR_GQRS_LEAD1_FILE | filtnn $FILT -p -n | sort -k 1n > $RR_FILT_GQRS_LEAD1_FILE
### if [[ $? -ne 0 ]]; then echo "Error: gqrs lead 1"; exit 1; fi 
### cat $RR_ECGPU_LEAD1_FILE | filtnn $FILT -p -n | sort -k 1n > $RR_FILT_ECGPU_LEAD1_FILE
### if [[ $? -ne 0 ]]; then echo "Error: ecgpu lead 1"; exit 1; fi 
### 
### 
### 
### echo ""
### echo " * awk to convert RR to Kubios.txt..."
### echo " ---------------------------------------------------------"
### 
### # non filtered
### cat $RR_GQRS_LEAD1_FILE | awk '// { if( $3 == "N" ) { print $1"\t"$2 } }' > $RR_GQRS_LEAD1_KUBIOS_FILE
### cat $RR_ECGPU_LEAD1_FILE | awk '// { if( $3 == "N" ) { print $1"\t"$2 } }' > $RR_ECGPU_LEAD1_KUBIOS_FILE
### 
### # filtered
### cat $RR_FILT_GQRS_LEAD1_FILE | awk '// { if( $3 == "N" ) { print $1"\t"$2 } }' > $RR_FILT_GQRS_LEAD1_KUBIOS_FILE
### cat $RR_FILT_ECGPU_LEAD1_FILE | awk '// { if( $3 == "N" ) { print $1"\t"$2 } }' > $RR_FILT_ECGPU_LEAD1_KUBIOS_FILE
### 


echo ""
echo " * get_hrv non-filtered..."
echo " ---------------------------------------------------------"

# -m: RR interval in msec
# -R: RR interval file (2 columns: time (sec), interval, N or ...))
# either -R or record name and annotation file -> BOTH GIVE IDENTICAL RESULTS
# -M: output statistics in msec rather than sec
# -f "filt hwin" : filter intervals
# -L: output stats on 1 line
# Here the "-F 0.2 20 -x 0.4 2.0" specifies the filtering parameters as follows. 
# First, any intervals less than 0.4 sec or greater than 2.0 sec are excluded.
# Next, using a window of 41 intervals (20 intervals on either side of the central point),
# the average over the window is calculated excluding the central interval.
# If the central interval lies outside 20% (0.2) of the window average this interval is flagged as an outlier and excluded. 
# Then the window is advanced to the next interval. These parameters can be adjusted as appropriate for different data sets.
#
# get_hrv -m  -M -f "0.2 20 -x 0.4 2.0" -p "50" data/work/b6eyerafh1w451d64vjrgfkb2 ann-ecgpu-s1
# or...
# get_hrv ... -f ... -p ... -R rr_file # but get_hrv do it nicely itself

#GET_HRV_OPTS="-L" # print in one line (but no info)

#
# Output one line 
#
get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD1 > $GETHRV_GQRS_LEAD1_FILE
echo "get_hrv -L -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD1 > $GETHRV_GQRS_LEAD1_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadI"; exit 1; fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD2 > $GETHRV_GQRS_LEAD2_FILE
    echo "get_hrv -L -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD2 > $GETHRV_GQRS_LEAD2_FILE" >> $OUTPUT_COMMANDS
    if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadII"; exit 1; fi 
    fi

# ECGPU is DISABLED
#get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD1 > $GETHRV_ECGPU_LEAD1_FILE
#if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadI"; exit 1; fi 
#if [[ $HAS_LEAD2 -eq 1 ]]; then
#    get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD2 > $GETHRV_ECGPU_LEAD2_FILE
#    if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadII"; exit 1; fi 
#    fi


#
# Output debug / verbose file
#
echo $DATE > $OUTPUT_FILE

echo "" >> $OUTPUT_FILE
echo "GQRS - LEAD I :" >> $OUTPUT_FILE
get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILE
echo "get_hrv -L -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadI"; exit 1; fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD2 >> $OUTPUT_FILE
    echo "get_hrv -L -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD2 >> $OUTPUT_FILE" >> $OUTPUT_COMMANDS
    if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadII"; exit 1; fi 
    fi

# ECGPU is DISABLED
#echo "" >> $OUTPUT_FILE
#echo "ECGPU - LEAD II :" >> $OUTPUT_FILE
#get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD1 >> $OUTPUT_FILE
#if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadI"; exit 1; fi 
#if [[ $HAS_LEAD2 -eq 1 ]]; then
#    get_hrv -L -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD2 >> $OUTPUT_FILE
#    if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadII"; exit 1; fi 
#    fi

echo "" >> $OUTPUT_FILE
echo "------------------------------------------------------" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "" >> $OUTPUT_FILE
echo "*** GQRS ***" >> $OUTPUT_FILE
echo " * LEAD I :" >> $OUTPUT_FILE
get_hrv -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILE
echo "get_hrv -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILE" >> $OUTPUT_COMMANDS
if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadI"; exit 1; fi 
if [[ $HAS_LEAD2 -eq 1 ]]; then
    echo " * LEAD II :" >> $OUTPUT_FILE
    get_hrv -m -M -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD2 >> $OUTPUT_FILE
    echo "get_hrv -m -M -p '50' $RECORD_WORK_ID $ANN_GQRS_LEAD2 >> $OUTPUT_FILE" >> $OUTPUT_COMMANDS
    if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs leadII"; exit 1; fi 
    fi

# ECGPU is DISABLED
#echo "" >> $OUTPUT_FILE
#echo "*** ECGPU ***" >> $OUTPUT_FILE
#echo " * LEAD I :" >> $OUTPUT_FILE
#get_hrv -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD1 >> $OUTPUT_FILE
#if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadI"; exit 1; fi 
#if [[ $HAS_LEAD2 -eq 1 ]]; then
#    echo " *  LEAD II :" >> $OUTPUT_FILE
#    get_hrv -m -M -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD2 >> $OUTPUT_FILE
#    if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu leadII"; exit 1; fi 
#    fi



### echo ""
### echo " * get_hrv filtered..."
### echo " ---------------------------------------------------------"
### 
### echo $DATE > $OUTPUT_FILTERED_FILE
### 
### echo "" >> $OUTPUT_FILTERED_FILE
### echo "GQRS - LEAD II :" >> $OUTPUT_FILTERED_FILE
### get_hrv -L -m -M -f "$FILT" -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILTERED_FILE
### if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs lead 1"; exit 1; fi 
### 
### echo "" >> $OUTPUT_FILTERED_FILE
### echo "ECGPU - LEAD II :" >> $OUTPUT_FILTERED_FILE
### get_hrv -L -m -M -f "$FILT" -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD1 >> $OUTPUT_FILTERED_FILE
### if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu lead 1"; exit 1; fi 
### 
### echo "" >> $OUTPUT_FILTERED_FILE
### echo "------------------------------------------------------" >> $OUTPUT_FILTERED_FILE
### echo "" >> $OUTPUT_FILTERED_FILE
### 
### echo "" >> $OUTPUT_FILTERED_FILE
### echo "GQRS - LEAD II :" >> $OUTPUT_FILTERED_FILE
### get_hrv -m -M -f "$FILT" -p "50" $RECORD_WORK_ID $ANN_GQRS_LEAD1 >> $OUTPUT_FILTERED_FILE
### if [[ $? -ne 0 ]]; then echo "Error: get_hrv gqrs lead 1"; exit 1; fi 
### 
### echo "" >> $OUTPUT_FILTERED_FILE
### echo "ECGPU - LEAD II :" >> $OUTPUT_FILTERED_FILE
### get_hrv -m -M -f "$FILT" -p "50" $RECORD_WORK_ID $ANN_ECGPU_LEAD1 >> $OUTPUT_FILTERED_FILE
### if [[ $? -ne 0 ]]; then echo "Error: get_hrv ecgpu lead 1"; exit 1; fi 
### 


echo ""
echo "done."
exit 0

