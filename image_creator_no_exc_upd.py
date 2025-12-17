#!/usr/bin/env python
# coding: utf-8
"""Create images and features for use in CNNs."""

import argparse
import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import ROOT
import uproot
from tqdm import tqdm


def main():
    """Create images and features for use in CNNs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputfiles",
        nargs="+",
        help="""List of input files to use.\n"""
        """Supports retrieving file from EOS via the XRootD protocol.""",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--outputfile",
        help="""Output file to write to.""",
        required=True,
    )
    parser.add_argument(
        "-j",
        "--num_cpu",
        default=1,
        type=int,
        help="""Number of threads to use.""",
    )
    parser.add_argument(
        "--saturation",
        default=1,
        type=int,
        help="""Saturation threshold, defaults to digital →1.""",
    )
    parser.add_argument(
        "--energy-cut",
        default=0,
        type=float,
        help="""Neutrino energy cut [GeV], defaults to 0.""",
    )
    parser.add_argument(
        "--new-geo",
        action="store_true",
        help="""Use channel mapping etc. for new no-excavation geometry.""",
    )
    parser.add_argument(
        "--muonic",
        action="store_true",
        help="""Select muonic events for ν_τ.""",
    )
    parser.add_argument(
        "--hadronic",
        action="store_true",
        help="""Select non-muonic events for ν_τ.""",
    )
    parser.add_argument(
        "--CC",
        action="store_true",
        help="""Select CC events for neutrinos.""",
    )
    parser.add_argument(
        "--NC",
        action="store_true",
        help="""Select NC events for neutrinos.""",
    )
    parser.add_argument(
        "--fiducial",
        action="store_true",
        help="""Cut on fiducial volume.""",
    )
    parser.add_argument(
        "--plot_events",
        action="store_true",
        help="""Plot events and save them to file.""",
    )
    args = parser.parse_args()
    ROOT.EnableImplicitMT(args.num_cpu)

    ROOT.gInterpreter.ProcessLine('#include "ShipMCTrack.h"')
    ROOT.gInterpreter.ProcessLine('#include "AdvTargetHit.h"')
    ROOT.gInterpreter.ProcessLine('#include "AdvMuFilterHit.h"')
    ROOT.gInterpreter.ProcessLine('#include "Hit2MCPoints.h"')

    df = ROOT.ROOT.RDataFrame("cbmsim", args.inputfiles)
    # ROOT.ROOT.RDF.Experimental.AddProgressBar(df)  # Only available in 6.30+

    df = df.Filter(
        "Digi_AdvMuFilterHits.GetEntries() || Digi_AdvTargetHits.GetEntries()",
        "Preselection",
    )
    ROOT.gInterpreter.Declare(
        """
        int station_from_id(int id) {
        return id >>17;
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        int column_from_id(int id) {
        int column = (id >> 11) % 4;
        int sensor = (id >> 10) % 2;
        return 2*column + sensor;
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        int sensor_from_id(int id) {
        return (id >> 10) % 2;
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        int strip_from_id(int id) {
        return (id) % 1024;
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        int plane_from_id(int id) {
        return (id >> 16) % 2;
        }
        """
    )
    ROOT.gInterpreter.Declare(
            """
            int row_from_id(int id) {
            return (id >> 13) % 8;
            }
            """
        )

    ROOT.gInterpreter.Declare(
        """
        int is_charged_lepton(int id) {
        return (abs(id) == 11) || (abs(id) == 13) || (abs(id) == 15);
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        ROOT::RVec<std::unordered_map<int, float>> wlist(Hit2MCPoints* link, ROOT::RVec<int> ids) {
            ROOT::RVec<std::unordered_map<int, float>> wlists{};
            for (auto&& id : ids) {
                wlists.push_back(link->wList(id));
            }
            return wlists;
        }
        """
    )
    ROOT.gInterpreter.Declare(
        """
        int points_from_weights(std::unordered_map<int, float> weights) {
            return weights.size();
        }
        """
    )
    ROOT.gInterpreter.Declare(f"const int SATURATION = {args.saturation};")
    ROOT.gInterpreter.Declare(
        """
        int apply_saturation(int points) {
            return min(points, SATURATION);
        }
        """
    )

    # ROOT.gInterpreter.Declare(r"""
    # // Z2-symmetric mapping
    # // base = strip + row*pitch
    # // rev  = (pitch - strip) + row*pitch
    # // apply rev if (column>=2) XOR (row is odd)
    # int strip_id_z2(int strip, int row, int column, int pitch=768) {
    #     const int base = strip + row * pitch;
    #     const int rev  = (pitch - 1 - strip) + row * pitch;

    #     // XOR condition (exactly one true => flip once)
    #     const bool mask = (column >= 2) != ((row % 2) == 1);

    #     return mask ? rev : base;
    # }

    # // invert X for plane==1
    # int invert_X_strip_id(int strip_id, int plane, int pitch=768) {
    #     return (plane == 1) ? (pitch * 4 - 1 - strip_id) : strip_id;
    # }

    # // Convenience: do both in one call
    # int calc_strip_id(int strip, int row, int column, int plane, int pitch=768) {
    #     int sid = strip_id_z2(strip, row, column, pitch);
    #     sid = invert_X_strip_id(sid, plane, pitch);
    #     return sid;
    # }
    # """)

    ROOT.gInterpreter.Declare(r"""
    #include <ROOT/RVec.hxx>
    using ROOT::VecOps::RVec;

    // Your scalar functions (as before)
    int strip_id_z2(int strip, int row, int column, int pitch=768) {
        const int base = strip + row * pitch;
        const int rev  = (pitch - 1 - strip) + row * pitch;
        const bool mask = (column >= 2) != ((row % 2) == 1); // XOR
        return mask ? rev : base;
    }

    int invert_X_strip_id(int strip_id, int plane, int pitch=768) {
        return (plane == 1) ? (pitch * 4 - 1 - strip_id) : strip_id;
    }

    int calc_strip_id(int strip, int row, int column, int plane, int pitch=768) {
        int sid = strip_id_z2(strip, row, column, pitch);
        sid = invert_X_strip_id(sid, plane, pitch);
        return sid;
    }

    // Vectorized overload
    RVec<int> calc_strip_id_vec(const RVec<int>& strips,
                                const RVec<int>& rows,
                                const RVec<int>& columns,
                                const RVec<int>& planes,
                                int pitch=768) {
        const auto n = strips.size();
        RVec<int> out(n);

        // Optional safety checks (comment out if you want max speed)
        // if (rows.size() != n || columns.size() != n || planes.size() != n) {
        //     throw std::runtime_error("calc_strip_id_vec: input RVec sizes mismatch");
        // }

        for (size_t i = 0; i < n; ++i) {
            out[i] = calc_strip_id(strips[i], rows[i], columns[i], planes[i], pitch);
        }
        return out;
    }
    """)

    ROOT.gInterpreter.Declare(
        """
        bool is_muonic(const TClonesArray& tracks) {
             for (auto* track: tracks) {
                 auto* particle = dynamic_cast<ShipMCTrack*>(track);
                 if (particle->GetMotherId() == 1) {
                     if (abs(particle->GetPdgCode()) == 13) {
                         return true;
                     }
                 }
             }
             return false;
        }
        """
    )
    # ROOT.gInterpreter.Declare(
    #     """
    #     bool fiducial_cut(double x, double y, double z) {
    #          if (x < -30 || x > -10)
    #               return false;
    #          if (y < 35 || y > 55)
    #               return false;
    #          if (z < -20 || z > 20)
    #               return false;
    #          return true;
    #     }
    #     """
    # )

    # volAdvTarget_1           : z=   11.8220cm  dZ=   43.4967cm  [  -31.6747      55.3186] dx=   29.9993cm [  -57.0019       2.9968] dy=   29.9970cm [   27.0030      86.9970]                dummy
    #[  -58.1054       1.8933] dy=   29.9970cm [   27.5323      87.5263]
    # [-52.0790      -4.1301]
    # volWall_1             : z=  149.1752cm  dZ=    0.3730cm  [  148.8021     149.5482] dx=   29.9993cm [  -58.1053       1.8934] dy=   29.9970cm [   27.5136      87.5077]
    # Target_Layer_22       : z=  181.4200cm  dZ=    0.4000cm  [  181.0200     181.8200] dx=   23.9745cm [  -52.0763      -4.1274] dy=   20.5930cm [   36.3017      77.4876]                dummy
    ROOT.gInterpreter.Declare(
        """
        bool fiducial_cut(double x, double y, double z) {

        if (x < -52 || x > -4)
                  return false;
        if (y < 36 || y > 77)
                  return false;

        return true;
        }
        """
    )


    df = (
        df.Define("start_x", "dynamic_cast<ShipMCTrack*>(MCTrack[1])->GetStartX()")
        .Define("start_y", "dynamic_cast<ShipMCTrack*>(MCTrack[1])->GetStartY()")
        .Define("start_z", "dynamic_cast<ShipMCTrack*>(MCTrack[1])->GetStartZ()")
        .Define("is_fiducial", "fiducial_cut(start_x, start_y, start_z)")
        .Define("nu_energy", "dynamic_cast<ShipMCTrack*>(MCTrack[0])->GetEnergy()")
        .Define("nu_flavour", "dynamic_cast<ShipMCTrack*>(MCTrack[0])->GetPdgCode()")
        .Define(
            "is_cc",
            "is_charged_lepton(dynamic_cast<ShipMCTrack*>(MCTrack[1])->GetPdgCode())",
        )
        .Define(
            "is_nc",
            "!is_cc",
        )
        .Define("muonic", "is_muonic(MCTrack)")
        .Define("non_muonic", "!muonic")
    )
    if args.fiducial:
        df = df.Filter("is_fiducial", "Fiducial volume cut")
    if args.CC:
        df = df.Filter("is_cc", "Only CC")
    elif args.NC:
        df = df.Filter("is_nc", "Only NC")
    if args.muonic:
        df = df.Filter("muonic", "Only muonic")
    elif args.hadronic:
        df = df.Filter("non_muonic", "Everything but muonic")
    if args.energy_cut:
        df = df.Filter(f"nu_energy >= {args.energy_cut}", "Fiducial volume cut")
    df = (
        df.Define(
            "lepton_energy", "dynamic_cast<ShipMCTrack*>(MCTrack[1])->GetEnergy()"
        )  # TODO not reconstructible in NC case
        .Define("hadron_energy", "nu_energy - lepton_energy")
        .Define("energy_dep_target", "Sum(AdvTargetPoint.fELoss)")
        .Define("energy_dep_mufilter", "Sum(AdvMuFilterPoint.fELoss)")
        .Define(
            "link_target", "dynamic_cast<Hit2MCPoints*>(Digi_AdvTargetHits2MCPoints[0])"
        )
        .Define("weights_target", "wlist(link_target, Digi_AdvTargetHits.fDetectorID)")
        .Define("points_per_hit_target", "Map(weights_target, points_from_weights)")
        .Define(
            "saturated_points_per_hit_target",
            "Map(points_per_hit_target, apply_saturation)",
        )
        .Define(
            "link_mufilter",
            "dynamic_cast<Hit2MCPoints*>(Digi_AdvMuFilterHits2MCPoints[0])",
        )
        .Define(
            "weights_mufilter", "wlist(link_mufilter, Digi_AdvMuFilterHits.fDetectorID)"
        )
        .Define("points_per_hit_mufilter", "Map(weights_mufilter, points_from_weights)")
        .Define(
            "saturated_points_per_hit_mufilter",
            "Map(points_per_hit_mufilter, apply_saturation)",
        )
    )
    # df = (
    #     (
    #         df.Define(
    #             "stations", "Map(Digi_AdvTargetHits.fDetectorID, station_from_id_new)"
    #         )
    #         .Define("strips", "Map(Digi_AdvTargetHits.fDetectorID, strip_from_id_new)")
    #         .Define("planes", "Map(Digi_AdvTargetHits.fDetectorID, plane_from_id_new)")
    #         .Define(
    #             "stations_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, station_from_id_new)",
    #         )
    #         .Define(
    #             "strips_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, strip_from_id_new)",
    #         )
    #         .Define(
    #             "planes_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, plane_from_id_new)",
    #         )
    #         .Define(
    #             "indices",
    #             "strips",
    #         )
    #         .Define("indices_mufilter", "strips_mufilter")
    #     )
    #     if args.new_geo
    #     else (
    #         df.Define(
    #             "stations", "Map(Digi_AdvTargetHits.fDetectorID, station_from_id)"
    #         )
    #         .Define("columns", "Map(Digi_AdvTargetHits.fDetectorID, column_from_id)")
    #         .Define("sensors", "Map(Digi_AdvTargetHits.fDetectorID, sensor_from_id)")
    #         .Define("strips", "Map(Digi_AdvTargetHits.fDetectorID, strip_from_id)")
    #         .Define("planes", "Map(Digi_AdvTargetHits.fDetectorID, plane_from_id)")
    #         .Define(
    #             "stations_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, station_from_id)",
    #         )
    #         .Define(
    #             "columns_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, column_from_id)",
    #         )
    #         .Define(
    #             "sensors_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, sensor_from_id)",
    #         )
    #         .Define(
    #             "strips_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, strip_from_id)",
    #         )
    #         .Define(
    #             "planes_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, plane_from_id)",
    #         )
    #         .Define(
    #             "indices",
    #             "(4 * columns + sensors - 2 * columns * sensors) * 768 + pow(-1, columns) * strips - 1 * columns",
    #         )
    #         .Define(
    #             "indices_mufilter",
    #             "Map(Digi_AdvMuFilterHits.fDetectorID, index_from_id)",
    #         )
    #     )
    # )

    df = (
        df.Define("stations", "Map(Digi_AdvTargetHits.fDetectorID, station_from_id)")
            .Define("columns", "Map(Digi_AdvTargetHits.fDetectorID, column_from_id)")
            .Define("sensors", "Map(Digi_AdvTargetHits.fDetectorID, sensor_from_id)")
            .Define("strips", "Map(Digi_AdvTargetHits.fDetectorID, strip_from_id)")
            .Define("planes", "Map(Digi_AdvTargetHits.fDetectorID, plane_from_id)")
            .Define("rows", "Map(Digi_AdvTargetHits.fDetectorID, row_from_id)")
            .Define(
                "stations_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, station_from_id)",
            )
            .Define(
                "columns_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, column_from_id)",
            )
            .Define(
                "sensors_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, sensor_from_id)",
            )
            .Define(
                "strips_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, strip_from_id)",
            )
            .Define(
                "planes_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, plane_from_id)",
            )
            .Define(
                "rows_mufilter",
                "Map(Digi_AdvMuFilterHits.fDetectorID, row_from_id)",
            )
            .Define(
                "indices",
                "calc_strip_id_vec(strips, rows, columns, planes)",
            )
            .Define(
                "indices_mufilter",
                "calc_strip_id_vec(strips_mufilter, rows_mufilter, columns_mufilter, planes_mufilter)",
            )
       )


    report = df.Report()

    col_names = {
        "start_x",
        "start_y",
        "start_z",
        "nu_energy",
        "hadron_energy",
        "lepton_energy",
        "nu_flavour",
        "is_cc",
        "muonic",
        "energy_dep_target",
        "energy_dep_mufilter",
        "indices",
        "stations",
        "planes",
        "indices_mufilter",
        "stations_mufilter",
        "planes_mufilter",
        "saturated_points_per_hit_target",
        "saturated_points_per_hit_mufilter",
    }

    df.Snapshot(
        "df", "temporary.root", col_names
    )  # TODO Use TMatrix to avoid detour via uproot?
    report.Print()

    # target_dims = (3279, 116) if args.new_geo else (3072, 200)
    # mufilter_dims = (3279, 34) if args.new_geo else (4608, 42)
    target_dims = (768*4, 116)
    # TODO how to do more optimized the last HCAL part that is only X?
    mufilter_dims = (768*4, 68)
    events = uproot.open("temporary.root:df")
    # TODO second file for testing?
    outputfile = uproot.recreate(args.outputfile)
    outputfile.mktree(
        "df",
        {
            "X": (">f4", target_dims),
            "X_mufilter": (">f4", mufilter_dims),
            "start_x": ">f8",
            "start_y": ">f8",
            "start_z": ">f8",
            "nu_energy": ">f8",
            "hadron_energy": ">f8",
            "lepton_energy": ">f8",
            "energy_dep_target": ">f8",
            "energy_dep_mufilter": ">f8",
            "nu_flavour": ">i8",
            "is_cc": "bool",
            "muonic": "bool",
        },
        title="Dataframe for CNN studies",
    )
    t = tqdm(total=events.num_entries)
    for batch in events.iterate(step_size="1MB", library="np"):
        batch_size = batch["is_cc"].shape[0]
        hitmaps = np.zeros((batch_size, *target_dims))
        hitmaps_mufilter = np.zeros((batch_size, *mufilter_dims))
        for i in range(batch_size):
            indices = batch["indices"][i].astype(int)
            stations = batch["stations"][i].astype(int)
            planes = batch["planes"][i].astype(int)
            points = batch["saturated_points_per_hit_target"][i].astype(int)
            hitmaps[i, indices, 2 * stations + planes] = points
            indices = batch["indices_mufilter"][i].astype(int)
            stations = batch["stations_mufilter"][i].astype(int)
            planes = batch["planes_mufilter"][i].astype(int)
            points = batch["saturated_points_per_hit_mufilter"][i].astype(int)
            hitmaps_mufilter[i, indices, 2 * stations + planes] = points
            if args.plot_events:
                print("plotting...")
                plt.subplot(3, 2, 1)
                plt.imshow(hitmaps[i, :, 0:-1:2], aspect="auto")
                plt.subplot(3, 2, 2)
                plt.imshow(hitmaps_mufilter[i, :, 0:-1:2], aspect="auto")
                plt.subplot(3, 2, 3)
                plt.imshow(hitmaps[i, :, 1::2], aspect="auto")
                plt.subplot(3, 2, 4)
                plt.imshow(hitmaps_mufilter[i, :, 1::2], aspect="auto")
                plt.subplot(3, 2, 5)
                plt.imshow(hitmaps[i, :, ::], aspect="auto")
                plt.subplot(3, 2, 6)
                plt.imshow(hitmaps_mufilter[i, :, ::], aspect="auto")
                os.makedirs("/eos/user/u/ursovsnd/SWAN_projects/tests/calopid/plots/",exist_ok = True)
                plt.savefig(f"/eos/user/u/ursovsnd/SWAN_projects/tests/calopid/plots/{i}_sat_5_upd.png")

                #plt.show()
        outputfile["df"].extend(
            {
                "X": hitmaps.astype(np.float32),
                "X_mufilter": hitmaps_mufilter.astype(np.float32),
                "start_x": batch["start_x"],
                "start_y": batch["start_y"],
                "start_z": batch["start_z"],
                "nu_energy": batch["nu_energy"],
                "hadron_energy": batch["hadron_energy"],
                "lepton_energy": batch["lepton_energy"],
                "energy_dep_target": batch["energy_dep_target"],
                "energy_dep_mufilter": batch["energy_dep_mufilter"],
                "nu_flavour": batch["nu_flavour"],
                "is_cc": batch["is_cc"],
                "muonic": batch["muonic"],
            }
        )
        t.update(batch_size)
    outputfile.close()
    os.remove("temporary.root")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

