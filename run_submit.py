#!/usr/bin/env python3
from pathlib import Path
import htcondor

# API name changed in newer releases (htcondor2). Try the current one first.
try:
    from htcondor import dags
except Exception:
    from htcondor2 import dags  # fallback for newer installs


# "TOPVOL": "volMuFilter"
# ---- user knobs (from your DAG) ----
VARS = {
    "TAG": "2024/sndlhc_1500fb-1_NC_1",
    "NEVENTS": "100",
    "TOPVOL": "volTarget",
    "NEUTRINO": "14",
    "EVENTGENLIST": "NC",
    "NJOBS": "1000",
    "COLNUM": "1.1715e14",
    "CONDOR_FOLDER": "/afs/cern.ch/user/u/ursovsnd/neutrino/neutrino_production_sndlhc_june_2025/nusim_automation_new_dag",
    "YEAR": "2024",
    "TUNE": "SNDG18_02a_01_000",
    "OUTPUTDIR": "/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025"
}
PRE_SKIP_CODE = 2
DAG_NAME = "all.dag"
DOT_PATH = "dag.dot"

base = Path(VARS["CONDOR_FOLDER"]).resolve()

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

# Write DAG description (and any generated submit files if you had htcondor.Submit objects)
dagfile_path = dags.write_dag(dag, dag_dir=base, dag_file_name=DAG_NAME)
print(f"Wrote DAG to: {dagfile_path}")

schedd = htcondor.Schedd()
submit_desc = htcondor.Submit.from_dag(str(dagfile_path))

# --- New API: use Schedd.submit() ---
res = schedd.submit(submit_desc)  # replaces transaction()+queue()
# Make this robust across versions (SubmitResult vs int)
try:
    cluster_id = res.cluster()
except AttributeError:
    cluster_id = int(res)

print(f"Submitted DAGMan job: cluster {cluster_id}")
