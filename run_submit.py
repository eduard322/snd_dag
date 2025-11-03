#!/usr/bin/env python3
from pathlib import Path
import htcondor
import os
import shutil

# API name changed in newer releases (htcondor2). Try the current one first.
try:
    from htcondor import dags
except Exception:
    from htcondor2 import dags  # fallback for newer installs


# "TOPVOL": "volMuFilter", "volTarget"
# 1000 jobs * 1.1715e14 = 1500 fb-1
# BEWARE: CURRENT SETUP IS TUNED TO SIMULATE THE NUMBER EVENTS THAT CORRESPOND TO THE EXPECTED LUMINOSITY: GENIE SAMPLES THIS NUMBER ACCORDING TO THE COLLISION NUMBER
# AND FLUKA FILE YOU ENTER AS AN INPUT. IF YOU WANT TO SIMULATE THE EXACT NUMBER OF EVENTS, CHECK generate_input_file.sh script.
# ---- user knobs (from your DAG) ----
VARS = {
    "TAG": "2024/sndlhc_1500fb-1_CC_fixed_flux",
    "NEVENTS": "100",
    "TOPVOL": "volMuFilter",
    "NEUTRINO": "12",
    "EVENTGENLIST": "CC",
    "NJOBS": "100",
    "COLNUM": "1.1715e15",
    "CONDOR_FOLDER": "/afs/cern.ch/user/u/ursovsnd/neutrino/neutrino_production_sndlhc_june_2025/nusim_automation_new_dag",
    "YEAR": "2024",
    "TUNE": "SNDG18_02a_01_000",
    "FLUKAFLUX": "/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/ALL_lhc_ir1_coll_2024_1p585mm_xrp_exp001_fort.30_FIXED.gsimple.root",
    "OUTPUTDIR": "/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025"
}
PRE_SKIP_CODE = 2
DAG_NAME = "all.dag"
DOT_PATH = "dag.dot"

base = Path(VARS["CONDOR_FOLDER"]).resolve()
tag_suffix = VARS["TAG"].split("/")[-1]
dag_dir = base / f"dag_{tag_suffix}" / VARS["TOPVOL"]

# CLEAN first, then recreate dag_dir
shutil.rmtree(dag_dir, ignore_errors=True)
dag_dir.mkdir(parents=True, exist_ok=True)

#print(f"Creating a dag directory dag_{VARS['TAG'].split('/')[-1]}...")
#dag_dir = base / f"dag_{VARS['TAG'].split('/')[-1]}"
#dag_dir.mkdir(parents=True, exist_ok=True)

#DAG_NAME =  dag_dir / DAG_NAME
#DOT_PATH =  dag_dir / DOT_PATH
# Point to your existing submit files on disk (we reuse them as-is)
sub_generate  = base / "generate_input_file.sub"
sub_transport = base / "transport_neutrinos.sub"
sub_digitise  = base / "digitise.sub"

# One logical node per layer (vars is a list; one dict == one underlying node)
node_vars = [VARS]

# DOT config like:  DOT dag.dot UPDATE
dot_cfg = dags.DotConfig(path=DOT_PATH, update=True)

dag = dags.DAG(dot_config=dot_cfg)

# Nodes (layers), each with PRE_SKIP behavior
gen = dag.layer(
    name="generate_input_file",
    submit_description=sub_generate,
    vars=node_vars,
    dir=base,                       # submit from your workflow folder
    pre_skip_exit_code=PRE_SKIP_CODE,
)
trn = gen.child_layer(
    name="transport_neutrinos",
    submit_description=sub_transport,
    vars=node_vars,
    dir=base,
    pre_skip_exit_code=PRE_SKIP_CODE,
)
dig = trn.child_layer(
    name="digitise",
    submit_description=sub_digitise,
    vars=node_vars,
    dir=base,
    pre_skip_exit_code=PRE_SKIP_CODE,
)
print(dag.describe())

# blow away any old files
#shutil.rmtree(dag_dir, ignore_errors = True)

# make the magic happen!
#dag_file = dags.write_dag(dag, dag_dir, dag_file_name=DAG_NAME)
#dag_submit = htcondor.Submit.from_dag(str(dag_file), {'force': 1})

#print(dag_submit)

#os.chdir(dag_dir)

#schedd = htcondor.Schedd()
#cluster_id = schedd.submit(dag_submit).cluster()

#print(f"DAGMan job cluster is {cluster_id}")

#os.chdir('..')

dag_file = dags.write_dag(dag, dag_dir=dag_dir, dag_file_name=DAG_NAME)

# Change cwd BEFORE building the Submit from the DAG (mimics condor_submit_dag)
os.chdir(dag_dir)

dag_submit = htcondor.Submit.from_dag(str(dag_file))
# Optional: if you use Kerberos creds
# Push your Kerberos ticket to the credd (uses your current kinit cache)
credd = htcondor.Credd()
credd.add_user_cred(htcondor.CredTypes.Kerberos, None)
dag_submit["MY.SendCredential"] = "True"
dag_submit["getenv"] = "True"
schedd = htcondor.Schedd()
res = schedd.submit(dag_submit)
cluster_id = getattr(res, "cluster", lambda: int(res))()
print(f"DAGMan job cluster is {cluster_id}")
