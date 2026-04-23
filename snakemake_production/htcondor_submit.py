#!/usr/bin/env python3
"""
HTCondor submit wrapper for snakemake --cluster.

Snakemake (v7) calls this script once per rule execution:

    python htcondor_submit.py \\
        --job-flavour tomorrow \\
        --requirements "(OpSysAndVer =?= \"AlmaLinux9\")" \\
        --cpus 1 \\
        --accounting-group group_u_SNDLHC.users \\
        --log-dir /path/to/logs \\
        /path/to/snakejob.rulename.jobid.sh

This script submits the jobscript as a single HTCondor job and prints
"<ClusterId>.0" to stdout. Snakemake captures that string as the external
job ID for its internal bookkeeping (no --cluster-status needed: the
GenericClusterExecutor appends .jobfinished/.jobfailed marker logic to the
jobscript automatically, and Snakemake polls those local files).
"""
import argparse
import os
import sys

import htcondor


def parse_args():
    p = argparse.ArgumentParser(description="Submit a Snakemake jobscript to HTCondor.")
    p.add_argument("--job-flavour", default="tomorrow",
                   help="HTCondor +JobFlavour value (e.g. tomorrow, longlunch).")
    p.add_argument("--requirements", default="",
                   help="HTCondor requirements expression (empty string = no requirement).")
    p.add_argument("--cpus", type=int, default=1,
                   help="RequestCpus value.")
    p.add_argument("--accounting-group", default="group_u_SNDLHC.users",
                   help="+AccountingGroup value.")
    p.add_argument("--log-dir", default=None,
                   help="Directory for HTCondor .out/.err/.log files.")
    p.add_argument("jobscript",
                   help="Path to the Snakemake-generated bash jobscript.")
    return p.parse_args()


def main():
    args = parse_args()
    jobscript = os.path.abspath(args.jobscript)

    log_dir = args.log_dir or os.path.join(os.path.dirname(jobscript), "logs")
    os.makedirs(log_dir, exist_ok=True)

    sub_dict = {
        "executable":            jobscript,
        "output":                os.path.join(log_dir, "$(ClusterId).$(ProcId).out"),
        "error":                 os.path.join(log_dir, "$(ClusterId).$(ProcId).err"),
        "log":                   os.path.join(log_dir, "$(ClusterId).$(ProcId).log"),
        "request_cpus":          str(args.cpus),
        "+JobFlavour":           f'"{args.job_flavour}"',
        "+AccountingGroup":      f'"{args.accounting_group}"',
        "MY.SendCredential":     "True",
        "getenv":                "True",
        "transfer_output_files": '""',
        "notification":          "Never",
    }

    if args.requirements.strip():
        sub_dict["requirements"] = args.requirements

    sub = htcondor.Submit(sub_dict)

    # Forward Kerberos credential so workers can access AFS and EOS.
    try:
        credd = htcondor.Credd()
        credd.add_user_cred(htcondor.CredTypes.Kerberos, None)
    except Exception as exc:
        print(f"[htcondor_submit] Warning: could not push Kerberos cred: {exc}",
              file=sys.stderr)

    schedd = htcondor.Schedd()
    result = schedd.submit(sub, count=1)
    cluster_id = result.cluster()

    # Snakemake reads the first token on stdout as the external job ID.
    print(f"{cluster_id}.0")


if __name__ == "__main__":
    main()
