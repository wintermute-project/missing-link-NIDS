import decimal
import os

import pandas as pd

decimal.getcontext().prec = 3
decimal.getcontext().rounding = "ROUND_HALF_UP"


def make_df():
    if os.path.exists("results.txt"):
        os.remove("results.txt")
    data = pd.read_csv("dataset.csv", delimiter=";", header=0)
    data.fillna(0, inplace=True)
    data.to_csv("dataset_na.csv", sep=";", index=False)
    return data


def analyse_data(data):
    # NOTE THAT RESULTS ARE NOT CORRECTED HERE
    for col in data.columns:
        with open("results.txt", "a", encoding='utf-8') as f:
            stats = data[col].value_counts()
            hypotheses = stats.index.name
            f.write(str(stats.name) + "\n")
            for index, value in stats.items():
                f.write("\t" + str(index) + ": " + str(value) + " / " + str(round(value / len(data), 2)) + "\n")
            f.write("\n")


def main():
    data = make_df()
    analyse_data(data)


if __name__ == '__main__':
    main()
