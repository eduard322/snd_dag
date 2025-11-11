"""Convert TGeo file to gdml format."""

import ROOT
from argparse import ArgumentParser
import os

parser = ArgumentParser(description=__doc__)
parser.add_argument("--from_config", action = "store_true")
parser.add_argument("-c", "--inputconfig", help="input config geofile", default = "$SNDSW_ROOT/geometry/sndLHC_TI18geom_config.py")
parser.add_argument("-i", "--inputfile", help=".root geometry file")
parser.add_argument("-o", "--outputfile", help=".gdml geometry file", required=True)
parser.add_argument("-y", "--year", help="year of the geometry", required=True)
options = parser.parse_args()

if options.from_config:
    os.system(f"python $SNDSW_ROOT/shipLHC/makeGeoFile.py -c {options.inputconfig} -y {options.year} -g geo_output_temp.root")

f = ROOT.TFile(options.inputfile if not options.from_config else "geo_output_temp.root")
geo  = f.Get("FAIRGeom")
geo.Export(options.outputfile)
