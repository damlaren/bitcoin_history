import csv
import datetime


data_fn = 'C:\\Projects\\bitcoin\\data.csv'


# Only use data from 2018 - 2019.
def pare_file():
    csv_fn = 'C:\\Projects\\bitcoin\\coinbaseUSD_1-min_data_2014-12-01_to_2019-01-09.csv'
    with open(csv_fn, 'r') as infile:
        with open(data_fn, 'w') as outfile:
            reader = csv.reader(infile)
            next(reader)  # skip header.
            for row in reader:
                timestamp = int(row[0])
                date = datetime.datetime.utcfromtimestamp(timestamp)
                if date.year >= 2018:
                    outfile.write(f'{timestamp},{row[1]}\n')


def get_printable_date(date, with_time=True):
    if with_time:
        return date.strftime('%Y-%m-%d-%H-%M-%S')
    return date.strftime('%Y-%m-%d')


def read_data():
    with open(data_fn, 'r') as infile:
        reader = csv.reader(infile)
        return [(int(row[0]), float(row[1])) for row in reader]


# Compute the max possible gain starting with an initial investment, if the market was timed perfectly.
# Ignore commission fees.
# The result quickly becomes absurdly large.
def max_gain(btc_data, capital):
    n_points = len(btc_data)
    btc_held = 0
    accum = capital
    for i in range(n_points - 1):
        pt = btc_data[i]
        next_pt = btc_data[i + 1]
        pt_date = datetime.datetime.utcfromtimestamp(pt[0])

        # Buy before every increase in price, if nothing is held.
        # Sell before every downturn, if BTC is held.
        if btc_held == 0 and next_pt[1] > pt[1]:
            btc_held = accum / pt[1]
            accum = 0
        if btc_held > 0 and next_pt[1] < pt[1]:
            accum += btc_held * pt[1]
            btc_held = 0

        # Sell off on last day.
        if i == n_points - 2:
            accum += btc_held * pt[1]
            btc_held = 0
    return accum - capital


def main():
    btc_data = read_data()
    capital = 50000
    max_profit = max_gain(btc_data, capital)
    print(f'Max possible profit since start of 2018 is: {max_profit}')


if __name__ == '__main__':
    main()
