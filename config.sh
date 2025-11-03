#TAG=2025/sndlhc_1500fb-1_CC_1
#TAG=2025/11_test_low_CC_no_logs
ADVSNDBUILD_DIR=/afs/cern.ch/user/u/ursovsnd/SND
source /cvmfs/sndlhc.cern.ch/SNDLHC-2025/Jan30/setUp.sh
#source /afs/cern.ch/user/u/ursovsnd/neutrino/pythia_flux/nusim_automation/env_cleanup.sh
eval $(alienv load sndsw/latest --work-dir /afs/cern.ch/user/u/ursovsnd/SND/sw  --no-refresh)


#OUTPUTDIR=/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025
OUTPUTDIR=${12}
TUNE=${10}

#TUNE=SNDG18_02a_01_000
XSECTION="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/splines/genie_splines_GENIE_v32_SNDG18_02a_01_000.xml"
#FLUX="/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/ALL_lhc_ir1_coll_2024_1p585mm_xrp_exp001_fort.30.gsimple.root"
FLUX=${11}



COL_NUMBER=$3
YEAR=$9
NEUTRINO=$5
EVENTGENLIST=$6
TAG=$7
OUTPUT_PREFIX=$TAG/nu$NEUTRINO/volume_$4
ProcId=$1
LSB_JOBINDEX=$((ProcId+1))
OUTPUTDIR=$OUTPUTDIR/$OUTPUT_PREFIX/$LSB_JOBINDEX

TOPVOLUME="+$4"
OUTPUTFILE_GEN="sndlhc_"$TOPVOLUME"_SND_LHC_"$TUNE".0.ghep.root"
INPUTFILE_TRANSP=$(basename $OUTPUTFILE_GEN .ghep.root).gst.root
OUTPUTFILE_TRANSP=sndLHC.Genie-TGeant4.root
INPUTFILE_DIGI=$OUTPUTFILE_TRANSP
OUTPUTFILE_DIGI=$(basename $INPUTFILE_DIGI .root)_dig.root

EOSSERVER=root://eosuser.cern.ch/
export FAIRSHIP=$FAIRSHIP_ROOT
GEOFILE_GEANT4=geofile_full.Genie-TGeant4.root
GEOFILE="/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/output_geo_geant.gdml"
