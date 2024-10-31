#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
source /afs/cern.ch/user/o/olantwin/SND/nusim_automation/config.sh

set -o nounset

FILEDIR="$EOSSERVER/eos/experiment/sndlhc/users/olantwin/advsnd"
MPL="$FILEDIR/mpl.xml"
XSECTION="$FILEDIR/genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2.xml"
FLUX="$FILEDIR/HL-LHC_neutrinos_TI18_20e6pr_gsimple.root"
NEVENTS=$2
TUNE=SNDG18_02a_01_000
TOPVOLUME="+volAdvTarget"
OUTPUTFILE="sndlhc_"$TOPVOLUME"_"$NEVENTS"_ADV"$TUNE".0.ghep.root"

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))
SEED=$LSB_JOBINDEX

OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX/$LSB_JOBINDEX

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE; then
	echo "Target exists, nothing to do."
	exit 0
fi

xrdcp $XSECTION .

XSECTION="genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2.xml"

xrdcp $MPL .

MPL="mpl.xml"

gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
    -g $GEOFILE \
    -t $TOPVOLUME \
    -L "cm" \
    -D "g_cm3" \
    -n $NEVENTS \
    -o $(basename $OUTPUTFILE .0.ghep.root) \
    --tune $TUNE \
    --cross-sections $XSECTION \
    --message-thresholds $GENIE/config/Messenger_laconic.xml \
    --seed $SEED \
    -z -3 \
    --event-generator-list $EVENTGENLIST \
    -m $MPL

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
