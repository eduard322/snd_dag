#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
ADVSNDBUILD_DIR=/afs/cern.ch/user/o/olantwin/SND
source /cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/setUp.sh
source $ADVSNDBUILD_DIR/advsnd_digi_setup.sh

set -o nounset

INPUTFILE=sndLHC.Genie-TGeant4_dig.root
GEOFILE=geofile_full.Genie-TGeant4.root
OUTPUTFILE=$(basename $INPUTFILE .root)_PR.root

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

EOSSERVER=root://eospublic.cern.ch/
OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/2024/01/numu/$LSB_JOBINDEX

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE; then
	echo "Target exists, nothing to do."
	exit 0
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUTFILE ./$INPUTFILE
xrdcp $EOSSERVER/$OUTPUTDIR/$GEOFILE ./$GEOFILE

python $ADVSNDBUILD_DIR/advsnd_scripts/pat_rec.py -f $EOSSERVER/$OUTPUTDIR/$INPUTFILE -g $EOSSERVER/$OUTPUTDIR/$GEOFILE -o $OUTPUTFILE &> /dev/null

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
