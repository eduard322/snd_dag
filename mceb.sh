#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment

source $8/config.sh "$@"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30//sw//slc9_x86-64/pythia/sndsw-pythia8309-local1/lib
set -o nounset

INPUTFILE=$INPUTFILE_MCEB
GEOFILE=$GEOFILE_GEANT4

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE_MCEB; then
	if [ "${RESIMULATE:-False}" = "True" ]; then
		echo "WARNING: output $OUTPUTDIR/$OUTPUTFILE_MCEB already exists — deleting for resimulation."
		xrdfs $EOSSERVER rm $OUTPUTDIR/$OUTPUTFILE_MCEB
	else
		echo "Target exists, nothing to do."
		exit 0
	fi
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUTFILE ./$INPUTFILE
xrdcp $EOSSERVER/$OUTPUTDIR/$GEOFILE ./$GEOFILE

# Temporarily turn off -e so we don't abort
set +o errexit

# python "$SNDSW_ROOT/shipLHC/run_digiSND.py" -f "$INPUTFILE" -g "$GEOFILE" -cpp \
#     || echo "⚠️ digi step failed, but continuing..."


python $SNDSW_ROOT/shipLHC/run_MCEventBuilder.py -f "$INPUTFILE" -g "$GEOFILE" --saveFirst25nsOnly -o "$OUTPUTFILE_MCEB" \
    || echo "⚠️ MCEventBuilder step failed, but continuing..."

# Re-enable -e for the rest of your script (if you still want it)
set -o errexit

echo "Checking..."
# mv "${INPUTFILE%.root}_digCPP.root" "$OUTPUTFILE_MCEB"

# Validate cbmsim TTree in digitise output before copying to EOS
python3 -c "
import sys, ROOT
ROOT.gROOT.SetBatch(True)
fname = '$OUTPUTFILE_MCEB'
f = ROOT.TFile.Open(fname)
if not f or f.IsZombie():
    print('ERROR: cannot open ' + fname, file=sys.stderr); sys.exit(1)
t = f.Get('cbmsim')
if not t or not isinstance(t, ROOT.TTree):
    print('ERROR: no TTree cbmsim in ' + fname, file=sys.stderr); sys.exit(1)
n = t.GetEntries()
if n == 0:
    print('ERROR: cbmsim has 0 entries in ' + fname, file=sys.stderr); sys.exit(1)
print(f'OK: cbmsim has {n} entries in ' + fname)
"

#xrdcp "$OUTPUTFILE" "$OUTPUTDIR"/.
xrdcp $OUTPUTFILE_MCEB $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_MCEB

