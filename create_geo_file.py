"""Convert TGeo file to gdml format."""

import ROOT
from argparse import ArgumentParser
import os

parser = ArgumentParser(description=__doc__)
parser.add_argument("--from_config", action = "store_true")
parser.add_argument("-c", "--inputconfig", help="input config geofile", default = "$SNDSW_ROOT/geometry/sndLHC_TI18geom_config.py")
parser.add_argument("-i", "--inputfile", help=".root geometry file")
parser.add_argument("-o", "--outputfile", help=".gdml geometry file", required=True)
parser.add_argument("-y", "--year", help="year of the geometry", required=False)
parser.add_argument("--advsnd", help="enable advsnd option", action = "store_true")
options = parser.parse_args()

if options.from_config:
    if options.advsnd:
        advsnd_geo_config = "$ADVSNDSW_ROOT/geometry/AdvSND_geom_config.py"
        os.system(f"python $ADVSNDSW_ROOT/shipLHC/makeGeoFile.py -c {advsnd_geo_config} -g geo_output_temp.root")
    else:
        os.system(f"python $SNDSW_ROOT/shipLHC/makeGeoFile.py -c {options.inputconfig} -y {options.year} -g geo_output_temp.root")

f = ROOT.TFile(options.inputfile if not options.from_config else "geo_output_temp.root")
geo  = f.Get("FAIRGeom")
geo.Export(options.outputfile)
