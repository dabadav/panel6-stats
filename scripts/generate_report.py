import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "outputs")  # Store outputs within project

# Load computed metrics
df_metrics = pd.read_csv(f"{OUTPUT_DIR}/logs_metrics.csv")

# Generate an HTML report with full-width layout
html_content = f"""
<html>
<head>
    <title>Panel 6 - Logs</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.25;
            background-color: #f4f4f4;
        }}
        .container {{
            width: 95%; /* Allow some margin on smaller screens */
            max-width: 1920px; /* Keep it large for big screens */
            margin: auto;
            padding: 20px;
            background: white;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .tabs {{
            display: flex;
            justify-content: space-around;
            background: #0073e6;
            border-radius: 5px 5px 0 0;
            overflow: hidden;
            padding: 0px 0;
        }}
        .tab-button {{
            flex: 1;
            padding: 5px;
            text-align: center;
            cursor: pointer;
            background: #0073e6;
            color: white;
            font-size: 18px;
            font-weight: bold;
            border: none;
            outline: none;
            transition: background 0.3s;
        }}
        .tab-button:hover {{
            background: #005bb5;
        }}
        .tab-button.active {{
            background: #005bb5;
        }}
        .tab-content {{
            display: none;
            padding: 20px;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }}
        .tab-content.active {{
            display: block;
        }}
        .explanation {{
            background: #f9f9f9;
            padding: 15px;
            border-left: 5px solid #0073e6;
            margin-bottom: 10px;
        }}
        img {{
            width: 100%;
            max-width: 900px;
            display: block;
            margin: 20px auto;
            border-radius: 5px;
        }}
    </style>
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tabbuttons;
            
            // Hide all tab content
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}

            // Remove active class from all tab buttons
            tabbuttons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabbuttons.length; i++) {{
                tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
            }}

            // Show the current tab, and add "active" class to the clicked button
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }}

        // Set default tab to open
        document.addEventListener("DOMContentLoaded", function () {{
            document.getElementById("defaultTab").click();
        }});
    </script>
</head>
<body>
    <div class="container">
        <h1>Panel 6 - Logs Analysis Report</h1>

        <div class="tabs">
            <button class="tab-button" onclick="openTab(event, 'metrics')" id="defaultTab">Key Metrics</button>
            <button class="tab-button" onclick="openTab(event, 'popularity')">Popularity</button>
            <button class="tab-button" onclick="openTab(event, 'completion_stats')">Completion Stats</button>
        </div>

        <!-- Tab 1: Key Metrics -->
        <div id="metrics" class="tab-content active">
            <h2>Interaction Metrics</h2>
            <ul>
                <li><b>Total Sessions:</b> {len(df_metrics)}</li>
                <li><b>Completed Sessions:</b> {df_metrics['is_complete'].sum()}</li>
                <li><b>Incomplete Sessions:</b> {len(df_metrics) - df_metrics['is_complete'].sum()}</li>
                <li><b>New Sessions:</b> {df_metrics['is_new'].sum()}</li>
                <li><b>New and Complete Sessions:</b> {len(df_metrics[(df_metrics['is_complete']) & (df_metrics['is_new'])])}</li>
                <li><b>Average Duration:</b> {df_metrics['duration'].mean():.2f} seconds</li>
                <li><b>Average Duration:</b> {df_metrics['duration'][df_metrics['duration'] < 1500].mean():.2f} seconds</li>
            </ul>

            <h2>Definitions</h2>
            <div class="explanation">
                <h3>What is a Completed Session?</h3>
                <p>A session is considered <b>complete</b> if it contains both a <i>start signal</i> and an <i>end signal</i>.</p>
                <ul>
                    <li>The session <b>starts</b> when the user closes the Instructions page (<code>Button_close_Instructions</code>).</li>
                    <li>The session <b>ends</b> when the user presses the Finish button (<code>Finish_virtualNavigation</code>).</li>
                </ul>
            </div>

            <div class="explanation">
                <h3>What is a New Session?</h3>
                <p>A session is classified as <b>new</b> if it corresponds to the Panel6 version which includes the event <code>UI_ClosePanoPage</code>, which indicates that a visitors has ended the interaction with exhibition content.</p>
            </div>
        </div>

        <!-- Tab 2: Session Duration -->
        <div id="popularity" class="tab-content">
            <h2>Session Duration Distribution</h2>
            <img src="plots/session_duration_hist.png">
        </div>

        <!-- Tab 3: Completed vs Incomplete -->
        <div id="completion_stats" class="tab-content">
            <h2>Completed vs. Incomplete Sessions</h2>
            <img src="plots/completed_sessions.png">
        </div>
    </div>
</body>
</html>
"""

# Save HTML report
with open(f"{OUTPUT_DIR}/logs_report.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Full-width report with tabs saved to {OUTPUT_DIR}/logs_report.html")