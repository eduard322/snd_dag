#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
source /afs/cern.ch/user/o/olantwin/SND/nusim_automation/config.sh

set -o nounset

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

INPUT=$2
OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX/$LSB_JOBINDEX
OUTPUT=$(basename $INPUT .ghep.root).gst.root

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUT; then
	echo "Target exists, nothing to do."
	exit 0
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUT ./$INPUT

gntpc -i $INPUT -f gst -o $OUTPUT -c
addAuxiliaryToGST $INPUT $OUTPUT

xrdcp $OUTPUT $EOSSERVER/$OUTPUTDIR/$OUTPUT
