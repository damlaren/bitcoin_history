import csv


def pare_file():
    csv_fn = 'C:\\Projects\\bitcoin\\coinbaseUSD_1-min_data_2014-12-01_to_2019-01-09.csv'
    out_fn = 'C:\\Projects\\bitcoin\\data.csv'
    with open(csv_fn, 'r') as infile:
        with open(out_fn, 'w') as outfile:
            reader = csv.reader(infile)
            for row in reader:
                outfile.write(f'{row[0]},{row[1]}\n')


def main():
    pare_file()


if __name__ == '__main__':
    main()
