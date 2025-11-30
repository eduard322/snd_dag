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


import argparse
from pathlib import Path
import yaml

sndsw_dir = os.getenv("SNDSW_DIR")
if not sndsw_dir:  # None or empty string
    raise RuntimeError(
        "Environment variable SNDSW_DIR is not set or empty. "
        "Please source the SND@LHC environment before running this script."
    )
condor_dir = os.getenv("CONDOR_FOLDER")
if not condor_dir:  # None or empty string
    print("CONDOR_FOLDER is not set, using the current folder...")
    condor_dir = Path.cwd()

def parse_args(argv=None) -> argparse.Namespace:
    # --- Stage 1: parse only --yaml so we know if we should load a config file ---
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument(
        "--yaml",
        type=Path,
        help="YAML file with default arguments (CLI overrides YAML).",
    )
    base_args, remaining = base.parse_known_args(argv)

    yaml_cfg = {}
    if base_args.yaml is not None:
        with base_args.yaml.open() as f:
            yaml_cfg = yaml.safe_load(f) or {}

    # Helper to get value from YAML or fall back to given default
    def yget(key, default):
        return yaml_cfg.get(key, default)

    def ypath(key, default: Path) -> Path:
        if key in yaml_cfg and yaml_cfg[key] is not None:
            return Path(yaml_cfg[key])
        return default

    # --- Stage 2: full parser, seeded with YAML-aware defaults ---
    parser = argparse.ArgumentParser(
        description="Configure SND@LHC neutrino production HTCondor DAG submission.",
        parents=[base],
    )

    parser.add_argument(
        "--tag",
        default=yget("tag", "2024/sndlhc_1500fb-1_fixed_flux"),
        help="Tag used to label this production (stored under TAG).",
    )
    parser.add_argument(
        "--nevents",
        type=int,
        default=yget("nevents", 0),
        help="Number of events per job (NEVENTS).",
    )
    parser.add_argument(
        "--topvol",
        default=yget("topvol", "volMuFilter"),
        choices=["volMuFilter", "volTarget", "volAdvMuFilter", "volAdvTarget"],
        help="Top volume where neutrino interactions are generated (TOPVOL).",
    )
    parser.add_argument(
        "--neutrino",
        type=int,
        default=yget("neutrino", 12),
        help="Neutrino PDG code (NEUTRINO).",
    )
    parser.add_argument(
        "--eventgenlist",
        default=yget("eventgenlist", "Default"),
        help="GENIE event generator list (EVENTGENLIST).",
    )
    parser.add_argument(
        "--njobs",
        type=int,
        default=yget("njobs", 100),
        help="Number of Condor jobs to submit (NJOBS).",
    )
    parser.add_argument(
        "--colnum",
        type=float,
        default=yget("colnum", 1.1715e15),
        help="Number of pp collisions to normalize to (COLNUM).",
    )
    parser.add_argument(
        "--year",
        default=yget("year", "2024"),
        help="Data-taking year (YEAR).",
    )
    parser.add_argument(
        "--tune",
        default=yget("tune", "SNDG18_02a_01_000"),
        help="GENIE tune name (TUNE).",
    )
    parser.add_argument(
        "--flukaflux",
        type=Path,
        default=ypath(
            "flukaflux",
            Path(
                "/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/"
                "ALL_lhc_ir1_coll_2024_1p585mm_xrp_exp001_fort.30_FIXED.gsimple.root"
            ),
        ),
        help="Input FLUKA/gsimple flux file (FLUKAFLUX).",
    )
    parser.add_argument(
        "--outputdir",
        type=Path,
        default=ypath(
            "outputdir",
            Path(
                "/eos/experiment/sndlhc/users/ursovsnd/"
                "neutrino_production_sndlhc_june_2025"
            ),
        ),
        help="Base EOS output directory (OUTPUTDIR).",
    )
    parser.add_argument(
        "--geofile",
        type=Path,
        default=ypath(
            "geofile",
            Path(
                "/eos/user/u/ursovsnd/neutrino_production_sndlhc_june_2025/"
                "output_geo_geant.gdml"
            ),
        ),
        help="Base gmdl geometry file (GEOFILE).",
    )
    parser.add_argument(
        "--xsec",
        type=Path,
        default=ypath(
            "xsec",
            Path(
                "/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/splines/"
                "genie_splines_GENIE_v32_SNDG18_02a_01_000.xml"
            ),
        ),
        help="GENIE splines (XSEC).",
    )

    parser.add_argument(
        "--advsnd",
        action="store_true",
        help="enable advsnd simulation",
    )



    return parser.parse_args(remaining)


def build_vars_from_args(args: argparse.Namespace) -> dict:
    """Convert parsed args back into the VARS dict used by the DAG scripts."""
    VARS = {
        "ADVSND": args.advsnd,
        "TAG": args.tag,
        "NEVENTS": str(args.nevents),
        "TOPVOL": args.topvol,
        "NEUTRINO": str(args.neutrino),
        "EVENTGENLIST": args.eventgenlist,
        "NJOBS": str(args.njobs),
        "COLNUM": f"{args.colnum:.6g}",  # keep scientific notation if you like
        "YEAR": args.year,
        "TUNE": args.tune,
        "FLUKAFLUX": str(args.flukaflux),
        "OUTPUTDIR": str(args.outputdir),
        "GEOFILE": str(args.geofile),
        "XSEC": str(args.xsec),
    }
    return VARS


args = parse_args()
VARS = build_vars_from_args(args)

if int(VARS["NEVENTS"]) != 0 and int(VARS["COLNUM"]) != 0:
    raise Exception("Choose either collision number or the exact number of events, not both. Set one of the values to 0.")
# add SNDSW_DIR to VARS
VARS["SNDSW_DIR"] = str(sndsw_dir)
# add CONDOR_FOLDER to VARS
VARS["CONDOR_FOLDER"] = str(condor_dir)
print(VARS)
# def write_readme(vars_dict: dict) -> None:
#     """
#     Write README.md into OUTPUTDIR / TAG with the simulation parameters.
#     Follows the template style given by the user.
#     """
#     output_base = Path(vars_dict["OUTPUTDIR"])
#     tag = vars_dict["TAG"]
#     pdg = vars_dict["NEUTRINO"]
#     topvol = vars_dict["TOPVOL"]

#     out_dir = output_base / tag / f"nu{pdg}" / f"volume_{topvol}"
#     out_dir.mkdir(parents=True, exist_ok=True)

#     # Map to template-style variable names
#     run_tag = tag
#     events_per_job = vars_dict["NEVENTS"]
#     output_dir = str(out_dir)
#     log_dir = os.path.join(str(out_dir), "logs")  # typical pattern, adjust if needed
#     expected_lumi = (float(vars_dict["COLNUM"])*int(vars_dict["NJOBS"])/78.1)*1e-12
#     # Fill in your template style, but with fields relevant to this production
#     readme_content = f"""# Simulation Parameters
# - advsnd: {vars_dict["ADVSND"]}
# - run_tag: {run_tag}
# - njobs: {vars_dict["NJOBS"]}
# - neutrino_pdg: {vars_dict["NEUTRINO"]}
# - eventgenlist: {vars_dict["EVENTGENLIST"]}
# - top_volume: {vars_dict["TOPVOL"]}
# - collisions_normalization per file (COLNUM): {vars_dict["COLNUM"]}
# - year: {vars_dict["YEAR"]}
# - tune: {vars_dict["TUNE"]}
# - fluka_flux_file: {vars_dict["FLUKAFLUX"]}
# - GENIE spline file: {vars_dict["XSEC"]}
# - output_dir: {output_dir}
# - simulated luminosity: {expected_lumi} fb-1 (L = number_pp_collisions / sigma)
# """
#     print(readme_content)
#     readme_path = out_dir / "README.md"
#     with open(readme_path, "w") as f:
#         f.write(readme_content)

from pathlib import Path
import os

def write_readme(vars_dict: dict) -> None:
    """
    Write README.md into OUTPUTDIR / TAG with the simulation parameters.
    Follows the template style given by the user.
    """
    output_base = Path(vars_dict["OUTPUTDIR"])
    tag = vars_dict["TAG"]
    pdg = vars_dict["NEUTRINO"]
    topvol = vars_dict["TOPVOL"]

    out_dir = output_base / tag / f"nu{pdg}" / f"volume_{topvol}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Map to template-style variable names
    run_tag = tag
    events_per_job = int(vars_dict["NEVENTS"]) / int(vars_dict["NJOBS"])
    output_dir = str(out_dir)
    log_dir = os.path.join(str(out_dir), "logs")  # typical pattern, adjust if needed
    expected_lumi = (float(vars_dict["COLNUM"]) * int(vars_dict["NJOBS"]) / 78.1) * 1e-12

    # Decide which description to use: collisions_normalization vs events
    colnum_is_zero = float(vars_dict["COLNUM"]) == 0.0
    if events_per_job != 0 and colnum_is_zero:
        collisions_or_events_line = f"- number of events per file: {events_per_job}\n"
        lumi_or_events_line = f"- simulated number of events: {vars_dict['NEVENTS']}\n"
    else:
        collisions_or_events_line = (
            f"- collisions_normalization per file (COLNUM): {vars_dict['COLNUM']}\n"
        )
        lumi_or_events_line = (
            f"- simulated luminosity: {expected_lumi} fb-1 (L = number_pp_collisions / sigma)\n"
        )

    # Fill in your template style, but with fields relevant to this production
    readme_content = (
        f"# Simulation Parameters\n"
        f"- advsnd: {vars_dict['ADVSND']}\n"
        f"- run_tag: {run_tag}\n"
        f"- njobs: {vars_dict['NJOBS']}\n"
        f"- neutrino_pdg: {vars_dict['NEUTRINO']}\n"
        f"- eventgenlist: {vars_dict['EVENTGENLIST']}\n"
        f"- top_volume: {vars_dict['TOPVOL']}\n"
        f"{collisions_or_events_line}"
        f"- year: {vars_dict['YEAR']}\n"
        f"- tune: {vars_dict['TUNE']}\n"
        f"- fluka_flux_file: {vars_dict['FLUKAFLUX']}\n"
        f"- GENIE spline file: {vars_dict['XSEC']}\n"
        f"- output_dir: {output_dir}\n"
        f"{lumi_or_events_line}"
    )

    print(readme_content)
    readme_path = out_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)


write_readme(VARS)


PRE_SKIP_CODE = 2
DAG_NAME = "all.dag"
DOT_PATH = "dag.dot"

base = Path(VARS["CONDOR_FOLDER"]).resolve()
tag_suffix = VARS["TAG"].split("/")[-1]
neutrino = VARS["NEUTRINO"]
dag_dir = base / f"dag_{tag_suffix}" / f"nu{neutrino}" / VARS["TOPVOL"]

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
