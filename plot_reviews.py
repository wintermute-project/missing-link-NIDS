import decimal
import os
import re

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def get_data(df):
    decimal.getcontext().prec = 3
    decimal.getcontext().rounding = "ROUND_HALF_UP"
    ticked_true = {}
    ticked_true_absolut = {}
    hypotheses = [h for h in df.columns if re.match(r"H\d{1,2}", h)]
    # adjust as order in plot is different than in dataframe
    hypotheses_mapping = {"H1": "H1",
                          "H2": "H2",
                          "H3": "H3",
                          "H4": "H4",
                          "H5": "H5",
                          "H6": "H6",
                          "H7": "H7",
                          "H8": "H8",
                          "H17": "H9",
                          "H11": "H10",
                          "H12": "H11",
                          "H13": "H12",
                          "H15": "H13",
                          "H16": "H14",
                          "H18": "H15",
                          "H19": "H16",
                          "H20": "H17"
                          }
    for h in hypotheses:
        h_nr = re.search(r"H\d{1,2}", h)[0]
        new_h_nr = hypotheses_mapping.get(h_nr)
        if not new_h_nr:
            continue
        ticked = len(df[df[h] == 1])
        if new_h_nr == "H1":
            no_info = len(df[(df["no info on data recording date"] == 1) &
                             (df["H1 Data too old (with respect to the newest utilized dataset)"] == 1)])
            ticked = ticked - no_info
        if new_h_nr == "H8":
            no_info = len(df[(df["unspecified hardware requirements"] == 1) &
                             (df["H8 Special/excessive processing hardware requirements"] == 1)])
            ticked = ticked - no_info
        ticked_ratio = round(ticked / len(df), 2)
        ticked_true[new_h_nr] = ticked_ratio
        ticked_true_absolut[new_h_nr] = ticked
    print(ticked_true_absolut)
    print(ticked_true)
    # sort by hypothesis number
    ticked_true = dict(sorted(ticked_true.items(), key=lambda x: int(x[0][1:])))
    return ticked_true


def plot_reviews(ticked_true, full_hypotheses, hypotheses_groups, group_color, suffix, edgecolor, alpha):
    fig, ax = plt.subplots(figsize=(21, 13))
    # hacky code to group the bars
    break_indices = [3, 5, 9, 12, 14]
    x = [0] * 17
    spacing = 0.8
    result_x = []
    for idx, val in enumerate(x):
        if idx > 0:
            val += spacing + result_x[idx - 1]
        if idx in break_indices:
            val += 0.45
        result_x.append(val)
        
    # plot the results
    x = result_x
    ax.set_yticks(x)
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    bars = ax.barh(y=x, width=ticked_true.values(), height=0.7, alpha=alpha, color=full_hypotheses.values(),
                   edgecolor=edgecolor, linewidth=1)
    ax.set_yticklabels(full_hypotheses.keys(), fontsize=14, color="black", fontstretch="400")
    ax.bar_label(bars, labels=[f'{i:.2f}' for i in list(ticked_true.values())],padding=4, fontsize=14)
    
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1"], fontsize=16)
    ax.set_xlabel("Proportion of papers for which the hypothesis is true", labelpad=15, fontsize=18)
    ax.set_ylabel("Hypotheses", labelpad=15, fontsize=18)
    ax.invert_yaxis()
    for ytick in ax.get_yticklabels():
        ytick.set_x(0.012)
        ytick.set_ha("left")
        
    # create the legend
    legend_box = plt.Rectangle((0.83, -0.7), 0.1625, 3.6, fill=False)
    ax.add_patch(legend_box)
    plt.text(0.84, -0.25, 'Hypothesis about', fontsize=14, fontweight='demi', fontstretch="200")
    offset = 0
    for (color, legend_label) in zip(group_color, hypotheses_groups.keys()):
        ax.add_patch(
            plt.Rectangle((0.84, round(0 + offset, 2)), 0.015, 0.3, fill=True, facecolor=color, edgecolor=edgecolor,
                          alpha=alpha, linewidth=1))
        plt.text(0.86, 0.25 + offset, legend_label, fontsize=14, fontstretch="300")
        offset += 0.475
    # rest
    plt.margins(y=0.03)
    plt.xlim(0, 1)
    # plt.grid(True, color="gainsboro", which="major", axis="x", alpha=0.4)
    plt.savefig(f"plots/plot_{suffix}.pdf", bbox_inches='tight')


def main():
    if not os.path.isdir("plots"):
        os.mkdir("plots")
    df = pd.read_csv("dataset_na.csv", delimiter=";")
    ticked_true = get_data(df)

    # Pale from https://personal.sron.nl/~pault/
    group_color_pale = ['#dddddd', '#ffcccc', '#eeeebb', '#ccddaa', '#cceeff', '#bbccee']
    # matplotlib tab 10
    group_color_mpl = plt.cm.tab10.colors[:6]
    # https://projects.susielu.com/viz-palette
    group_color_vp = ["#ffd700", "#ffb14e", "#fa8775", "#cd34b5", "#9d02d7", "#0000ff"]
    group_color_cubehelix = sns.cubehelix_palette(start=-1, rot=-1, light=.8, dark=0.3, n_colors=6)
    group_colors = [("pale", group_color_pale), ("violett", group_color_vp), ("mplt", group_color_mpl),
                    ("cubehelix", group_color_cubehelix)]

    for suffix, group_color in group_colors:
        if group_color == group_color_vp:
            edgecolor = "darkgray"
            alpha = 0.95
        elif group_color == group_color_pale:
            edgecolor = "gray"
            alpha = 0.85
        elif group_color == group_color_mpl:
            edgecolor = "gray"
            alpha = 0.45
        elif group_color == group_color_cubehelix:
            edgecolor = "black"
            alpha = 0.4
        full_hypotheses = {
            "H1: Data too old (w.r.t. the newest dataset)": group_color[0],
            "H2: Traffic mix unexplained": group_color[0],
            "H3: Data not available": group_color[0],
            "H4: (Pseudo)code not available": group_color[1],
            "H5: Potential model overfitting, not generalizable to own scenario": group_color[1],
            "H6: Unusable in practice, since required data problematic to obtain": group_color[2],
            "H7: Unrealistic or high effort for data collection or monitoring": group_color[2],
            "H8: Special Hardware": group_color[2],
            "H9: False positive rate hinders practical adoption": group_color[2],
            "H10: Model complexity too high, missing trust and explainability": group_color[3],
            "H11: Features not motivated or too complex, missing trust and explainability": group_color[3],
            "H12: Unclear meaning of decision and result": group_color[3],
            "H13: Important usability and interaction features are missing": group_color[4],
            "H14: Privacy not in researchers' focus": group_color[4],
            "H15: No comparison with state-of-the-art given": group_color[5],
            "H16: Ignored domain knowledge": group_color[5],
            "H17: No discussion of limitations": group_color[5],
        }

        hypotheses_groups = {
            "Data": ["H1", "H2", "H3"],
            "Code & Model": ["H4", "H5"],
            "Practicability": ["H6", "H7", "H8", "H9"],
            "Understandability": ["H10", "H11", "H12"],
            "Secondary Concerns": ["H13", "H14"],
            "Contextualization": ["H15", "H16", "H17"]
        }
        plot_reviews(ticked_true, full_hypotheses, hypotheses_groups, group_color, suffix, edgecolor, alpha)


if __name__ == '__main__':
    main()
