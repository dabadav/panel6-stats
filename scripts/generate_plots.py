import os
import sys
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Define paths
DATA_DIR = Path("../data")
ASSETS_DIR = Path("assets")
LOG_FILE = "good_logs.pkl"
LOG_FILE_GOOD = "good_logs.pkl"
LOG_METRICS_FILE = "logs_metrics.csv"

def plot_session_hist(session_duration, output_dir="outputs/plots", filename="session_duration_hist.png", x_label='Time (seconds)', hist_color='blue', overwrite=False):
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    if not overwrite and os.path.exists(os.path.join(output_dir, filename)):
        print(f"Plot {filename} already exists. Skipping...")
        return

    # Plot histogram
    plt.figure(figsize=(8, 6))
    sns.histplot(session_duration,
                bins=25, color=hist_color, kde=True)  # Adjust bins as needed

    # Add labels
    plt.xlabel(f"{x_label}")
    plt.ylabel("Number of Sessions")
    plt.title(f"Session Distribution - {x_label}")

    # Add text at the top right
    plt.text(
        x=max(session_duration) * 0.95,  # X position (90% of max value)
        y=plt.gca().get_ylim()[1] * 0.95,  # Y position (90% of max height)
        s=f"N={session_duration.shape[0]}",  # The text to display
        fontsize=12,
        ha='right',  # Align text to the right
        va='top',  # Align text to the top
        bbox=dict(facecolor='white', alpha=0.5, edgecolor='black')  # Background box
    )

    # Save plot
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")

    # Close the plot to free memory
    plt.close()
    print(f"Plot saved to {save_path}")

def plot_footprint(logs, output_dir="outputs/plots", filename="footprint_heatmap.png", overwrite=False):
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    if not overwrite and os.path.exists(os.path.join(output_dir, filename)):
        print(f"Plot {filename} already exists. Skipping...")
        return

    # Define the screen resolution
    SCREEN_WIDTH = 1921
    SCREEN_HEIGHT = 1081

    # Extract x, y coordinates and convert them to integers (pixel positions)
    x_coords = logs[:, 1].astype(int)
    y_coords = logs[:, 2].astype(int)

    # Create a 2D array representing the screen
    heatmap_matrix = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH))  # (height, width)

    # Count occurrences of (x, y) positions
    for x, y in zip(x_coords, y_coords):
        if 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT:  # Ensure coordinates are within screen bounds
            heatmap_matrix[y, x] += 1  # Note: y comes first because NumPy follows (row, col)
        else:
            print(f"Bad Resolution ({x},{y})")

    # Set custom saturation range
    V_MIN = 0   # Minimum intensity (usually 0)
    # V_MAX = np.max(heatmap_matrix) * 0.5 # 50% of the max value (adjust as needed)
    V_MAX = 0.25 # 50% of the max value (adjust as needed)

    # Plot heatmap
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        heatmap_matrix,
        cmap="Reds",
        cbar=True,
        square=False,
        xticklabels=1920,
        yticklabels=1080,
        vmin=V_MIN,  # Set lower saturation level
        vmax=V_MAX   # Set upper saturation level
    )

    # Labels and title
    plt.xlabel("X Coordinate (Pixels)")
    plt.ylabel("Y Coordinate (Pixels)")
    plt.title("Touch Interaction Heatmap")

    # Flip the Y-axis (because images start from top-left)
    plt.gca().invert_yaxis()

    # Save plot
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")

    # Close the plot to free memory
    plt.close()
    print(f"Plot saved to {save_path}")

def time_metrics(df, output_dir: Path):
    # Time per Item
    time_per_item = df.groupby("ITEM_ID")["ACTION_DURATION"].sum().dropna()
    time_per_item.plot(kind="bar", title="Total Time Spent per Item", xlabel="Item ID", ylabel="Time Spent (seconds)")
    plt.savefig(output_dir / "item_duration.png", dpi=300, bbox_inches="tight")

    # Number of Interactions per Item
    interactions_per_item = df.groupby("ITEM_ID")["ACTION"].count().dropna()
    interactions_per_item.plot(kind="bar", title="Number of Interactions per Item", xlabel="Item ID", ylabel="Interaction Count")
    plt.savefig(output_dir / "item_action.png", dpi=300, bbox_inches="tight")

    # Overall Time per Session
    session_durations = df.groupby("SESSION_ID")["SESSION_DURATION"].first()
    session_durations.plot(kind="bar", title="Total Session Durations", xlabel="Session ID", ylabel="Duration (seconds)")
    plt.savefig(output_dir / "session_duration.png", dpi=300, bbox_inches="tight")


    # Display numeric results in a table
    result_df = pd.DataFrame({
        "Total Time Spent (s)": time_per_item,
        "Number of Interactions": interactions_per_item
    }).fillna(0)

    result_df.to_csv(output_dir / "time_metrics.csv")

    return result_df

if __name__ == "__main__":
    # # Load session data from pickle file
    # with open(f"{OUTPUT_DIR}/{LOG_FILE}", "rb") as file:
    #     sessions = pickle.load(file)

    metrics = pd.read_csv(DATA_DIR / LOG_METRICS_FILE)
    session_duration = np.array(metrics['duration'])
    session_interaction = np.array(metrics['num_actions'])

    # Plot session time

    overwrite_plots = False  # Set to True to overwrite existing plots
    plot_session_hist(session_duration / 60, filename="session_duration_hist_minutes.png", x_label='Time (minutes)', overwrite=overwrite_plots)
    plot_session_hist(session_duration[session_duration < 1500] / 60, filename="session_duration_hist_minutes_filtered.png", x_label='Time (minutes)', overwrite=overwrite_plots)
    plot_session_hist(session_duration, filename="session_duration_hist_seconds.png", overwrite=overwrite_plots)
    plot_session_hist(session_duration[session_duration < 1500], filename="session_duration_hist_seconds_filtered.png", overwrite=overwrite_plots)

    # Create html table with session metrics ordered by duration descending
    metrics = metrics.sort_values('duration', ascending=False)
    # Add column duration in minutes
    metrics['duration_minutes'] = metrics['duration'] / 60
    metrics['duration_hours'] = metrics['duration'] / 60 / 60
    metrics.to_html(DATA_DIR / "session_metrics.html", index=False)

    # Plot session actions
    plot_session_hist(session_interaction, filename="session_events_hist.png", x_label='Number of Events', hist_color='orange', overwrite=overwrite_plots)
    plot_session_hist(session_interaction[session_duration < 1500], filename="session_events_hist_filtered.png", x_label='Number of Events', hist_color='orange', overwrite=overwrite_plots)

    sessions = pickle.load(DATA_DIR / LOG_FILE)
    sessions_all = np.concatenate(sessions)
    print(sessions_all.shape)
    plot_footprint(sessions_all, overwrite=overwrite_plots)

    # Open action data csv
    actions = pd.read_csv(DATA_DIR / "action_data.csv")

    # actions["ITEM_ID"] = actions["ITEM_ID"].astype('int64')
    # Create html table with item_id ordered by action duration descending
    actions = actions.sort_values('ACTION_DURATION', ascending=False)
    actions = actions.dropna(subset=["ITEM_ID"])
    actions.to_html(DATA_DIR / "session_actions.html", index=False)

    df_time_metrics = time_metrics(actions, output_dir=ASSETS_DIR)

    # Plot session time
    # plot_session_time(sessions)