# Interactive dashboard for submission
# Displays all analysis results for Bob
# Run: python interactive_dashboard.py

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import csv
import json
import os

HOST = "0.0.0.0"
PORT = 8000

PART2_OUTPUT = "part2_cell_frequencies.csv"
PART3_STATS = "part3_responder_statistics.csv"
PART3_PLOT = "part3_responder_boxplot.png"
PART4_SUMMARY = "part4_subset_summary.csv"
PART4_SAMPLES = "part4_subset_samples.csv"

# Read in the CSVs we have made
def read_csv(filename):
    with open(filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)

# Build the dashboard
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        if path == "/":
            self.serve_dashboard()

        elif path == "/api/part2":
            self.serve_all_part2()

        elif path == "/api/samples":
            self.serve_samples()

        elif path == "/api/frequencies":
            sample = params.get("sample", [None])[0]
            self.serve_frequencies(sample)

        elif path == "/api/part3/statistics":
            self.serve_part3_statistics()

        elif path == "/part3_responder_boxplot.png":
            self.serve_part3_plot()

        elif path == "/api/part4/summary":
            self.serve_part4_summary()

        elif path == "/api/part4/samples":
            self.serve_part4_samples()

        else:
            self.send_error(404, "Not found")

    # Converts data to JSON for browser
    def send_json(self, data):
        response = json.dumps(data).encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()

        self.wfile.write(response)

    # Give part 2 results to browser
    def serve_all_part2(self):
        data = read_csv(PART2_OUTPUT)
        self.send_json(data)

    # Give part2 samples to browser
    def serve_samples(self):
        rows = read_csv(PART2_OUTPUT)

        samples = sorted({
            row["sample"]
            for row in rows
        })

        data = [
            {"sample": sample}
            for sample in samples
        ]

        self.send_json(data)

    # Give part2 frequencies for one sample to browser
    def serve_frequencies(self, sample):
        if sample is None:
            self.send_error(
                400,
                "Sample is required"
            )
            return
        rows = read_csv(PART2_OUTPUT)
        data = [
            row
            for row in rows
            if row["sample"] == sample
        ]
        if not data:
            self.send_error(
                404,
                f"Sample not found: {sample}"
            )
            return

        self.send_json(data)

    # Give part3 statistics to browser
    def serve_part3_statistics(self):
        data = read_csv(PART3_STATS)
        self.send_json(data)

    # Give part 3 plot to browser
    def serve_part3_plot(self):
        with open(PART3_PLOT, "rb") as file:
            plot = file.read()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "image/png"
        )
        self.send_header(
            "Content-Length",
            str(len(plot))
        )
        self.end_headers()
        self.wfile.write(plot)

    # Give part 4 summary to browser
    def serve_part4_summary(self):
        data = read_csv(PART4_SUMMARY)
        self.send_json(data)

    # Give part 4 samples to browser
    def serve_part4_samples(self):
        data = read_csv(PART4_SAMPLES)
        self.send_json(data)

    # Dashboard page
    def serve_dashboard(self):
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Immune Trial Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #f7f7f7;
            color: #222;
        }
        h1 {
            margin-bottom: 5px;
        }
        h2 {
            margin-top: 0;
        }
        .subtitle {
            color: #555;
            margin-bottom: 30px;
        }
        .section {
            background-color: white;
            padding: 25px;
            margin-top: 25px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .controls {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        label {
            font-weight: bold;
        }
        select {
            padding: 8px;
            min-width: 180px;
            font-size: 14px;
        }
        button {
            padding: 8px 14px;
            font-size: 14px;
            cursor: pointer;
        }
        .table-container {
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th,
        td {
            border-bottom: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background-color: #fafafa;
        }
        .summary {
            margin: 15px 0;
            color: #555;
        }
        .frequency-bars {
            margin-top: 30px;
        }
        .bar-row {
            display: grid;
            grid-template-columns: 130px 1fr 80px;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .bar-background {
            height: 24px;
            background-color: #eeeeee;
            border-radius: 4px;
            overflow: hidden;
        }
        .bar {
            height: 100%;
            background-color: #4d79a6;
            border-radius: 4px;
        }
        .bar-value {
            text-align: right;
        }
        .part3-layout {
            display: grid;
            grid-template-columns: 1fr;
            gap: 25px;
        }
        .part3-plot {
            width: 100%;
            max-width: 900px;
            height: auto;
            display: block;
        }
        .plot-panel,
            .stats-panel {
            min-width: 0;
        }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(
                auto-fit,
                minmax(180px, 1fr)
            );
            gap: 15px;
            margin-top: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background-color: #fafafa;
        }
        .summary-card-title {
            font-size: 14px;
            color: #555;
            margin-bottom: 5px;
        }
        .summary-card-value {
            font-size: 24px;
            font-weight: bold;
        }
        .summary-card-group {
            font-size: 12px;
            color: #777;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>Immune Trial Analysis Dashboard</h1>
    <p class="subtitle">
        Interactive presentation of immune-cell analysis results.
    </p>

    <!-- Part 2: Cell Population Frequencies -->
    <div class="section">
        <h2>Part 2: Cell Population Frequencies</h2>
        <p>
            Relative frequencies were calculated for each immune
            cell population within each sample. Select an individual
            sample below or display the complete Part 2 results.
        </p>
        <div class="controls">
            <label for="sampleSelect">
                Sample:
            </label>
            <select id="sampleSelect"></select>
            <button
                id="showSampleButton"
                type="button">
                Show Selected Sample
            </button>
            <button
                id="showAllButton"
                type="button">
                Show All Samples
            </button>
        </div>
        <div
            id="summaryText"
            class="summary">
        </div>
        <div
            id="frequencyBars"
            class="frequency-bars">
        </div>
        <div class="table-container">
            <table id="frequencyTable">
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>Total Count</th>
                        <th>Population</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <!-- Part 3: Treatment Response Analysis -->
    <div class="section">
        <h2>Part 3: Treatment Response Analysis</h2>
        <p>
            Day 0 PBMC immune-cell relative frequencies were compared
            between melanoma patients who later responded to miraclib
            and those who did not.
        </p>
        <div class="part3-layout">
            <div class="plot-panel">
                <h3>Responder vs Non-responder Frequencies</h3>
                <img
                    src="/part3_responder_boxplot.png"
                    alt="Boxplots comparing day 0 immune cell frequencies between responders and non-responders"
                    class="part3-plot"
                >
            </div>
            <div class="stats-panel">
                <h3>Statistical Summary</h3>
                <p class="summary">
                    Two-sided Mann–Whitney U tests were used to compare
                    responders and non-responders for each immune-cell population.
                    Benjamini–Hochberg adjusted p-values are also shown.
                </p>
                <div class="table-container">
                    <table id="part3StatsTable">
                        <thead>
                            <tr>
                                <th>Population</th>
                                <th>Responder Median</th>
                                <th>Non-responder Median</th>
                                <th>Median Difference</th>
                                <th>U Statistic</th>
                                <th>p-value</th>
                                <th>Adjusted p-value</th>
                                <th>Significant</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <!-- Part 4: Baseline Miraclib Sample Summary -->
    <div class="section">
        <h2>Part 4: Baseline Miraclib Sample Summary</h2>
        <p>
            Day 0 PBMC samples from melanoma patients treated with
            miraclib were identified and summarized by project,
            treatment response, and sex.
        </p>
        <h3>Subset Summary</h3>
        <div
            id="part4SummaryCards"
            class="summary-cards">
        </div>
        <h3>Matching Baseline Samples</h3>
        <p
            id="part4SampleCount"
            class="summary">
        </p>
        <div class="table-container">
            <table id="part4SamplesTable">
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>Subject</th>
                        <th>Project</th>
                        <th>Response</th>
                        <th>Sex</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
<script>
    const populationLabels = {
        "b_cell": "B cell",
        "cd8_t_cell": "CD8 T cell",
        "cd4_t_cell": "CD4 T cell",
        "nk_cell": "NK cell",
        "monocyte": "Monocyte"
    };
    async function loadSamples() {
        const response = await fetch("/api/samples");
        const samples = await response.json();
        const select =
            document.getElementById("sampleSelect");
        select.innerHTML = "";
        samples.forEach(row => {
            const option =
                document.createElement("option");
            option.value = row.sample;
            option.textContent = row.sample;
            select.appendChild(option);
        });
        if (samples.length > 0) {
            select.value = samples[0].sample;
            await loadSelectedSample(
                samples[0].sample
            );
        }
    }
    function displayTable(data) {
        const tbody =
            document.querySelector(
                "#frequencyTable tbody"
            );
        tbody.innerHTML = "";
        data.forEach(row => {
            const tr =
                document.createElement("tr");
            const population =
                populationLabels[row.population]
                || row.population;
            tr.innerHTML = `
                <td>${row.sample}</td>
                <td>${row.total_count}</td>
                <td>${population}</td>
                <td>${row.count}</td>
                <td>${row.percentage}%</td>
            `;
            tbody.appendChild(tr);
        });
    }
    function displayBars(data) {
        const container =
            document.getElementById(
                "frequencyBars"
            );
        container.innerHTML = "";
        if (data.length !== 5) {
            return;
        }
        data.forEach(row => {
            const percentage =
                Number(row.percentage);
            const population =
                populationLabels[row.population]
                || row.population;
            const rowDiv =
                document.createElement("div");
            rowDiv.className = "bar-row";
            const label =
                document.createElement("div");
            label.textContent = population;
            const background =
                document.createElement("div");
            background.className =
                "bar-background";
            const bar =
                document.createElement("div");
            bar.className = "bar";
            bar.style.width =
                Math.min(
                    Math.max(
                        percentage,
                        0
                    ),
                    100
                ) + "%";
            const value =
                document.createElement("div");
            value.className =
                "bar-value";
            value.textContent =
                percentage.toFixed(2) + "%";
            background.appendChild(bar);
            rowDiv.appendChild(label);
            rowDiv.appendChild(background);
            rowDiv.appendChild(value);
            container.appendChild(rowDiv);
        });
    }
    async function loadSelectedSample(sample) {
        const response = await fetch(
            "/api/frequencies?sample=" +
            encodeURIComponent(sample)
        );
        const data = await response.json();
        document.getElementById(
            "summaryText"
        ).textContent =
            "Displaying 5 cell populations for " +
            sample + ".";
        displayBars(data);
        displayTable(data);
    }
    async function loadAllResults() {
        const response =
            await fetch("/api/part2");
        const data =
            await response.json();
        document.getElementById(
            "summaryText"
        ).textContent =
            "Displaying all " +
            data.length +
            " Part 2 population-frequency records.";
        document.getElementById(
            "frequencyBars"
        ).innerHTML = "";
        displayTable(data);
    }
    document
        .getElementById(
            "showSampleButton"
        )
        .addEventListener(
            "click",
            () => {
                const sample =
                    document.getElementById(
                        "sampleSelect"
                    ).value;

                loadSelectedSample(sample);
            }
        );
    document
        .getElementById(
            "showAllButton"
        )
        .addEventListener(
            "click",
            () => {
                loadAllResults();
            }
        );
    document
        .getElementById(
            "sampleSelect"
        )
        .addEventListener(
            "change",
            event => {
                loadSelectedSample(
                    event.target.value
                );
            }
        );
    async function loadPart3Statistics() {
        const response =
            await fetch("/api/part3/statistics");

        const data =
            await response.json();
        const tbody =
            document.querySelector(
                "#part3StatsTable tbody"
            );
        tbody.innerHTML = "";
        data.forEach(row => {
            const tr =
                document.createElement("tr");
            const population =
                populationLabels[row.population]
                || row.population;
            tr.innerHTML = `
                <td>${population}</td>
                <td>${Number(row.responder_median).toFixed(2)}%</td>
                <td>${Number(row.non_responder_median).toFixed(2)}%</td>
                <td>${Number(row.median_difference).toFixed(2)}</td>
                <td>${Number(row.u_statistic).toFixed(1)}</td>
                <td>${Number(row.p_value).toFixed(3)}</td>
                <td>${Number(row.adjusted_p_value).toFixed(3)}</td>
                <td>${row.significant}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    async function loadPart4Summary() {
        const response =
            await fetch("/api/part4/summary");
        const data =
            await response.json();
        const container =
            document.getElementById(
                "part4SummaryCards"
            );
        container.innerHTML = "";
        data.forEach(row => {
            const card =
                document.createElement("div");
            card.className =
                "summary-card";
            let groupLabel = "";
            if (row.summary_type === "project") {
                groupLabel = "Project";
            }
            else if (row.summary_type === "response") {
                groupLabel = "Treatment response";
            }
            else if (row.summary_type === "sex") {
                groupLabel = "Sex";
            }
            else {
                groupLabel = row.summary_type;
            }
            card.innerHTML = `
                <div class="summary-card-title">
                    ${row.category}
                </div>
                <div class="summary-card-value">
                    ${row.count}
                </div>
                <div class="summary-card-group">
                    ${groupLabel}
                </div>
            `;
            container.appendChild(card);
        });
    }
    async function loadPart4Samples() {
        const response =
            await fetch("/api/part4/samples");
        const data =
            await response.json();
        document.getElementById(
            "part4SampleCount"
        ).textContent =
            "Displaying " +
            data.length +
            " matching baseline samples.";
        const tbody =
            document.querySelector(
                "#part4SamplesTable tbody"
            );
        tbody.innerHTML = "";
        data.forEach(row => {
            const tr =
                document.createElement("tr");
            tr.innerHTML = `
                <td>${row.sample}</td>
                <td>${row.subject}</td>
                <td>${row.project}</td>
                <td>${row.response}</td>
                <td>${row.sex}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    loadSamples();
    loadPart3Statistics();
    loadPart4Summary();
    loadPart4Samples();
</script>
</body>
</html>
        """
        response = html.encode("utf-8")
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()
        self.wfile.write(response)


def main():

    required_files = [
        PART2_OUTPUT,
        PART3_STATS,
        PART3_PLOT,
        PART4_SUMMARY,
        PART4_SAMPLES
    ]
    missing_files = [
        filename
        for filename in required_files
        if not os.path.exists(filename)
    ]
    if missing_files:
        print("ERROR: Missing required dashboard files:")
        for filename in missing_files:
            print(f"  - {filename}")
        print("Run bob_analysis.py first!")
        return

    server = HTTPServer(
        (HOST, PORT),
        DashboardHandler
    )

    print(
        f"Dashboard running at "
        f"http://localhost:{PORT}"
    )
    print(
        "Ctrl+C to stop the dashboard."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(
            "Stopping dashboard."
        )
    finally:
        server.server_close()


if __name__ == "__main__":
    main()