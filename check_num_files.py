import os
import fnmatch

def count_files_in_subdirs(base_dir, pattern, start=1, end=1000):
    total_count = 0
    missing_dirs = []

    for i in range(start, end + 1):
        subdir = os.path.join(base_dir, str(i))
        if not os.path.isdir(subdir):
            continue  # Skip if folder doesn't exist

        match_count = 0
        for filename in os.listdir(subdir):
            if fnmatch.fnmatch(filename, pattern):
                match_count += 1

        total_count += match_count

        if match_count == 0:
            print(f"No matching files in: {subdir}")
            missing_dirs.append(subdir)

    print(f"\nTotal matching files found: {total_count}")
    return missing_dirs

# Example usage
#filedir = "/path/to/filedir"
#pattern = "data_*.txt"
#missing_folders = count_files_in_subdirs(filedir, pattern)

# Example usage
directory = "/eos/experiment/sndlhc/users/ursovsnd/advsnd/2025/01/nu16/CCDIS/"
directory = "/eos/experiment/sndlhc/users/ursovsnd/neutrino_production_sndlhc_june_2025/2025/sndlhc_1500fb-1_1/nu14/volume_volMuFilter/"
#pattern = "*.root"  # can be any pattern, e.g. "*.root", "result_2025_*.csv", etc.
# pattern = "sndLHC.Genie-TGeant4.root"
pattern = "sndLHC.Genie-TGeant4_dig.root"
#pattern = "sndlhc_+volAdvTarget_500_ADVSNDG18_02a_01_000.0.ghep.root"
#pattern = "sndlhc_+volAdvTarget_500_ADVSNDG18_02a_01_000.0.gst.root"
num_files = count_files_in_subdirs(directory, pattern)
print(f"Number of matching files: {num_files}")
