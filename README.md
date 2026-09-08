# Loblaw Bio's Immune Cell Population Analysis

This repository contains the pipeline and interactive dashboard for Bob Loblaw's analysis of immune cell populations. The pipeline loads his immune cell data and assesses whether there are differences between melanoma patients who responded to miraclib and those who did not. An interactive dashboard is also included.

## Repository Structure

```text
.
├── cell-count.csv
├── load_data.py
├── bob_analysis.py
├── interactive_dashboard.py
├── requirements.txt
├── Makefile
├── Loblaw_Bio_immune_trial.db
├── README.md
└── outputs/
    ├── part2_cell_frequencies.csv
    ├── part3_responder_statistics.csv
    ├── part3_responder_boxplot.png
    ├── part4_subset_samples.csv
    └── part4_subset_summary.csv
```

The three main Python programs have separate responsibilities:

* `load_data.py` creates the SQLite database and loads the source CSV into the relational structure.
* `bob_analysis.py` performs the analyses for Parts 2–4 and writes the resulting CSV and figure files.
* `interactive_dashboard.py` starts a local web server that displays and allows interaction with the precomputed analysis results.

## Running the Project

The project is designed to run from the repository root in GitHub Codespaces.

### 1. Install dependencies

This installs the Python packages specified in `requirements.txt`.
```bash
make setup
```

### 2. Run the complete analysis pipeline
```bash
make pipeline
```

This sequentially runs:
```bash
python3 load_data.py
python3 bob_analysis.py
```

`load_data.py` rebuilds `Loblaw_Bio_immune_trial.db` from `cell-count.csv`. `bob_analysis.py` then queries the database and generates the requested outputs.

The generated analysis outputs are:

* `part2_cell_frequencies.csv` — cell counts and frequencies for each cell population in each sample.
* `part3_responder_statistics.csv` — comparisons between baseline miraclib responders and non-responders.
* `part3_responder_boxplot.png` — boxplot of the Part 3 response analysis.
* `part4_subset_samples.csv` — Day 0 melanoma PBMC samples from miraclib-treated patients.
* `part4_subset_summary.csv` — summaries by project, treatment response, and sex.

### 3. Start the interactive dashboard
```bash
make dashboard
```

The dashboard runs a local HTTP server on port 8000.
In GitHub Codespaces, open the forwarded port when prompted or navigate to the **Ports** tab and open port 8000 in the browser.
The dashboard presents the results calculated from Parts 2–4.

## Relational Database Description

The input data are split into three SQLite tables: `subjects`, `samples`, and `cell_counts`.

### `subjects`

Stores information that describes an individual subject.

| Column      | Description                            |
| ----------- | -------------------------------------- |
| `subject`   | Unique subject identifier; primary key |
| `project`   | Project associated with the subject    |
| `condition` | Disease/condition                      |
| `age`       | Subject age                            |
| `sex`       | Subject sex                            |
| `treatment` | Treatment received                     |
| `response`  | Treatment response                     |

### `samples`

Stores sample-level information.

| Column                      | Description                                  |
| --------------------------- | -------------------------------------------- |
| `sample`                    | Unique sample identifier; primary key        |
| `subject`                   | Subject who provided the sample; foreign key |
| `sample_type`               | Type of biological sample                    |
| `time_from_treatment_start` | Sampling time relative to treatment start    |
`subject` is a foreign key referencing `subjects(subject)`. Therefore, one subject can be associated with multiple samples.

### `cell_counts`
Stores the measured cell counts in long format.

| Column      | Description                    |
| ----------- | ------------------------------ |
| `sample`    | Sample identifier; foreign key |
| `cell_type` | Cell population                |
| `count`     | Observed cell count            |

The combination of `(sample, cell_type)` is the primary key. This ensures that each cell population has at most one count for a given sample. `sample` is also a foreign key referencing `samples(sample)`.
The relationships can therefore be summarized as:

```text
subjects
|
| 1-to-3
v
samples
|
| 1-to-5
v
cell_counts
```

## Database Design Rationale

The database is normalized so that subject-level information is stored once per subject rather than being repeated for every sample and cell population. Similarly, sample metadata are stored once per sample rather than once for every cell count.

Cell measurements are stored in long format instead of creating a separate database column for every possible cell population. For example, B cells and CD8 T cells are represented as different rows in `cell_counts` rather than as fixed `b_cell` and `cd8_t_cell` database columns.

This design has several advantages for scaling. With hundreds of projects and thousands or more samples, repeated subject and sample metadata do not need to be duplicated across every cell measurement. New cell populations can also be incorporated without altering the table; they can simply be added as new `cell_type` records. Primary and foreign keys enforce the relationships between subjects, samples, and measurements and help preserve data integrity.

The normalized structure also supports downstream analytics. Queries can independently filter or aggregate subject characteristics, sample characteristics, and cell measurements. For substantially larger datasets, indexes could additionally be introduced on frequently queried fields.

## Analysis Overview

### Part 2: Cell Population Frequencies

For each sample, the total cell count is calculated as the sum of all measured cell populations. The relative frequency of each population is then calculated as:

```text
percentage = cell population count / total sample count × 100
```

The percentage is rounded to two decimal places.

The resulting long-format table contains one row per sample and cell population.

### Part 3: Miraclib Response Analysis

The response analysis focuses on baseline (`time_from_treatment_start = 0`) PBMC samples from melanoma patients receiving miraclib. Day 0 samples were selected because the objective is to investigate whether cell population frequencies present before treatment are associated with subsequent treatment response.

Relative cell frequencies are compared between responders and non-responders using two-sided Mann–Whitney U tests. Five cell populations are tested, and Benjamini–Hochberg false discovery rate correction is applied to account for multiple comparisons. The distributions are visualized using boxplots.

### Part 4: Baseline Miraclib Sample Summary

Day 0 PBMC samples from melanoma patients treated with miraclib are identified and summarized by:

* number of samples per project,
* number of responder and non-responder subjects, and
* number of male and female subjects.

The matching sample-level records are also exported for inspection.

## Dashboard

The interactive dashboard is available after running:

```bash
make dashboard
```

Local dashboard URL:

http://localhost:8000

The dashboard is implemented using Python's standard-library HTTP server together with HTML, CSS, and JavaScript. No additional dashboard framework is required. It reads the outputs generated by `bob_analysis.py`.
