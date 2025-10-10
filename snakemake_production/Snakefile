import os
configfile: "config.yaml"

eos_dir = config["eos_dir"]
neutrino_pid = config['neutrino_pid']
target = config['target']
event_generator_list = config['event_generator_list']
N = config['N']
geo_id = config['geo_id']




# Define the single target path based on your config
rule all:
    input:
        os.path.join(
            eos_dir,
            f"sim_{neutrino_pid}_{event_generator_list}_{geo_id}_{N}",
            "sndLHC.Genie-TGeant4.root"
        )

rule make_geofile:
    output:
        os.path.join(eos_dir, f"geofile.{geo_id}.root")
    shell:
        "python $ADVSNDSW_ROOT/shipLHC/makeGeoFile.py -c $ADVSNDSW_ROOT/geometry/AdvSND_geom_config.py -g {output}"

rule convert_geofile:
    input:
        os.path.join(eos_dir, f"geofile.{geo_id}.root")
    output:
        os.path.join(eos_dir, f"geofile.{geo_id}.gdml")
    shell:
        "python gdml_convert.py -i {input} -o {output}"

rule generate_mpl_xml:
    input:
        os.path.join(eos_dir, f"geofile.{geo_id}.gdml")
    output:
        os.path.join(eos_dir, "mpl.xml")
    shell:
        "gmxpl -f {input} -t \"+{target}\" -L \"cm\" -D \"g_cm3\" -o {output} --message-thresholds $GENIE/config/Messenger_laconic.xml"


rule generate_input_file:
    input:
        # your four inputs
        gdml    = os.path.join(eos_dir, f"geofile.{geo_id}.gdml"),
        xs      = "/afs/cern.ch/work/d/dannc/public/AdvSND/2024/splines/genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2_plus2.xml",
        header  = "/eos/experiment/sndlhc/users/ursovsnd/genie_input/20b_no_bias.gsimple.root",
        auxxml  = "/afs/cern.ch/work/d/dannc/public/AdvSND/2024/auxiliary/mympl_plus.xml"

    output:
        # f-string injects eos_dir, but {target}, {N}, etc. remain wildcards
        os.path.join(
            eos_dir,
            "sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.ghep.root"
        )

    params:
        # now that wildcards are defined, strip off the ".ghep.root" suffix to get the GENIE prefix
        prefix=lambda wildcards, output: output[0][:-len(".0.ghep.root")]

    shell:
        """
        gevgen_fnal \
          -f "{input.header},,-{wildcards.neutrino_pid},{wildcards.neutrino_pid}" \
          -g {input.gdml} \
          -t "+{wildcards.target}" \
          -L cm -D g_cm3 \
          -n {wildcards.N} \
          -o {params.prefix} \
          --tune SNDG18_02a_01_000 \
          --cross-sections {input.xs} \
          --message-thresholds $GENIE/config/Messenger_laconic.xml -z -3 \
          --event-generator-list {wildcards.event_generator_list} \
          -m {input.auxxml}
        """

rule convert_ghep_gst:
    input:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.ghep.root"
        )
    output:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.gst.root"
        )
    log:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.gst.log"
        )
    shell:
        "gntpc -i {input} -f gst -o {output} -c"

rule add_auxiliary_to_gst:
    input:
        gst=os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.gst.root"
        ),
        ghep=os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.ghep.root"
        )
    output:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0_aux.gst.root"
        )
    log:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0_aux.gst.log"
        )
    shell:
        "cp {input.gst} {output} && addAuxiliaryToGST {input.ghep} {input.gst}"

rule run_sim:
    input:
        os.path.join(
            eos_dir,
            f"sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0_aux.gst.root"
        )
    output:
        os.path.join(
            eos_dir,
            f"sim_{neutrino_pid}_{event_generator_list}_{geo_id}_{N}",
            "sndLHC.Genie-TGeant4.root"
        )
    shell:
        "python $ADVSNDSW_ROOT/shipLHC/run_simSND.py --Genie 4 -f {input} --AdvSND -n {N} -o {output}"

