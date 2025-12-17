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
* To set up parameters of the simulation, check `simulation_configs/default_target_2024.yaml` file.
* To launch simulation, one has to specify `$SNDSW_DIR` and `$CONDOR_FOLDER` in `system_config.sh` file and launch it `source system_config.sh`
* To generate `.gdml` geometry file, use `python create_geo_config.py --from_config --year 2024`. See flags in the file. 
* `python run_submit.py --yaml simulation_configs/default_target_2024.yaml` or manually set info: `python3 run_submit.py --tag 2022/sndlhc_1500fb-1_up --topvol volMuFilter --neutrino 14 --year 2022 --flukaflux /eos/experiment/sndlhc/MonteCarlo/FLUKA/neutrino_up_13TeV/all13TeVK0_gsimple.root`
* This script will generate a dedicated folder with DAG instructions and logs for HTCondor DAG run. Logs for each subjob is stored in `logs/` directory.
* If you want to simulate SND@HL-LHC, then just add --advsnd flag to the `run_submit.py`: `run_submit.py --yaml simulation_configs/advtarget_14_2024.yaml --advsnd`.
* Set the steps you want to launch by `--flow` key: `run_submit.py --yaml simulation_configs/your_config.yaml --flow generate_input_file transport digitise`. Write step by step the names of the `.sub` files you would like to launch. To launch the hardcoded pipeline of ["generate_input_file", "transport", "digitise", "analysis"] use `--flow all`.
* You can choose the exact number of events to simulate or the number of pp collisions to simulate. See yaml configs.
## Verifying the number of files

* `ls -la $OUTPUT_FOLDER$/nu12/volume_volMuFilter/*/sndLHC.Genie-TGeant4_dig.root | wc -l`
* Check if the `GENIE` simulation works: `source local_generate_input.py`.
## Current limitations

* A lot of variables need to be kept in synch across jobs an scripts. How to avoid this?
* DAG needs the entire step to complete. Any way to have Child B of Parent A run on subjobs?
