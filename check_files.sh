#!/usr/bin/env bash
source config.sh
set -o errexit -o pipefail -o noclobber -o nounset
set -x

JOB=$1
NEVENTS=500000 # pass from dag?
NJOBS=1000
NEVENTSPERJOB=$((NEVENTS / NJOBS))

EOSSERVER=root://eospublic.cern.ch/
#OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX
OUTPUTDIR=/eos/experiment/sndlhc/users/ursovsnd/advsnd/$OUTPUT_PREFIX
#exit 3
case "${JOB}" in
	generate_input_file) OUTPUTFILE="sndlhc_+volAdvMuFilter_"$NEVENTSPERJOB"_ADVSNDG18_02a_01_000.0.ghep.root";;
	convert_ghep_gst) OUTPUTFILE="sndlhc_+volAdvMuFilter_"$NEVENTSPERJOB"_ADVSNDG18_02a_01_000.0.gst.root";;
	transport_neutrinos) OUTPUTFILE=sndLHC.Genie-TGeant4.root;;
	digitise) OUTPUTFILE=sndLHC.Genie-TGeant4_dig.root;;
	pat_rec) OUTPUTFILE=sndLHC.Genie-TGeant4_dig_PR.root;;
	*) echo "Unknown JOB $JOB"; exit 1;;
esac

echo "OUTPUTFILE format for JOB $JOB : $OUTPUTFILE"
# Temporarily disable errexit so we can handle no-match gracefully
set +e
count=$( ls "$OUTPUTDIR"/*/"$OUTPUTFILE" 2>/dev/null | wc -l )
set -e
#if [ "$NJOBS" -eq "$(ls $OUTPUTDIR/*/$OUTPUTFILE | wc -l)" ]; then
#	echo "All targets exist, nothing to do for $JOB."
#	exit 2
#fi

echo "Found $count of $NJOBS expected files for $JOB."
#exit 3
if [ "$count" -eq "$NJOBS" ]; then
    echo "All targets exist, nothing to do for $JOB."
    exit 3
fi

exit 0
