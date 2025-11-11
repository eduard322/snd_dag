ADVSNDBUILD_DIR="/afs/cern.ch/user/u/ursovsnd/SND"

# Environment setup
source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Jan30/setUp.sh
eval "$(alienv load sndsw/latest --work-dir ${15} --no-refresh)"

# Positional arguments
ProcId="$1"
COL_NUMBER="$3"
NEUTRINO="$5"
EVENTGENLIST="$6"
TAG="$7"
YEAR="$9"
TUNE="${10}"
FLUX="${11}"
OUTPUTDIR="${12}"
GEOFILE="${13}"
# Geometry / volume setup
TOPVOLUME="+$4"
OUTPUT_PREFIX="${TAG}/nu${NEUTRINO}/volume_$4"

LSB_JOBINDEX=$((ProcId + 1))
OUTPUTDIR="${OUTPUTDIR}/${OUTPUT_PREFIX}/${LSB_JOBINDEX}"

# File names for each stage
OUTPUTFILE_GEN="sndlhc_${TOPVOLUME}_SND_LHC_${TUNE}.0.ghep.root"
INPUTFILE_TRANSP="$(basename "${OUTPUTFILE_GEN}" .ghep.root).gst.root"
OUTPUTFILE_TRANSP="sndLHC.Genie-TGeant4.root"
INPUTFILE_DIGI="${OUTPUTFILE_TRANSP}"
OUTPUTFILE_DIGI="$(basename "${INPUTFILE_DIGI}" .root)_dig.root"

# EOS and geometry files
EOSSERVER="root://eosuser.cern.ch/"
export FAIRSHIP="${FAIRSHIP_ROOT}"
GEOFILE_GEANT4="geofile_full.Genie-TGeant4.root"

# Cross-section and flux
XSECTION="${14}"


