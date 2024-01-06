#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber -o nounset

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

INPUT=$2
EOSSERVER=root://eosuser.cern.ch/
OUTPUTDIR=/eos/user/o/olantwin/advsnd/2024/01/numu/$LSB_JOBINDEX
OUTPUT=$(basename $INPUT .ghep.root).gst.root

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUT ./$INPUT

gntpc -i $INPUT -f gst -o $OUTPUT -c
addAuxiliaryToGST $INPUT $OUTPUT

xrdcp $OUTPUT $EOSSERVER/$OUTPUTDIR/$OUTPUT
