#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber -o nounset

GEOFILE="/afs/cern.ch/user/o/olantwin/SND/geofile.050124.gdml"
MPL="/afs/cern.ch/user/o/olantwin/SND/mpl.xml"
XSECTION="/afs/cern.ch/user/o/olantwin/public/genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2.xml"
FLUX="/afs/cern.ch/user/o/olantwin/public/HL-LHC_neutrinos_TI18_20e6pr_gsimple.root"
NEVENTS=$3
OUTPUTDIR=
TUNE=SNDG18_02a_01_000
EVENTGENLIST=CCDIS
TOPVOLUME="+volAdvTarget"
OUTPUTFILE="sndlhc_"$TOPVOLUME"_"$NEVENTS"_ADV"$TUNE".0.ghep.root"
NEUTRINO=14

ProcId=$2
LSB_JOBINDEX=$((ProcId+1))
SEED=$LSB_JOBINDEX

EOSSERVER=root://eosuser.cern.ch/
OUTPUTDIR=/eos/user/o/olantwin/advsnd/2024/01/numu/$LSB_JOBINDEX

gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
    -g $GEOFILE \
    -t $TOPVOLUME \
    -L "cm" \
    -D "g_cm3" \
    -n $NEVENTS \
    -o $OUTPUTFILE \
    --tune $TUNE \
    --cross-sections $XSECTION \
    --message-thresholds $GENIE/config/Messenger_laconic.xml \
    --seed $SEED \
    -z -2 \
    --event-generator-list $EVENTGENLIST \
    -m $MPL

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
