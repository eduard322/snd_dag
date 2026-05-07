#!/usr/bin/env python3
"""
Convert FLUKA "new" format ROOT file to FLUKA "standard" (fort.30) text format.

Input: ROOT file produced by the fast-simulation converter, tree "nt", branches:
  run          always 0
  event        primary event number (float-encoded int)
  id           FLUKA particle type ID
  generation   generation number
  E            kinetic energy (GeV)
  w            statistical weight
  x            x coord at scoring plane (cm)
  y            y coord at scoring plane (cm)
  px           x direction cosine
  py           y direction cosine
  t            particle age (s)
  z            z coord at scoring plane (cm)
  lastdec_x/y/z/ID/E   last decay info
  lastint_x/y/z/ID/E   last interaction info
  origin       (ignored)

Output: standard fort.30 text format, 22 columns, preceded by a comment header:
  col  1  FLUKA run number            (int)
  col  2  primary event number        (int)
  col  3  FLUKA particle type ID      (int)
  col  4  generation number           (int)
  col  5  kinetic energy (GeV)        (float)
  col  6  statistical weight          (float)  ← ROOT branch w
  col  7  x coord (cm)                (float)
  col  8  y coord (cm)                (float)
  col  9  x direction cosine          (float)
  col 10  y direction cosine          (float)
  col 11  z coord (cm)                (float)  ← ROOT branch z
  col 12  particle age (s)            (float)
  col 13  last decay x (cm)           (float)
  col 14  last decay y (cm)           (float)
  col 15  last decay z (cm)           (float)
  col 16  last decay ID               (int)
  col 17  KE of decay parent (GeV)   (float)
  col 18  last interaction x (cm)    (float)
  col 19  last interaction y (cm)    (float)
  col 20  last interaction z (cm)    (float)
  col 21  last interaction ID        (int)
  col 22  KE of parent (GeV)         (float)

Usage:
    python convert_fluka_new_to_standard.py input.root output.txt
    python convert_fluka_new_to_standard.py input.root          # writes to stdout
"""

import sys
import argparse
import uproot

HEADER = """\
 # Scoring particles entering Region No         0
 # Col  1: FLUKA run number
 # Col  2: primary event number
 # -- Particle information --
 # Col  3: FLUKA particle type ID
 # Col  4: Generation number
 # Col  5: Kinetic energy (GeV)
 # Col  6: Statistical weight
 # -- Crossing at scoring plane --
 # Col  7: x coord (cm)
 # Col  8: y coord (cm)
 # Col  9: x dir cosine
 # Col 10: y dir cosine
 # Col 11: z coord (cm)
 # Col 12: Particle age since primary event (sec)
 # Col 13: Last decay x cooord (cm)
 # Col 14: Last decay y cooord (cm)
 # Col 15: Last decay z cooord (cm)
 # Col 16: Last decay ID
 # Col 17: Kinetic energy of decay parent (GeV)
 # Col 18: Last interaction x cooord (cm)
 # Col 19: Last interaction y cooord (cm)
 # Col 20: Last interaction z cooord (cm)
 # Col 21: Last interaction ID
 # Col 22: Kinetic energy of parent (GeV)
"""

BRANCHES = [
    "run", "event", "id", "generation",
    "E", "w", "x", "y", "px", "py", "t", "z",
    "lastdec_x", "lastdec_y", "lastdec_z", "lastdec_ID", "lastdec_E",
    "lastint_x", "lastint_y", "lastint_z", "lastint_ID", "lastint_E",
]


def fmt_int(value, width):
    return f"{int(value):>{width}d}"


def fmt_float(value):
    return f"{value:24.16E}"


def convert(root_path, outfile):
    with uproot.open(root_path) as f:
        tree = f["nt"]
        outfile.write(HEADER)
        for batch in tree.iterate(BRANCHES, step_size=100_000, library="np"):
            n = len(batch["run"])
            for i in range(n):
                parts = [
                    fmt_int(batch["run"][i],        5),   # col 1
                    fmt_int(batch["event"][i],      9),   # col 2
                    fmt_int(batch["id"][i],         5),   # col 3
                    fmt_int(batch["generation"][i], 4),   # col 4
                    fmt_float(batch["E"][i]),             # col 5
                    fmt_float(batch["w"][i]),             # col 6  statistical weight
                    fmt_float(batch["x"][i]),             # col 7
                    fmt_float(batch["y"][i]),             # col 8
                    fmt_float(batch["px"][i]),            # col 9
                    fmt_float(batch["py"][i]),            # col 10
                    fmt_float(batch["z"][i]),             # col 11  z coord
                    fmt_float(batch["t"][i]),             # col 12  particle age
                    fmt_float(batch["lastdec_x"][i]),     # col 13
                    fmt_float(batch["lastdec_y"][i]),     # col 14
                    fmt_float(batch["lastdec_z"][i]),     # col 15
                    fmt_int(batch["lastdec_ID"][i],  5),  # col 16
                    fmt_float(batch["lastdec_E"][i]),     # col 17
                    fmt_float(batch["lastint_x"][i]),     # col 18
                    fmt_float(batch["lastint_y"][i]),     # col 19
                    fmt_float(batch["lastint_z"][i]),     # col 20
                    fmt_int(batch["lastint_ID"][i],  5),  # col 21
                    fmt_float(batch["lastint_E"][i]),     # col 22
                ]
                outfile.write("".join(parts) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert FLUKA new-format ROOT file to standard fort.30 text format."
    )
    parser.add_argument("input", help="Input ROOT file (tree 'nt')")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output text file (default: stdout)",
    )
    args = parser.parse_args()

    if args.output:
        with open(args.output, "w") as outfile:
            convert(args.input, outfile)
    else:
        convert(args.input, sys.stdout)


if __name__ == "__main__":
    main()
