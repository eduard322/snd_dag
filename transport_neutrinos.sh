#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
ADVSNDBUILD_DIR=/afs/cern.ch/user/o/olantwin/SND
source /cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/setUp.sh
source $ADVSNDBUILD_DIR/advsnd_geo_setup.sh

set -o nounset

OUTPUTFILE=sndLHC.Genie-TGeant4.root

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

EOSSERVER=root://eosuser.cern.ch/
OUTPUTDIR=/eos/user/o/olantwin/advsnd/2024/01/numu/$LSB_JOBINDEX
INPUT=$2

set -x

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUT ./$INPUT

python $SNDSW_ROOT/shipLHC/run_simSND.py --Genie 4 -f $INPUT --AdvSND

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
