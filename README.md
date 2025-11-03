# Neutrino simulation automation

Files to run SND@LHC and AdvSND neutrino simulation (and maybe other simulations later?) in a reliable and reproducible way.

## Goals

* Reliable
* Reproducible
* Runnable by non-experts
* Only rerun failed jobs
* Only upload output of successful jobs

## How to run

* `run_submit.py` creates the HTCondor DAG instruction with a lot of options. See the possible keys in the script.
* To set up parameters, check `config.sh` file where one has to change the path to the folder of `sndsw` that one has on their system.
* `python run_submit.py`

## Verifying the number of files

* `ls -la $OUTPUT_FOLDER$/nu12/volume_volMuFilter/*/sndLHC.Genie-TGeant4_dig.root | wc -l`

## Current limitations

* A lot of variables need to be kept in synch across jobs an scripts. How to avoid this?
* DAG needs the entire step to complete. Any way to have Child B of Parent A run on subjobs?
