import os
import csv
from collections import defaultdict

def calculate_rank(data, column):
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

def process_directory(directory, rank, ranking_column):
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
                    # Verificar la longitud de values y header
                    if len(values) != len(header):
                        # Si values es más largo, recortar desde el principio hasta que sea igual a header
                        if len(values) > len(header):
                            values = values[-len(header):]
                            print(f"Warning: The compound name contains one or more tabs.")
                    # Continuar creando el diccionario
                    for key, value in zip(header, values):
                        data[key] = value
                    data['Path'] = directory + 'energies/' + subdir
                    data_dict['Data'].append(data)


    # Assign rank value according to specified column
    for data in data_dict['Data']:
        data[rank] = calculate_rank(data, column=ranking_column)

    # Sort by rank value
    sorted_data = sorted(data_dict['Data'], key=lambda x: x[rank], reverse=True)

    # Convert rank value in position
    for i, data in enumerate(sorted_data, start=1):
        data[rank] = i

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

    if len(sys.argv) < 3:
        print("Usage: python script.py directory_path software [ranking_column]")
        sys.exit(1)

    directory_path = sys.argv[1]
    software = sys.argv[2]
    if software == "EO":
        ranking_column = 'EON_ET_combo'
        rank = 'EON_Rank'
    elif software == "RC":
        ranking_column = 'TanimotoCombo'
        rank = 'Rank'
    else:
        print("Software must be EO(EON) or RC(ROCS)")
        sys.exit(1)
    if len(sys.argv) > 3:
        ranking_column = sys.argv[3]
    process_directory(directory_path, rank, ranking_column=ranking_column)
