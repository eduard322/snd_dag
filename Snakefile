configfile: "config.yaml"

rule add_auxiliary_to_gst:
    input:
        gst="{name}.ghep.root",
        ghep="{name}.gst.root"
    log:
        "{name}_aux.gst.log"
    output:
        "{name}_aux.gst.root"
    shell:
        "cp {input.gst} {output} && addAuxiliaryToGST {input.ghep} {input.gst}"

rule convert_ghep_gst:
    input:
        "{name}.ghep.root"
    log:
        "{name}.gst.log"
    output:
        "{name}.gst.root"
    shell:
        "gntpc -i {input} -f gst -o {output} -c"

rule generate_input_file:
    input:
        geofile=expand("geofile.{geo_id}.gdml", geo_id=config["geo_id"]),
        xsection="genie_splines_GENIE_v32_ADVSNDG18_02a_01_000_2.xml",
        flux="HL-LHC_neutrinos_TI18_20e6pr_gsimple.root",
        mpl="mpl.xml"
    output:
        expand("sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.ghep.root", N=config["N"], target=config["target"], neutrino_pid=config["neutrino_pid"], event_generator_list=config["event_generator_list"])
    shell:
        'gevgen_fnal -f "{input.flux},,-{config[neutrino_pid]},{config[neutrino_pid]}" \
          -g {input.geofile} \
          -t "+{config[target]}" \
          -L "cm" -D "g_cm3" -n {config[N]} -o $(basename {output} .0.ghep.root) \
        --tune SNDG18_02a_01_000 --cross-sections {input.xsection} \
        --message-thresholds $GENIE/config/Messenger_laconic.xml -z -3 \
        --event-generator-list {config[event_generator_list]} -m {input.mpl}'

rule run_sim:
    input:
        inputfile=expand("sndlhc_+{target}_{N}_{neutrino_pid}_{event_generator_list}_ADVSNDG18_02a_01_000.0.gst.root", N=config["N"], target=config["target"], neutrino_pid=config["neutrino_pid"], event_generator_list=config["event_generator_list"]),
    output:
        expand("sim_{neutrino_pid}_{event_generator_list}_{geo_id}_{N}/sndLHC.Genie-TGeant4.root", N=config["N"], geo_id=config["geo_id"], neutrino_pid=config["neutrino_pid"], event_generator_list=config["event_generator_list"])
    shell:
        'python $SNDSW_ROOT/shipLHC/run_simSND.py \
        --Genie 4 \
        -f {input.inputfile} \
        --AdvSND \
        -n {config[N]} \
        -o sim_{config[neutrino_pid]}_{config[event_generator_list]}_{config[geo_id]}_{config[N]}'

rule generate_mpl_xml:
    input:
        expand("geofile.{geo_id}.gdml", geo_id=config["geo_id"])
    output:
        "mpl.xml"
    shell:
        'gmxpl -f {input} -t "+{config[target]}" -L "cm" -D "g_cm3" -o {output} --message-thresholds $GENIE/config/Messenger_laconic.xml'

rule make_geofile:
    output:
        expand("geofile.{geo_id}.root", geo_id=config["geo_id"])
    shell:
        "python $SNDSW_ROOT/shipLHC/makeGeoFile.py -c $SNDSW_ROOT/geometry/AdvSND_geom_config.py -g {output}"

rule convert_geofile:
    input:
        "{name}.root"
    output:
        "{name}.gdml"
    shell:
        "python gdml_convert.py -i {input} -o {output}"
