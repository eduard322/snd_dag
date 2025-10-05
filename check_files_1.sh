#!/usr/bin/env bash
source config.sh
set -o errexit -o pipefail -o noclobber -o nounset
set -x

JOB=$1
NEVENTS=500000 # pass from dag?
NJOBS=1000
NEVENTSPERJOB=$((NEVENTS / NJOBS))

EOSSERVER=root://eosuser.cern.ch/
#OUTPUTDIR=/eos/experiment/sndlhc/users/olantwin/advsnd/$OUTPUT_PREFIX
OUTPUTDIR=/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025/$OUTPUT_PREFIX

case "${JOB}" in
	generate_input_file) OUTPUTFILE="sndlhc_+volTarget_"$NEVENTSPERJOB"_SND_LHC_G18_02a_01_000.0.ghep.root";;
	convert_ghep_gst) OUTPUTFILE="sndlhc_+volTarget_"$NEVENTSPERJOB"_SND_LHC_G18_02a_01_000.0.gst.root";;
	transport_neutrinos) OUTPUTFILE=sndLHC.Genie-TGeant4.root;;
	digitise) OUTPUTFILE=sndLHC.Genie-TGeant4_dig.root;;
	pat_rec) OUTPUTFILE=sndLHC.Genie-TGeant4_dig_PR.root;;
	*) echo "Unknown JOB $JOB"; exit 1;;
esac

echo "OUTPUTFILE format for JOB $JOB : $OUTPUTFILE"

if [ "$NJOBS" -eq "$(ls $OUTPUTDIR/*/$OUTPUTFILE | wc -l)" ]; then
	echo "All targets exist, nothing to do for $JOB."
	exit 2
fi

exit 0
