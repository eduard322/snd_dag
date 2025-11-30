#!/usr/bin/env bash
set -o errexit -o pipefail -o noclobber

# Set up SND environment

source $8/config.sh "$@"
set -o nounset


ProcId=$1
LSB_JOBINDEX=$((ProcId+1))
SEED=$LSB_JOBINDEX


set -x

if xrdfs $EOSSERVER stat $OUTPUTDIR/$OUTPUTFILE_GEN; then
	echo "Target exists, nothing to do."
	exit 0
fi



echo $SNDSW_ROOT

#gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
#    -g $GEOFILE \
#    -t $TOPVOLUME \
#    -L "cm" \
#    -D "g_cm3" \
#    -e $COL_NUMBER \
#    -o $(basename $OUTPUTFILE_GEN .0.ghep.root) \
#    --tune $TUNE \
#    --cross-sections $XSECTION \
#    --event-generator-list $EVENTGENLIST \
#    --message-thresholds $GENIE/config/Messenger_laconic.xml \
#    --seed $SEED
#    #-z -3 \
    #-m $MPL


# if [ "${NEVENTS:-0}" -eq 0 ]; then
#   gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
#       -g "$GEOFILE" \
#       -t "$TOPVOLUME" \
#       -L "cm" \
#       -D "g_cm3" \
#       -e "$COL_NUMBER" \
#       -o "$(basename "$OUTPUTFILE_GEN" .0.ghep.root)" \
#       --tune "$TUNE" \
#       --cross-sections "$XSECTION" \
#       --event-generator-list "$EVENTGENLIST" \
#       --message-thresholds "$GENIE/config/Messenger_laconic.xml" \
#       --seed "$SEED"
# else
#   gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
#       -g "$GEOFILE" \
#       -t "$TOPVOLUME" \
#       -L "cm" \
#       -D "g_cm3" \
#       -n "$NEVENTS" \
#       -o "$(basename "$OUTPUTFILE_GEN" .0.ghep.root)" \
#       --tune "$TUNE" \
#       --cross-sections "$XSECTION" \
#       --event-generator-list "$EVENTGENLIST" \
#       --message-thresholds "$GENIE/config/Messenger_laconic.xml" \
#       --seed "$SEED"
# fi

Z_FLAG=""
if [ "${16}" = "True" ]; then
  Z_FLAG="-z 0"
fi

if [ "${NEVENTS:-0}" -eq 0 ]; then
  gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
      -g "$GEOFILE" \
      -t "$TOPVOLUME" \
      -L "cm" \
      -D "g_cm3" \
      -e "$COL_NUMBER" \
      -o "$(basename "$OUTPUTFILE_GEN" .0.ghep.root)" \
      --tune "$TUNE" \
      --cross-sections "$XSECTION" \
      --event-generator-list "$EVENTGENLIST" \
      --message-thresholds "$GENIE/config/Messenger_laconic.xml" $Z_FLAG \
      --seed "$SEED"
else
  gevgen_fnal -f "$FLUX,,-$NEUTRINO,$NEUTRINO" \
      -g "$GEOFILE" \
      -t "$TOPVOLUME" \
      -L "cm" \
      -D "g_cm3" \
      -n "$NEVENTS" \
      -o "$(basename "$OUTPUTFILE_GEN" .0.ghep.root)" \
      --tune "$TUNE" \
      --cross-sections "$XSECTION" \
      --event-generator-list "$EVENTGENLIST" \
      --message-thresholds "$GENIE/config/Messenger_laconic.xml" $Z_FLAG \
      --seed "$SEED"
fi


OUTPUTGST=$(basename $OUTPUTFILE_GEN .ghep.root).gst.root


#echo "DOING SOMETHING"
gntpc -i $OUTPUTFILE_GEN -f gst -o $OUTPUTGST -c
addAuxiliaryToGST $OUTPUTFILE_GEN $OUTPUTGST

xrdcp *ghep.root $EOSSERVER/$OUTPUTDIR/$OUTPUTFILE_GEN
xrdcp *gst.root $EOSSERVER/$OUTPUTDIR/$OUTPUTGST
