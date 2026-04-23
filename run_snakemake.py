#!/usr/bin/env python3
"""
Snakemake launcher for SND@LHC / AdvSND neutrino production.

Mirrors run_submit.py: reads the same YAML simulation configs, supports the
same CLI flags, and uses the same SNDSW_DIR / CONDOR_FOLDER environment
variables.  Instead of submitting a DAGMan job, it drives Snakemake with
--cluster mode so that individual HTCondor jobs are submitted per rule
execution, enabling per-job-index pipelining without waiting for a whole
stage to complete.

Usage:
    python run_snakemake.py --yaml simulation_configs/default_advtarget_2024.yaml --advsnd
    python run_snakemake.py --yaml simulation_configs/default_target_2024.yaml --flow all
    python run_snakemake.py --yaml simulation_configs/default_advtarget_14_2024.yaml \\
        --advsnd --njobs 1 --flow generate_input_file   # smoke test
    python run_snakemake.py --yaml simulation_configs/default_advtarget_14_2024.yaml \\
        --advsnd --dryrun                                # dry run, no HTCondor submission
"""
import argparse
import os
import sys
from pathlib import Path

import snakemake
import yaml

# ---------------------------------------------------------------------------
# Paths relative to this script
# ---------------------------------------------------------------------------

BASE_DIR       = Path(__file__).parent.resolve()
SNAKEMAKE_DIR  = BASE_DIR / "snakemake_production"
SNAKEFILE      = SNAKEMAKE_DIR / "Snakefile"
CLUSTER_CFG    = SNAKEMAKE_DIR / "cluster_config.yaml"
SUBMIT_SCRIPT  = SNAKEMAKE_DIR / "htcondor_submit.py"
RUNTIME_CONFIG = SNAKEMAKE_DIR / "config.yaml"

# ---------------------------------------------------------------------------
# Argument parsing (same two-pass YAML-aware approach as run_submit.py)
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    # Pass 1: extract --yaml so we can seed defaults from it.
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--yaml", type=Path,
                      help="YAML file with default arguments (CLI overrides YAML).")
    base_args, remaining = base.parse_known_args(argv)

    yaml_cfg: dict = {}
    if base_args.yaml is not None:
        with base_args.yaml.open() as f:
            yaml_cfg = yaml.safe_load(f) or {}

    def yget(key, default):
        return yaml_cfg.get(key, default)

    def ypath(key, default: Path) -> Path:
        if key in yaml_cfg and yaml_cfg[key] is not None:
            return Path(yaml_cfg[key])
        return default

    # Pass 2: full parser seeded with YAML-aware defaults.
    parser = argparse.ArgumentParser(
        description="Launch SND@LHC neutrino production via Snakemake + HTCondor.",
        parents=[base],
    )

    parser.add_argument("--tag", default=yget("tag", "2024/sndlhc_1500fb-1_fixed_flux"))
    parser.add_argument("--nevents", type=int, default=yget("nevents", 0))
    parser.add_argument(
        "--topvol",
        default=yget("topvol", "volMuFilter"),
        choices=["volMuFilter", "volTarget", "volAdvMuFilter", "volAdvTarget"],
    )
    parser.add_argument("--neutrino", type=int, default=yget("neutrino", 12))
    parser.add_argument("--eventgenlist", default=yget("eventgenlist", "Default"))
    parser.add_argument("--njobs", type=int, default=yget("njobs", 100))
    parser.add_argument("--colnum", type=float, default=yget("colnum", 1.1715e15))
    parser.add_argument("--year", default=yget("year", "2024"))
    parser.add_argument("--tune", default=yget("tune", "SNDG18_02a_01_000"))
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
    )
    parser.add_argument(
        "--outputdir",
        type=Path,
        default=ypath(
            "outputdir",
            Path("/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025"),
        ),
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
    )
    parser.add_argument("--advsnd", action="store_true",
                        help="Enable AdvSND simulation mode.")
    parser.add_argument(
        "--flow", type=str, nargs="+", default="standard",
        help=(
            "Stages to execute. Use 'standard' (default), 'all', or a custom list: "
            "--flow generate_input_file transport_neutrinos digitise"
        ),
    )
    parser.add_argument("--dryrun", action="store_true",
                        help="Dry run: print jobs that would be submitted without submitting.")

    return parser.parse_args(remaining)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_STAGES     = ["generate_input_file", "transport_neutrinos", "digitise", "analysis"]
DEFAULT_STAGES = ["generate_input_file", "transport_neutrinos", "digitise"]


def resolve_flow(flow_arg) -> list[str]:
    if flow_arg == "all":
        return ALL_STAGES
    if flow_arg == "standard" or flow_arg is None:
        return DEFAULT_STAGES
    # nargs='+' returns a list when multiple values are given, a single-item list otherwise.
    if isinstance(flow_arg, list):
        return flow_arg
    return [flow_arg]


def sentinel_targets(cfg: dict, stages: list[str]) -> list[str]:
    """Return the sentinel .done paths for every job index at the last stage."""
    tag          = cfg["tag"]
    neutrino     = cfg["neutrino"]
    topvol       = cfg["topvol"]
    njobs        = cfg["njobs"]
    condor_folder= cfg["condor_folder"]
    last_stage   = stages[-1]
    root = (
        Path(condor_folder)
        / "snakemake_sentinels"
        / tag
        / f"nu{neutrino}"
        / f"volume_{topvol}"
        / last_stage
    )
    return [str(root / f"{i}.done") for i in range(1, njobs + 1)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # Validate environment (same requirement as run_submit.py).
    sndsw_dir = os.environ.get("SNDSW_DIR")
    if not sndsw_dir:
        raise SystemExit(
            "ERROR: SNDSW_DIR is not set. "
            "Please source the SND@LHC environment before running this script."
        )

    condor_folder = os.environ.get("CONDOR_FOLDER") or str(BASE_DIR)

    # Validate mutual exclusivity of nevents / colnum.
    if args.nevents != 0 and args.colnum != 0:
        raise SystemExit(
            "ERROR: Set exactly one of --nevents / --colnum to 0 (not both non-zero)."
        )

    # Build Snakemake config dict.
    cfg = {
        "tag":           args.tag,
        "nevents":       args.nevents,
        "colnum":        f"{args.colnum:.6g}",
        "topvol":        args.topvol,
        "neutrino":      args.neutrino,
        "eventgenlist":  args.eventgenlist,
        "njobs":         args.njobs,
        "year":          args.year,
        "tune":          args.tune,
        "flukaflux":     str(args.flukaflux),
        "outputdir":     str(args.outputdir),
        "geofile":       str(args.geofile),
        "xsec":          str(args.xsec),
        "advsnd":        args.advsnd,
        "sndsw_dir":     sndsw_dir,
        "condor_folder": condor_folder,
    }

    # Write runtime config for the Snakefile.
    RUNTIME_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNTIME_CONFIG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    print(f"Wrote runtime config to {RUNTIME_CONFIG}")

    stages  = resolve_flow(args.flow)
    targets = sentinel_targets(cfg, stages)

    print(f"Flow: {' -> '.join(stages)}")
    print(f"Jobs: {args.njobs}  |  Targets: {len(targets)} sentinel files")
    if args.dryrun:
        print("Dry run mode: Snakemake will not submit any HTCondor jobs.")

    # --cluster command template — Snakemake substitutes {cluster.KEY} from cluster_config.yaml.
    # Snakemake v7 appends the jobscript path automatically at the end of the
    # cluster command — do NOT include {jobscript} here (it is unknown to the
    # rule template engine and causes a NameError).
    cluster_cmd = (
        f"python {SUBMIT_SCRIPT}"
        " --job-flavour {cluster.job_flavour}"
        " --requirements '{cluster.requirements}'"
        " --cpus {cluster.request_cpus}"
        " --accounting-group {cluster.accounting_group}"
        f" --log-dir {SNAKEMAKE_DIR / 'logs'}"
    )

    success = snakemake.snakemake(
        snakefile          = str(SNAKEFILE),
        configfiles        = [str(RUNTIME_CONFIG)],
        targets            = targets,
        cluster            = cluster_cmd if not args.dryrun else None,
        cluster_config     = str(CLUSTER_CFG),
        nodes              = args.njobs,
        latency_wait       = 60,
        restart_times      = 3,
        keepgoing          = True,
        printshellcmds     = True,
        dryrun             = args.dryrun,
        workdir            = str(BASE_DIR),
        jobname            = "snakejob.{rulename}.{jobid}.sh",
        max_jobs_per_second= 10,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
