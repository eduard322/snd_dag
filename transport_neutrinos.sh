#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment

source $8/config.sh "$@"


export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30//sw//slc9_x86-64/pythia/sndsw-pythia8309-local1/lib

set -o nounset


INPUT=$INPUTFILE_TRANSP
ProcId=$1
LSB_JOBINDEX=$((ProcId+1))

set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE_TRANSP; then
	if [ "${RESIMULATE:-False}" = "True" ]; then
		echo "WARNING: output $OUTPUTDIR/$OUTPUTFILE_TRANSP already exists — deleting for resimulation."
		xrdfs $EOSSERVER rm $OUTPUTDIR/$OUTPUTFILE_TRANSP
	else
		echo "Target exists, nothing to do."
		exit 0
	fi
fi

xrdcp $EOSSERVER/$OUTPUTDIR/$INPUT ./$INPUT

if [[ ! -f "$INPUT" ]]; then
  echo "ERROR: File '$INPUT' not found." >&2
  return 1
fi

# ask ROOT in batch mode to print the number of entries in gst
N=$(root -l -b <<EOF
TFile *f = TFile::Open("${INPUT}");
if (!f) {
  std::cerr << "Failed to open file '${INPUT}'\n";
  exit(1);
}
TTree *t = (TTree*)f->Get("gst");
if (!t) {
  std::cerr << "Tree 'gst' not found in file\n";
  exit(1);
}
std::cout << t->GetEntries() << "\n";
.q
EOF
)

# check that N is numeric
if ! [[ $N =~ ^[0-9]+$ ]]; then
  echo "ERROR: could not extract a valid entry count (got: '$N')" >&2
  return 1
fi

echo "Found $N events in gst → launching python with -n $N"


# if [ "${16}" = "True" ]; then
#   python $SNDSW_ROOT/shipLHC/run_simSND.py --Genie 4 -f $INPUT --nEvents $N -y $YEAR
# fi
if [ "${16}" = "True" ]; then
  python "$SNDSW_ROOT"/shipLHC/run_simSND.py \
    --Genie 4 -f "$INPUT" --nEvents "$N" --AdvSND
else
  python "$SNDSW_ROOT"/shipLHC/run_simSND.py \
    --Genie 4 -f "$INPUT" --nEvents "$N" -y "$YEAR"
fi


# Validate cbmsim TTree in transport output before copying to EOS
python3 -c "
import sys, ROOT
ROOT.gROOT.SetBatch(True)
fname = '$OUTPUTFILE_TRANSP'
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

xrdcp $OUTPUTFILE_TRANSP $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_TRANSP
xrdcp $GEOFILE_GEANT4 $EOSSERVER/$OUTPUTDIR/$GEOFILE_GEANT4
