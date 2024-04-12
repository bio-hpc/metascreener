import os
import csv
from collections import defaultdict

def calculate_rank(data, column='EON_ET_combo'):
    return float(data[column].strip())

def read_rpt_file(filepath):
    data = {}
    with open(filepath, 'r') as file:
        header = file.readline().strip().split('\t')
        for line in file:
            values = line.strip().split('\t')
            for key, value in zip(header, values):
                data[key] = value
    return data

def process_directory(directory, ranking_column='EON_ET_combo'):
    energies_dir = os.path.join(directory, 'energies')
    subdirectories = [subdir for subdir in os.listdir(energies_dir) if os.path.isdir(os.path.join(energies_dir, subdir))]

    if not subdirectories:
        print(f"No directories found inside {energies_dir}, there must be some error in the MetaScreener runs.")
        return

    data_dict = defaultdict(list)

    for subdir in subdirectories:
        subdir_path = os.path.join(energies_dir, subdir)
        rpt_files = [file for file in os.listdir(subdir_path) if file.endswith('.rpt')]
        for rpt_file in rpt_files:
            rpt_filepath = os.path.join(subdir_path, rpt_file)
            with open(rpt_filepath, 'r') as file:
                header = file.readline().strip().split('\t')
                for line in file:
                    data = {}
                    values = line.strip().split('\t')
                    for key, value in zip(header, values):
                        data[key] = value
                    #data['Path'] = directory
                    data['Path'] = directory + 'energies/' + subdir
                    data_dict['Data'].append(data)

    # Assign rank value according to specified column
    for data in data_dict['Data']:
        data['EON_Rank'] = calculate_rank(data, column=ranking_column)

    # Sort by rank value
    sorted_data = sorted(data_dict['Data'], key=lambda x: x['EON_Rank'], reverse=True)

    # Convert rank value in position
    for i, data in enumerate(sorted_data, start=1):
        data['EON_Rank'] = i

    # Write sorted data in a csv file
    csv_filename = os.path.basename(os.path.normpath(directory)) + '.csv'
    csv_filepath = os.path.join(directory, csv_filename)
    with open(csv_filepath, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=data.keys(), delimiter=';')
        writer.writeheader()
        for data in sorted_data:
            writer.writerow(data)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py directory_path [ranking_column]")
        sys.exit(1)

    directory_path = sys.argv[1]
    if len(sys.argv) > 2:
        ranking_column = sys.argv[2]
        process_directory(directory_path, ranking_column=ranking_column)
    else:
        process_directory(directory_path)
