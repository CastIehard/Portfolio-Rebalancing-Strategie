import pandas as pd
import os
import matplotlib.pyplot as plt

class Config:
    PORTFOLIO_START = 1000
    MONTHLY_INVESTMENT = 500
    LEVERAGE = 1000000

class Stock:
    def __init__(self, name, percentage):
        self.name = name
        self.percentage = percentage
        self.df = self.load_data()

    def load_data(self):
        path = os.path.join(os.path.dirname(__file__), f"Stocks/{self.name}.csv")
        df = pd.read_csv(path)
        return self.interpolate_days(df)

    def interpolate_days(self, df):
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)
        date_range = pd.date_range(start=df["Date"].min(), end=df["Date"].max())
        date_df = pd.DataFrame(date_range, columns=["Date"])
        return date_df.merge(df, on="Date", how="left").interpolate(method="linear")

class Portfolio:
    def __init__(self, stocks, rebalance=False):
        self.stocks = stocks
        self.rebalance = rebalance
        self.df = self.initialize_portfolio()

    def initialize_portfolio(self):
        initial_data = {
            "Date": self.stocks[0].df["Date"],
            "Value": Config.PORTFOLIO_START,
            "Investment": 0
        }
        for stock in self.stocks:
            initial_data.update({
                f"{stock.name}_value": Config.PORTFOLIO_START * stock.percentage,
                f"{stock.name}_price_change": stock.df["Close"].pct_change().fillna(0)
            })
        return pd.DataFrame(initial_data)

    def simulate_investments(self):
        for index, day in enumerate(self.df["Date"][1:], start=1):
            self.apply_daily_changes(index, day)
        return self.df

    def apply_daily_changes(self, index, day):
        for stock in self.stocks:
            self.df.loc[index, f"{stock.name}_value"] = self.df.loc[index - 1, f"{stock.name}_value"]
            self.df.loc[index, f"{stock.name}_value"] *= (1 + self.df.loc[index, f"{stock.name}_price_change"])

        if day.day == 15:
            total_investment = Config.MONTHLY_INVESTMENT
            self.df.loc[index, "Investment"] = total_investment
            if self.rebalance:
                self.rebalance_portfolio(index, total_investment)
            else:
                for stock in self.stocks:
                    self.df.loc[index, f"{stock.name}_value"] += total_investment * stock.percentage

        self.df.loc[index, "Value"] = sum(self.df.loc[index, f"{stock.name}_value"] for stock in self.stocks)

    def rebalance_portfolio(self, index, total_investment):
        current_value = sum(self.df.loc[index - 1, f"{stock.name}_value"] for stock in self.stocks)
        monthly_investment = 0
        for stock in self.stocks:
            real_percentage = self.df.loc[index - 1, f"{stock.name}_value"] / current_value
            diff = stock.percentage - real_percentage
            buy_percentage = stock.percentage + diff * Config.LEVERAGE
            local_investment = total_investment * buy_percentage
            if local_investment < 0:
                local_investment = 0
            if monthly_investment + local_investment > total_investment:
                local_investment = total_investment - monthly_investment

            self.df.loc[index, f"{stock.name}_value"] += local_investment
            monthly_investment += local_investment
            print(f"{stock.name}-> Real: {real_percentage*100}%, Investment: {local_investment}€")
        print("Monthly investment: ", monthly_investment, "€", "\n\n")

def calculate_differences(portfolio_no_re, portfolio_with_re):
    money_invested = round(portfolio_no_re["Investment"].sum() + Config.PORTFOLIO_START, 2)
    print("Money invested: ", money_invested, " €")
    money_in_end_without_rebalancing = round(portfolio_no_re["Value"].iloc[-2], 2)
    print("Money in end without rebalancing: ", money_in_end_without_rebalancing, " €")

    money_in_end_with_rebalancing = round(portfolio_with_re["Value"].iloc[-2], 2)
    print("Money in end with rebalancing: ", money_in_end_with_rebalancing, " €")

    difference = round(money_in_end_with_rebalancing - money_in_end_without_rebalancing, 2)
    print("Difference: ", difference, " €")

    difference_percentage = round(difference / money_in_end_without_rebalancing * 100, 2)
    print("Difference in percentage: ", difference_percentage, " %")

def plot_portfolio(portfolios):
    portfolio_no_re, portfolio_with_re = portfolios

    money_in_end_without_rebalancing = portfolio_no_re.df["Value"].iloc[-2]
    money_in_end_with_rebalancing = portfolio_with_re.df["Value"].iloc[-2]

    difference = round(money_in_end_with_rebalancing - money_in_end_without_rebalancing, 2)
    difference_percentage = round(difference / money_in_end_without_rebalancing * 100, 2)

    for portfolio in portfolios:
        label = "Portfolio with rebalancing" if portfolio.rebalance else "Portfolio without rebalancing"
        plt.plot(portfolio.df["Date"], portfolio.df["Value"], label=label)

    plt.legend()
    plt.xticks(rotation=45)
    plt.title(f"Portfolio value over time - Difference: {difference}€ ({difference_percentage}%)")
    plt.savefig("portfolio_value.png")
    plt.show()


stocks = [Stock("msci_world", 0.2),
        Stock("euro_600", 0.2),
        Stock("gold", 0.2),
        Stock("health", 0.2),
        Stock("real_estate", 0.2)
        ]

portfolio_no_re = Portfolio(stocks, rebalance=False)
portfolio_no_re_df = portfolio_no_re.simulate_investments()
portfolio_with_re = Portfolio(stocks, rebalance=True)
portfolio_with_re_df = portfolio_with_re.simulate_investments()

plot_portfolio([portfolio_no_re, portfolio_with_re])
calculate_differences(portfolio_no_re_df, portfolio_with_re_df)
