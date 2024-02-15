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
        expand("sndlhc_+volAdvTarget_{N}_ADVSNDG18_02a_01_000.0.ghep.root", N=config["N"])
    shell:
        'gevgen_fnal -f "{input.flux},,-{config[neutrino_pid]},{config[neutrino_pid]}" \
          -g {input.geofile} \
          -t "+volAdvTarget" \
          -L "cm" -D "g_cm3" -n {config[N]} -o $(basename {output} .0.ghep.root) --tune SNDG18_02a_01_000 --cross-sections {input.xsection} --message-thresholds $GENIE/config/Messenger_laconic.xml -z -2 --event-generator-list CCDIS -m {input.mpl}'

rule run_sim:
    input:
        inputfile=expand("sndlhc_+volAdvTarget_{N}_ADVSNDG18_02a_01_000.0.gst.root", N=config["N"]),
    output:
        'sndLHC.Genie-TGeant4.root'
    shell:
        'python $SNDSW_ROOT/shipLHC/run_simSND.py \
        --Genie 4 \
        -f {input.inputfile} \
        --AdvSND \
        -n {config[N]}'

rule generate_mpl_xml:
    input:
        expand("geofile.{geo_id}.gdml", geo_id=config["geo_id"])
    output:
        "mpl.xml"
    shell:
        'gmxpl -f {input} -t "+volAdvTarget" -L "cm" -D "g_cm3" -o {output} --message-thresholds $GENIE/config/Messenger_laconic.xml'

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
