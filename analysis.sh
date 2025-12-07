#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment

source $8/config.sh "$@"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30//sw//slc9_x86-64/pythia/sndsw-pythia8309-local1/lib
set -o nounset

INPUTFILE=$INPUTFILE_DIGI
GEOFILE=$GEOFILE_GEANT4
#OUTPUTFILE=$(basename $INPUTFILE .root)_dig.root

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))



set -x

# if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE_DIGI; then
# 	echo "Target exists, nothing to do."
# 	exit 0
# fi

xrdcp $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_DIGI ./$OUTPUTFILE_DIGI


python $8/image_creator.py -j 4 --inputfiles $OUTPUTFILE_DIGI -o image.root

# # Temporarily turn off -e so we don't abort
# set +o errexit

# python "$SNDSW_ROOT/shipLHC/run_digiSND.py" -f "$INPUTFILE" -g "$GEOFILE" -cpp \
#     || echo "⚠️ digi step failed, but continuing..."

# # Re-enable -e for the rest of your script (if you still want it)
# set -o errexit

#echo "Checking..."
#mv "${INPUTFILE%.root}_digCPP.root" "$OUTPUTFILE_DIGI"
#xrdcp "$OUTPUTFILE" "$OUTPUTDIR"/.
xrdcp image.root $EOSSERVER/$OUTPUTDIR/image.root

