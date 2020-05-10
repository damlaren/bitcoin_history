import csv
import datetime
import math
import random


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


class Wallet:
    """Wallet containing BTC bought at each price point."""
    def __init__(self, capital):
        """Constructor.

        :param capital: Starting capital ($).
        """

        self.holdings = {}
        """Dictionary from price to amount bought at that price."""

        self.capital = capital
        """Current capital."""

        self.gains = 0
        """Total realized profits."""

    def buy(self, price, amount):
        """Buy coin.

        :param price: Buy price.
        :param amount: Buy amount.
        :return: Whether buy succeeded.
        """
        assert self.capital >= 0
        assert price > 0
        assert amount > 0

        damage = price * amount
        if damage > self.capital:
            return False
        self.capital -= damage
        if price in self.holdings:
            self.holdings[price] += amount
        else:
            self.holdings[price] = amount
        return True

    def sell(self, buy_price, sell_price, amount):
        """Sell coin.

        :param buy_price: Sell coins bought at this price (must be present).
        :param sell_price: Sell the coins for that price.
        :param amount: Amount to sell.
        """
        assert buy_price > 0 and sell_price > 0 and amount > 0
        assert buy_price in self.holdings and self.holdings[buy_price] >= amount

        self.capital += sell_price * amount
        self.gains += (sell_price - buy_price) * amount
        if self.holdings[buy_price] == amount:
            del self.holdings[buy_price]
        else:
            self.holdings[buy_price] = self.holdings[buy_price] - amount

    def take_profits(self, sell_price, min_profit):
        """Sell coins to realize profits.

        :param sell_price: Price at which to sell coins.
        :param min_profit: Minimum profit to accept per coin.
        """
        sells = [(k, v) for k, v in self.holdings.items()]
        for s in sells:
            if sell_price - s[0] >= min_profit:
                self.sell(s[0], sell_price, s[1])


def buylow_sellhigh(btc_data, capital, interval_size, max_price, buy_size, min_profit):
    """Algorithm that buys as prices go down, sells as they go up.

    Commission fees are ignored.

    :param btc_data: BTC data.
    :param capital: Starting capital.
    :param interval_size: Buy some coin when it drops every `interval` $.
    :param max_price: Maximum price to pay per coin.
    :param buy_size: Amount to buy at once, as a fixed $ amount.
    :param min_profit: Minimum profit to accept before selling 1 coin.
    """
    assert interval_size > 0
    assert min_profit >= 0

    wallet = Wallet(capital)
    n_points = len(btc_data)
    last_interval = int(btc_data[0][1] / interval_size)
    for i in range(1, n_points):
        curr_price = btc_data[i][1]
        if math.isnan(curr_price):
            continue

        # Detect interval crossing (only buy or sell at interval)
        curr_interval = int(curr_price / interval_size)
        if curr_interval > last_interval:
            sell_price = curr_interval * interval_size
            wallet.take_profits(sell_price, min_profit)
        elif curr_interval < last_interval:
            # Price went down. Buy a fixed amount more than the next highest holding.
            crossed_price = (curr_interval + 1) * interval_size
            if crossed_price <= max_price:
                target_buy = buy_size / crossed_price
                if crossed_price in wallet.holdings:
                    target_buy = max(0, target_buy - wallet.holdings[crossed_price])
                if target_buy > 0:
                    wallet.buy(crossed_price, target_buy)

        # Prepare for next iteration.
        last_interval = curr_interval

    print(f'Final holdings: ${wallet.holdings}')
    print(f'Final capital: ${wallet.capital}')
    print(f'Final gains: ${wallet.gains}')


def buy_random(btc_data, capital, chance, max_price, buy_size, min_profit):
    """Buy BTC at random times, sell it when profit is realized.

    :param btc_data: BTC data.
    :param capital: Starting capital.
    :param chance: Chance to buy on each timepoint, as a float between 0 and 1.
    :param max_price: Maximum price to pay per coin.
    :param buy_size: Amount to buy at once, as a fixed $ amount.
    :param min_profit: Minimum profit to take.
    """
    wallet = Wallet(capital)
    n_points = len(btc_data)
    for i in range(1, n_points):
        curr_price = btc_data[i][1]
        if math.isnan(curr_price):
            continue
        if random.random() < chance:
            if curr_price < max_price:
                wallet.buy(curr_price, buy_size / curr_price)
        wallet.take_profits(curr_price, min_profit)

    print(f'Final holdings: ${wallet.holdings}')
    print(f'Final capital: ${wallet.capital}')
    print(f'Final gains: ${wallet.gains}')


def main():
    btc_data = read_data()
    capital = 40000
    interval_size = 500
    min_profit = 500
    buy_size = 5000
    max_price = 10000
    n_trials = 10

    #buylow_sellhigh(btc_data, capital, interval_size, max_price, buy_size, min_profit)
    for i in range(n_trials):
        buy_random(btc_data, capital, 1.0 / (1440.0 * 3.5), max_price, buy_size, min_profit)


if __name__ == '__main__':
    main()
