#!/usr/bin/env python3
"""
Check EOS output files for valid TTrees.

Opens each expected ROOT output file directly over xrootd, verifies the
named TTree exists and has at least one entry, and reports bad files.
With --delete, removes bad files from EOS via xrdfs rm.

Usage:
    python check_output_files.py --yaml simulation_configs/default_advtarget_14_2024.yaml \
        --advsnd --stages transport digitise --jobs 1-100
    python check_output_files.py --yaml simulation_configs/default_advtarget_14_2024.yaml \
        --advsnd --delete
    python check_output_files.py --yaml simulation_configs/default_advtarget_14_2024.yaml \
        --advsnd --stages generate --jobs 1-5,10,50-55
"""
import argparse
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Stage -> [(filename_or_callable, treename), ...]
# ---------------------------------------------------------------------------

def _gen_ghep(cfg):
    return f"sndlhc_+{cfg['topvol']}_SND_LHC_{cfg['tune']}.0.ghep.root"

def _gen_gst(cfg):
    return f"sndlhc_+{cfg['topvol']}_SND_LHC_{cfg['tune']}.0.gst.root"

STAGE_CHECKS = {
    "generate":  [(_gen_ghep, "gtree"), (_gen_gst, "gst")],
    "transport": [("sndLHC.Genie-TGeant4.root",          "cbmsim")],
    "digitise":  [("sndLHC.Genie-TGeant4_dig.root", "cbmsim")],
}

EOSSERVER = "root://eosuser.cern.ch/"

# ---------------------------------------------------------------------------
# Argument parsing (two-pass YAML-aware, same pattern as run_submit.py)
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--yaml", type=Path)
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

    parser = argparse.ArgumentParser(
        description="Check EOS output files for valid TTrees.",
        parents=[base],
    )
    parser.add_argument("--tag",      default=yget("tag", ""))
    parser.add_argument("--neutrino", type=int, default=yget("neutrino", 14))
    parser.add_argument("--topvol",   default=yget("topvol", "volTarget"),
                        choices=["volMuFilter", "volTarget", "volAdvMuFilter", "volAdvTarget"])
    parser.add_argument("--tune",     default=yget("tune", "SNDG18_02a_01_000"))
    parser.add_argument("--njobs",    type=int, default=yget("njobs", 100))
    parser.add_argument("--outputdir", type=Path,
                        default=ypath("outputdir", Path("/eos/experiment/sndlhc/users/ursovsnd")))
    parser.add_argument("--advsnd", action="store_true",
                        default=bool(yget("advsnd", False)))
    parser.add_argument(
        "--stages", nargs="+",
        default=["generate", "transport", "digitise"],
        choices=list(STAGE_CHECKS.keys()),
        help="Which stages to check (default: generate transport digitise).",
    )
    parser.add_argument(
        "--jobs", default=None,
        help=(
            "Job indices to check. Accepts ranges and comma lists, e.g. "
            "'1-100,250,300-310'. Default: 1-{njobs}."
        ),
    )
    parser.add_argument("--delete", action="store_true",
                        help="Delete bad files from EOS (requires valid Kerberos token).")
    parser.add_argument("--parallel", type=int, default=16,
                        help="Number of parallel ROOT file checks (default: 8).")

    return parser.parse_args(remaining)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_job_indices(spec: str, njobs: int) -> list[int]:
    """Parse a range/comma spec like '1-100,250,300-310' into a sorted list."""
    indices = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            indices.update(range(int(lo), int(hi) + 1))
        else:
            indices.add(int(part))
    return sorted(indices)


def eos_jobdir(outputdir: str, tag: str, neutrino: int, topvol: str, job_idx: int) -> str:
    return f"{outputdir}/{tag}/nu{neutrino}/volume_{topvol}/{job_idx}"


def check_file(xrd_url: str, treename: str) -> tuple[str, str]:
    """
    Open a ROOT file over xrootd and validate the named TTree.
    Returns (status, detail) where status is "OK", "MISSING", "CORRUPT", or "BAD".
    """
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kError

    f = ROOT.TFile.Open(xrd_url)
    if not f or f.IsZombie():
        return "MISSING", "cannot open file"
    t = f.Get(treename)
    if not t or not isinstance(t, ROOT.TTree):
        return "CORRUPT", f"no TTree '{treename}'"
    n = int(t.GetEntries())
    f.Close()
    if n == 0:
        return "BAD", f"'{treename}' has 0 entries"
    return "OK", f"'{treename}' has {n} entries"


def xrdfs_rm(eosserver: str, eos_path: str) -> bool:
    """Delete a file via xrdfs rm. Returns True on success."""
    result = subprocess.run(
        ["xrdfs", eosserver.rstrip("/"), "rm", eos_path],
        capture_output=True, text=True,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if not args.tag:
        raise SystemExit("ERROR: --tag is required (or set in YAML).")

    job_indices = (
        parse_job_indices(args.jobs, args.njobs)
        if args.jobs
        else list(range(1, args.njobs + 1))
    )

    cfg = {
        "topvol": args.topvol,
        "tune":   args.tune,
    }

    # Build work list: (job_idx, stage, filename, treename, xrd_url, eos_path)
    work = []
    outputdir = str(args.outputdir)
    for job_idx in job_indices:
        jobdir = eos_jobdir(outputdir, args.tag, args.neutrino, args.topvol, job_idx)
        for stage in args.stages:
            for fname_or_fn, treename in STAGE_CHECKS[stage]:
                filename = fname_or_fn(cfg) if callable(fname_or_fn) else fname_or_fn
                eos_path = f"{jobdir}/{filename}"
                xrd_url  = f"{EOSSERVER}{eos_path}"
                work.append((job_idx, stage, filename, treename, xrd_url, eos_path))

    n_files  = len(work)
    n_stages = len(args.stages)
    print(
        f"Checking {len(job_indices)} jobs × {n_stages} stage(s) "
        f"({n_files} file checks) on {EOSSERVER}..."
    )
    if args.delete:
        print("--delete is set: bad files will be removed from EOS.")

    # Run checks in parallel
    results = {}  # (job_idx, stage, filename) -> (status, detail)
    with ProcessPoolExecutor(max_workers=args.parallel) as pool:
        future_map = {
            pool.submit(check_file, xrd_url, treename): (job_idx, stage, filename, eos_path)
            for job_idx, stage, filename, treename, xrd_url, eos_path in work
        }
        for future in as_completed(future_map):
            job_idx, stage, filename, eos_path = future_map[future]
            try:
                status, detail = future.result()
            except Exception as exc:
                status, detail = "CORRUPT", str(exc)
            results[(job_idx, stage, filename)] = (status, detail, eos_path)

    # Print sorted results (only non-OK)
    bad_items = []
    for key in sorted(results):
        job_idx, stage, filename = key
        status, detail, eos_path = results[key]
        if status != "OK":
            stage_col = f"{stage:<10}"
            print(f"[job {job_idx:>5} / {stage_col}] {status:<7}  {eos_path} — {detail}")
            bad_items.append((status, eos_path))

    # Summary
    counts = {"MISSING": 0, "BAD": 0, "CORRUPT": 0}
    for status, _ in bad_items:
        counts[status] = counts.get(status, 0) + 1
    total_bad = len(bad_items)
    print(
        f"\nSummary: {total_bad} bad file(s) found "
        f"({counts['MISSING']} MISSING, {counts['BAD']} BAD, {counts['CORRUPT']} CORRUPT)"
        f" out of {n_files} checked."
    )

    if total_bad == 0 or not args.delete:
        sys.exit(0 if total_bad == 0 else 1)

    # Delete bad files
    print()
    deleted = 0
    eosserver_host = EOSSERVER.rstrip("/").replace("root://", "")
    for status, eos_path in bad_items:
        if status == "MISSING":
            print(f"SKIP (already missing): {eos_path}")
            continue
        print(f"Deleting {eos_path} ... ", end="", flush=True)
        ok = xrdfs_rm(eosserver_host, eos_path)
        if ok:
            print("OK")
            deleted += 1
        else:
            print("FAILED")

    print(f"\nDeleted {deleted}/{total_bad - counts['MISSING']} file(s).")
    sys.exit(0 if deleted == (total_bad - counts["MISSING"]) else 1)


if __name__ == "__main__":
    main()
