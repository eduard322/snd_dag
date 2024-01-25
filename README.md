# Neutrino simulation automation

Files to run SND@LHC and AdvSND neutrino simulation (and maybe other simulations later?) in a reliable and reproducible way.

## Goals

* Reliable
* Reproducible
* Runnable by non-experts
* Only rerun failed jobs
* Only upload output of successful jobs

## How to run

* Run all steps (skip completed steps): `condor_submit_dag all.dag`
* Run a particular step: `condor_submit <step>.sub`
* Check how many output files exist: `./check_files <step>` (used by the DAG to skip completed steps)

## Current limitations

* A lot of variables need to be kept in synch across jobs an scripts. How to avoid this?
* DAG needs the entire step to complete. Any way to have Child B of Parent A run on subjobs?
