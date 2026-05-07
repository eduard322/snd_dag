# Environment setup
# All variables are received as named environment variables set by the HTCondor
# submit file's `environment` stanza (JOBINDEX, ADVSND, SNDSW_DIR, TOPVOL, …).

ADV_VARIABLE=""
if [ "$ADVSND" = "True" ]; then
  ADV_VARIABLE="adv"
  source /cvmfs/sndlhc.cern.ch/SNDLHC-2024/June25/setUp.sh
  eval "$(alienv load ${ADV_VARIABLE}sndsw/latest --work-dir "$SNDSW_DIR" --no-refresh)"
else
  source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Nov24/setUp.sh
  eval "$(alienv load ${ADV_VARIABLE}sndsw/latest --work-dir "$SNDSW_DIR" --no-refresh)"
fi

if [ "$ADVSND" = "True" ]; then
  SNDSW_ROOT=$ADVSNDSW_ROOT
fi

# Named environment variables → internal names used by stage scripts
ProcId="$JOBINDEX"
NEVENTS="$NEVENTS_PER_JOB"
COL_NUMBER="$COLNUM"
FLUX="$FLUKAFLUX"
XSECTION="$XSEC"
RESIMULATE="${RESIMULATE:-False}"

# Geometry / volume setup
TOPVOLUME="+$TOPVOL"
OUTPUT_PREFIX="${TAG}/nu${NEUTRINO}/volume_${TOPVOL}"

LSB_JOBINDEX=$((ProcId + 1))
OUTPUTDIR="${OUTPUTDIR}/${OUTPUT_PREFIX}/${LSB_JOBINDEX}"

# File names for each stage
OUTPUTFILE_GEN="sndlhc_${TOPVOLUME}_SND_LHC_${TUNE}.0.ghep.root"
INPUTFILE_TRANSP="$(basename "${OUTPUTFILE_GEN}" .ghep.root).gst.root"
OUTPUTFILE_TRANSP="sndLHC.Genie-TGeant4.root"
INPUTFILE_MCEB="${OUTPUTFILE_TRANSP}"
OUTPUTFILE_MCEB="$(basename "${INPUTFILE_MCEB}" .root)_MCEB.root"
if [ "$ADVSND" = "True" ]; then
  INPUTFILE_DIGI="${OUTPUTFILE_TRANSP}"
else
  INPUTFILE_DIGI="${OUTPUTFILE_MCEB}"
fi
OUTPUTFILE_DIGI="$(basename "${INPUTFILE_DIGI}" .root)_dig.root"

# EOS and geometry files
EOSSERVER="root://eosuser.cern.ch/"
export FAIRSHIP="${FAIRSHIP_ROOT}"
GEOFILE_GEANT4="geofile_full.Genie-TGeant4.root"
