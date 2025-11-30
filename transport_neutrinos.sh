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
	echo "Target exists, nothing to do."
	exit 0
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
    --Genie 4 -f "$INPUT" --nEvents "$N" --year "$YEAR"
fi


xrdcp $OUTPUTFILE_TRANSP $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_TRANSP
xrdcp $GEOFILE_GEANT4 $EOSSERVER/$OUTPUTDIR/$GEOFILE_GEANT4
