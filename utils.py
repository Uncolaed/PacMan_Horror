#csv file processing 
import csv

def auto_cast(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

def load_csv_auto(path, delimiter=","):
    grid = []
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            grid.extend([auto_cast(v) for v in row])
    return grid
