#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment
#source /afs/cern.ch/user/u/ursovsnd/neutrino/pythia_flux/nusim_automation/config.sh
#source /afs/cern.ch/user/u/ursovsnd/neutrino/neutrino_production_sndlhc_june_2025/nusim_automation_new_dag/config.sh
source $8/config.sh "$@"
set -o nounset

#FILEDIR="$EOSSERVER/eos/experiment/sndlhc/users/olantwin/advsnd"
#MPL="/afs/cern.ch/work/d/dannc/public/AdvSND/2024/auxiliary/mympl_plus.xml"
#XSECTION="/afs/cern.ch/work/d/dannc/public/AdvSND/2024/splines/genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2_plus.xml"
#XSECTION="/afs/cern.ch/work/d/dannc/public/AdvSND/2024/splines/genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2_plus2.xml"
#XSECTION="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/splines/genie_splines_GENIE_v32_SNDG18_02a_01_000.xml"
#FLUX="/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/ALL_lhc_ir1_coll_2024_1p585mm_xrp_exp001_fort.30.gsimple.root"
# FLUX="$FILEDIR/HL-LHC_neutrinos_TI18_20e6pr_gsimple.root"
#FLUX="/eos/experiment/sndlhc/MonteCarlo/AdvSND/TP_2025/nu_tau_force_decay/output_nutau_1.0.gst.root"
#FLUX="/eos/experiment/sndlhc/users/ursovsnd/genie_input/20b_no_bias.gsimple.root"

#TUNE=SNDG18_02a_01_000




#TOPVOLUME="+volTarget"
# NEUTRINO=$5
# EVENTGENLIST=$6
# TAG=$7
# OUTPUT_PREFIX=$TAG/nu$NEUTRINO/volume_$4
# TOPVOLUME="+$4"
# OUTPUTFILE="sndlhc_"$TOPVOLUME"_SND_LHC_"$TUNE".0.ghep.root"

ProcId=$1
LSB_JOBINDEX=$((ProcId+1))
SEED=$LSB_JOBINDEX

#OUTPUTDIR=/eos/experiment/sndlhc/users/ursovsnd/advsnd/$OUTPUT_PREFIX/$LSB_JOBINDEX
#OUTPUTDIR=/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025/$OUTPUT_PREFIX/$LSB_JOBINDEX
#OUTPUTDIR=$OUTPUTDIR/$OUTPUT_PREFIX/$LSB_JOBINDEX
set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE_GEN; then
	echo "Target exists, nothing to do."
	exit 0
fi

#xrdcp $XSECTION .

#XSECTION="genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2_plus2.xml"

#xrdcp $MPL .

#MPL="mympl_plus.xml"

echo $SNDSW_ROOT 

gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
    -g $GEOFILE \
    -t $TOPVOLUME \
    -L "cm" \
    -D "g_cm3" \
    -e $COL_NUMBER \
    -o $(basename $OUTPUTFILE_GEN .0.ghep.root) \
    --tune $TUNE \
    --cross-sections $XSECTION \
    --event-generator-list $EVENTGENLIST \
    --message-thresholds $GENIE/config/Messenger_laconic.xml \
    --seed $SEED
    #-z -3 \
    #--event-generator-list $EVENTGENLIST \
    #-m $MPL

#echo "Too much" > _condor_stdout

OUTPUTGST=$(basename $OUTPUTFILE_GEN .ghep.root).gst.root


#echo "DOING SOMETHING"
gntpc -i $OUTPUTFILE_GEN -f gst -o $OUTPUTGST -c
addAuxiliaryToGST $OUTPUTFILE_GEN $OUTPUTGST

xrdcp *ghep.root $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_GEN
xrdcp *gst.root $EOSSERVER/$OUTPUTDIR/$OUTPUTGST
