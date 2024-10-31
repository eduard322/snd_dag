#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
source /afs/cern.ch/user/o/olantwin/SND/nusim_automation/config.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30//sw//slc9_x86-64/pythia/sndsw-pythia8309-local1/lib

set -o nounset

OUTPUTFILE=sndLHC.Genie-TGeant4.root

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX/$LSB_JOBINDEX
INPUT=$2
NEVENTS=$3

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE; then
	echo "Target exists, nothing to do."
	exit 0
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUT ./$INPUT

python $ADVSNDSW_ROOT/shipLHC/run_simSND.py --Genie 4 -f $INPUT --AdvSND --nEvents $NEVENTS

xrdcp $OUTPUTFILE $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE
xrdcp geofile_full.Genie-TGeant4.root $EOSSERVER/$OUTPUTDIR/geofile_full.Genie-TGeant4.root
