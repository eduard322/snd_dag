#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
source /afs/cern.ch/user/o/olantwin/SND/nusim_automation/config.sh

set -o nounset

INPUTFILE=sndLHC.Genie-TGeant4.root
GEOFILE=geofile_full.Genie-TGeant4.root
OUTPUTFILE=$(basename $INPUTFILE .root)_dig.root

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX/$LSB_JOBINDEX

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE; then
	echo "Target exists, nothing to do."
	exit 0
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUTFILE ./$INPUTFILE
xrdcp $EOSSERVER/$OUTPUTDIR/$GEOFILE ./$GEOFILE

python $SNDSW_ROOT/shipLHC/run_digiSND.py -f $INPUTFILE -g $GEOFILE -cpp
mv $(basename $INPUTFILE .root)_digCPP.root $OUTPUTFILE

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
