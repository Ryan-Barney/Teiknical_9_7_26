# Parts 2 through 4
# Python script to perform the following:
#   Part 2 calculates the frequencies of each cell population per sample and outputs a csv with the information
#   Part 3 performs a statistical analysis to determine patterns of treatment response
#   Part 4 performs data subsetting operations to allow for further analysis of treatment effects
# Run: python bob_analysis.py

import csv
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

DB = "Loblaw_Bio_immune_trial.db"
PART2_OUTPUT = "part2_cell_frequencies.csv"
PART3_STATS = "part3_responder_statistics.csv"
PART3_PLOT = "part3_responder_boxplot.png"
PART4_SUMMARY = "part4_subset_summary.csv"
PART4_SAMPLES = "part4_subset_samples.csv"

CELL_TYPES = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

########## Part 2 helper functions ##########

# Calculates cell population frequencies per sample
def part2_calculate_cell_frequencies(connection):
    cursor = connection.cursor()
    # Round to 2 decimal places below
    cursor.execute("""
        SELECT
            cc.sample,
            totals.total_count,
            cc.cell_type AS population,
            cc.count,
            ROUND(100.0 * cc.count / totals.total_count, 2) AS percentage
        FROM cell_counts AS cc
        JOIN (
            SELECT
                sample,
                SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample
        ) AS totals
            ON cc.sample = totals.sample
        ORDER BY cc.sample, cc.cell_type;
    """)
    return cursor.fetchall()

# Write findings into a csv file for inspection
def part2_write_csv(rows):
    with open(PART2_OUTPUT, "w", newline="", encoding="utf-8") as file:
        w = csv.writer(file)
        w.writerow([
            "sample",
            "total_count",
            "population",
            "count",
            "percentage",
        ])
        w.writerows(rows)

########## Part 3 helper functions ##########

# Get the defined subset of data: PBMC, melanoma, miraclib, and response (yes/no)
# This is done for day 0 only to predict how responder/non-responder populations differ before treatment
def part3_data(connection):
    query = """
        SELECT
            s.subject,
            sa.sample,
            s.response,
            cc.cell_type AS population,
            cc.count,
            totals.total_count,
            100.0 * cc.count / totals.total_count AS percentage
        FROM subjects AS s
        JOIN samples AS sa
            ON s.subject = sa.subject
        JOIN cell_counts AS cc
            ON sa.sample = cc.sample
        JOIN (
            SELECT
                sample,
                SUM(count) AS total_count
            FROM cell_counts
            GROUP BY sample
        ) AS totals
            ON sa.sample = totals.sample
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
          AND s.response IN ('yes', 'no');
    """
    return pd.read_sql_query(query, connection)

# Mann-Whitney U test to compare responder vs. non-responder cell frequencies
def part3_stat_test_response_frequencies(data):
    results = []
    for population in CELL_TYPES:
        population_data = data[
            data["population"] == population
        ]

        # Only want responders vs. non-responders, not NULL
        responders = population_data.loc[
            population_data["response"] == "yes",
            "percentage"
        ]
        non_responders = population_data.loc[
            population_data["response"] == "no",
            "percentage"
        ]

        # Run two-sided Mann-Whitney U 
        u_statistic, p_value = mannwhitneyu(
            responders,
            non_responders,
            alternative="two-sided"
        )

        # Stats
        responder_median = responders.median()
        non_responder_median = non_responders.median()

        results.append({
            "population": population,
            "responder_n": len(responders),
            "responder_median": responder_median,

            "non_responder_n": len(non_responders),
            "non_responder_median": non_responder_median,

            "median_difference": (
                responder_median - non_responder_median
            ),
            "u_statistic": u_statistic,
            "p_value": p_value,
        })
    results_df = pd.DataFrame(results)

    # FDR correction for 5 tests
    results_df["adjusted_p_value"] = multipletests(
        results_df["p_value"],
        method="fdr_bh"
    )[1]
    results_df["significant"] = (
        results_df["adjusted_p_value"] < 0.05
    )
    return results_df

# Create boxplot responder vs. non-responder cell frequencies at day 0
def part3_boxplot(data, results):
    population_labels = {
        "b_cell": "B cell",
        "cd8_t_cell": "CD8 T cell",
        "cd4_t_cell": "CD4 T cell",
        "nk_cell": "NK cell",
        "monocyte": "Monocyte"
    }
    population_order = [
        "b_cell",
        "cd8_t_cell",
        "cd4_t_cell",
        "nk_cell",
        "monocyte"
    ]

    # Make a plotting copy
    plot_data = data.copy()
    plot_data["population_label"] = (
        plot_data["population"]
        .map(population_labels)
    )

    plot_data["response_label"] = (
        plot_data["response"]
        .map({
            "no": "Non-responder",
            "yes": "Responder"
        })
    )

    label_order = [
        population_labels[population]
        for population in population_order
    ]

    plt.figure(figsize=(10, 6))

    ax = sns.boxplot(
        data=plot_data,
        x="population_label",
        y="percentage",
        hue="response_label",
        order=label_order,
        hue_order=["Non-responder", "Responder"]
    )

    # Add nominal p-values above each cell 
    for i, population in enumerate(population_order):
        p_value = results.loc[
            results["population"] == population,
            "p_value"
        ].iloc[0]
        population_values = plot_data.loc[
            plot_data["population"] == population,
            "percentage"
        ]
        y_position = population_values.quantile(0.99) + 5
        ax.text(
            i,
            y_position,
            f"p = {p_value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9
        )
    ax.set_xlabel("Immune cell population")
    ax.set_ylabel("Relative frequency in cell populations (%)")
    ax.set_title(
        "Day 0 Immune Cell Frequencies in Miraclib Treatment Response"
    )
    ax.legend(
        title="Treatment response",
        frameon=False
    )

    # Clean and save
    sns.despine()
    plt.tight_layout()
    plt.savefig(
        "part3_responder_boxplot.png",
        bbox_inches="tight"
    )
    plt.close()

########## Part 4 helper functions ##########

# Subset the data to melanoma, miraclib, PBMC, day 0, and summarize counts by project, response
def part4_summary(connection):
    cursor = connection.cursor()
    results = []

    # Samples from each project meeting criteria
    cursor.execute("""
        SELECT
            s.project,
            COUNT(*) AS sample_count
        FROM subjects AS s
        JOIN samples AS sa
            ON s.subject = sa.subject
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
        GROUP BY s.project
        ORDER BY s.project;
    """)
    for project, count in cursor.fetchall():
        results.append({
            "summary_type": "project",
            "category": project,
            "count": count
        })

    # Subject number by response
    cursor.execute("""
        SELECT
            s.response,
            COUNT(DISTINCT s.subject) AS subject_count
        FROM subjects AS s
        JOIN samples AS sa
            ON s.subject = sa.subject
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
        GROUP BY s.response
        ORDER BY s.response;
    """)
    for response, count in cursor.fetchall():
        results.append({
            "summary_type": "response",
            "category": response,
            "count": count
        })

    # Subject number by sex
    cursor.execute("""
        SELECT
            s.sex,
            COUNT(DISTINCT s.subject) AS subject_count
        FROM subjects AS s
        JOIN samples AS sa
            ON s.subject = sa.subject
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
        GROUP BY s.sex
        ORDER BY s.sex;
    """)
    for sex, count in cursor.fetchall():
        results.append({
            "summary_type": "sex",
            "category": sex,
            "count": count
        })

    return pd.DataFrame(results)

# In case Bob wants the samples corresponding to the filtered subset, we also output those
def part4_samples(connection):
    query = """
        SELECT
            sa.sample,
            s.subject,
            s.project,
            s.condition,
            s.treatment,
            sa.sample_type,
            sa.time_from_treatment_start,
            s.response,
            s.sex
        FROM subjects AS s
        JOIN samples AS sa
            ON s.subject = sa.subject
        WHERE s.condition = 'melanoma'
          AND s.treatment = 'miraclib'
          AND sa.sample_type = 'PBMC'
          AND sa.time_from_treatment_start = 0
        ORDER BY s.project, s.subject;
    """
    return pd.read_sql_query(query, connection)

##############################

def main():
    connection = sqlite3.connect(DB)
    try:
        # Part 2!
        part2_rows = part2_calculate_cell_frequencies(connection)
        part2_write_csv(part2_rows)
        print(f"Part 2 complete: {PART2_OUTPUT}")

        #Part 3!
        part3_dat = part3_data(connection)
        part3_stats = part3_stat_test_response_frequencies(part3_dat)
        part3_stats.to_csv(PART3_STATS,index=False)
        part3_boxplot(part3_dat, part3_stats)
        print(f"Part 3 complete: {PART3_STATS} and {PART3_PLOT}")

        # Part 4!
        part4_sum = part4_summary(connection)
        part4_sum.to_csv(PART4_SUMMARY, index=False)
        part4_samp = part4_samples(connection)
        part4_samp.to_csv(PART4_SAMPLES, index=False)
        print(f"Part 4 complete: {PART4_SUMMARY} and {PART4_SAMPLES}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()