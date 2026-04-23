#!/usr/bin/env python3
"""
Convert FLUKA "new" format to FLUKA "standard" (fort.30) format.

New format  (23 whitespace-separated columns, no header):
  col  1  run number          (always 0.0)
  col  2  event number        (float, e.g. 1.0, 2.0, ...)
  col  3  particle type ID    (always 6.0)
  col  4  generation          (always 1.0)
  col  5  kinetic energy (GeV)
  col  6  y coord at scoring plane (cm)  -- fixed, e.g. -17.644
  col  7  x coord (cm)
  col  8  z coord (cm)
  col  9  x direction cosine
  col 10  y direction cosine
  col 11-21  zeros (unused)
  col 22  statistical weight  (always 1.0)
  col 23  0.0 (unused)

Standard format  (22 columns, preceded by a comment header):
  col  1  FLUKA run number            (int)
  col  2  primary event number        (int)
  col  3  FLUKA particle type ID      (int)
  col  4  generation number           (int)
  col  5  kinetic energy (GeV)        (float)
  col  6  statistical weight          (float)
  col  7  x coord (cm)                (float)
  col  8  y coord (cm)                (float)
  col  9  x direction cosine          (float)
  col 10  y direction cosine          (float)
  col 11  z coord (cm)                (float)
  col 12  particle age (s)            (float)  -- PLACEHOLDER: 0
  col 13  last decay x (cm)           (float)  -- PLACEHOLDER: 0
  col 14  last decay y (cm)           (float)  -- PLACEHOLDER: 0
  col 15  last decay z (cm)           (float)  -- PLACEHOLDER: 0
  col 16  last decay ID               (int)    -- PLACEHOLDER: 0
  col 17  KE of decay parent (GeV)   (float)  -- PLACEHOLDER: 0
  col 18  last interaction x (cm)    (float)  -- PLACEHOLDER: 0
  col 19  last interaction y (cm)    (float)  -- PLACEHOLDER: 0
  col 20  last interaction z (cm)    (float)  -- PLACEHOLDER: 0
  col 21  last interaction ID        (int)    -- PLACEHOLDER: 1
  col 22  KE of parent (GeV)         (float)  -- PLACEHOLDER: 0

Usage:
    python convert_fluka_new_to_standard.py input.txt output.txt
    python convert_fluka_new_to_standard.py input.txt          # writes to stdout
"""

import sys
import argparse

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

PLACEHOLDER_FLOAT = 0.0
PLACEHOLDER_DECAY_ID = 0
PLACEHOLDER_INTERACTION_ID = 1  # standard files consistently use 1 here


def fmt_int(value, width):
    return f"{int(value):>{width}d}"


def fmt_float(value):
    # Match the Fortran E24.16 style used in standard FLUKA output
    s = f"{value:24.16E}"
    # Python uses 'e', Fortran uses 'E'; Python also writes e+01 not E+01
    # fix exponent: ensure two-digit exponent with sign, upper-case E
    return s


def convert_line(cols):
    """Convert a parsed list of 23 floats/ints to a standard-format line string."""
    run        = int(float(cols[0]))   # col 1
    event      = int(float(cols[1]))   # col 2
    ptype      = int(float(cols[2]))   # col 3
    generation = int(float(cols[3]))   # col 4
    ke         = float(cols[4]) # col 5
    y_coord    = float(cols[5]) # col 6 in new → col 8 in standard
    x_coord    = float(cols[6]) # col 7 in new → col 7 in standard
    z_coord    = float(cols[7]) # col 8 in new → col 11 in standard
    x_dcos     = float(cols[8]) # col 9 → col 9
    y_dcos     = float(cols[9]) # col 10 → col 10
    weight     = float(cols[21])# col 22 in new → col 6 in standard

    parts = [
        fmt_int(run,   5),          # col 1
        fmt_int(event, 9),          # col 2
        fmt_int(ptype, 5),          # col 3
        fmt_int(generation, 4),     # col 4
        fmt_float(ke),              # col 5
        fmt_float(weight),          # col 6
        fmt_float(x_coord),         # col 7
        fmt_float(y_coord),         # col 8
        fmt_float(x_dcos),          # col 9
        fmt_float(y_dcos),          # col 10
        fmt_float(z_coord),         # col 11
        fmt_float(PLACEHOLDER_FLOAT),  # col 12  particle age
        fmt_float(PLACEHOLDER_FLOAT),  # col 13  last decay x
        fmt_float(PLACEHOLDER_FLOAT),  # col 14  last decay y
        fmt_float(PLACEHOLDER_FLOAT),  # col 15  last decay z
        fmt_int(PLACEHOLDER_DECAY_ID, 5),     # col 16  last decay ID
        fmt_float(PLACEHOLDER_FLOAT),  # col 17  KE decay parent
        fmt_float(PLACEHOLDER_FLOAT),  # col 18  last interaction x
        fmt_float(PLACEHOLDER_FLOAT),  # col 19  last interaction y
        fmt_float(PLACEHOLDER_FLOAT),  # col 20  last interaction z
        fmt_int(PLACEHOLDER_INTERACTION_ID, 5),  # col 21  last interaction ID
        fmt_float(PLACEHOLDER_FLOAT),  # col 22  KE of parent
    ]
    return "".join(parts)


def convert(infile, outfile):
    outfile.write(HEADER)
    for lineno, line in enumerate(infile, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cols = line.split()
        if len(cols) != 23:
            print(
                f"WARNING: line {lineno} has {len(cols)} columns (expected 23), skipping.",
                file=sys.stderr,
            )
            continue
        outfile.write(convert_line(cols) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert FLUKA new format to standard fort.30 format."
    )
    parser.add_argument("input", help="Input file in new format")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    with open(args.input) as infile:
        if args.output:
            with open(args.output, "w") as outfile:
                convert(infile, outfile)
        else:
            convert(infile, sys.stdout)


if __name__ == "__main__":
    main()
