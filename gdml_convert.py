"""Convert TGeo file to gdml format."""

import ROOT
from argparse import ArgumentParser

parser = ArgumentParser(description=__doc__)
parser.add_argument("-i", "--inputfile", help=".root geometry file", required=True)
parser.add_argument("-o", "--outputfile", help=".gdml geometry file", required=True)
options = parser.parse_args()

f = ROOT.TFile(options.inputfile)
geo  = f.Get("FAIRGeom")
geo.Export(options.outputfile)
