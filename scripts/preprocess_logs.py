import os
import numpy as np
import seaborn as sns
import pandas as pd
import ast
import re
import json
import pickle
from event_processor import SessionFSM

def get_json_files(directory, word: str = "Interactions"):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.json') and word in f]

def read_json_files(files):
    logs = []
    all_sessions = []

    for log in files:
        with open(log, "r", encoding="utf-8") as file:
            data = json.load(file)

            processed_logs = [
                (item["action"], *ast.literal_eval(item["positionScreen"]), float(item["time"]))
                for item in data
            ]

            log_session = np.array(processed_logs, dtype=object)
            logs.append(log_session)

            session_info = {
                "filename": os.path.basename(log),
                "num_actions": len(log_session),
                "is_complete": is_session_complete(log_session),
                "is_new": is_session_new(log_session),
                "duration": log_session[-1][-1] - log_session[0][-1] if len(log_session) > 0 else 0
            }

            all_sessions.append(session_info)
    return logs, pd.DataFrame(all_sessions)

def find_indices(array, regex_pattern):
    """
    Find indices of rows in a NumPy array where the first column matches a given regex pattern.

    Parameters:
    - array (numpy.ndarray): 2D NumPy array where the first column contains strings.
    - regex_pattern (str): Regular expression pattern to match.

    Returns:
    - numpy.ndarray: Indices of matching rows.
    """
    pattern = re.compile(fr"{regex_pattern}")
    matching_indices = np.where(np.vectorize(lambda x: bool(pattern.match(str(x))))(array))[0]
    return matching_indices

def is_session_complete(array)-> bool:
    try:
        start_label = "Button_close_Instructions"
        end_label   = "Finish_virtualNavigation"
        _ = find_indices(array, start_label)[0]
        _ = find_indices(array, end_label)[0]
        return True

    except:
        # No Start and End signal in array
        return False

def is_session_new(array)-> bool:
    try:
        end_signal = "UI_ClosePanoPage"
        _ = find_indices(array, end_signal)[0]
        return True

    except:
        # No Start and End signal in array
        return False

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "../data")  # Store outputs within project
LOG_DIR = "../data/logs"
LOG_TYPE = "Interactions"
VERSION = "new"

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/plots", exist_ok=True)

    log_files = get_json_files(LOG_DIR, LOG_TYPE)
    logs, df_metrics = read_json_files(log_files)

    df_metrics.to_csv(f"{OUTPUT_DIR}/logs_metrics_{VERSION}.csv", index=False)

    # Save logs as pickle
    with open(f"{OUTPUT_DIR}/logs_{VERSION}.pkl", "wb") as file:
        pickle.dump(logs, file)

    # Good Logs
    good_logs = [log for log in logs if is_session_complete(log)]
    good_logs = [log for log in good_logs if is_session_new(log)]

    # Save good logs as pickle file
    with open(f"{OUTPUT_DIR}/good_logs_{VERSION}.pkl", "wb") as file:
        pickle.dump(good_logs, file)

    # Events Detection
    good_sessions = np.concatenate(good_logs)[:,[0,3]]
    df = pd.DataFrame(good_sessions, columns=["Action", "Timestamp"])
    df["Timestamp"] = df["Timestamp"].astype(float)

    session_fsm = SessionFSM(df)
    session_df, action_df = session_fsm.generate_session_dataframe()

    session_df.to_csv(f"{OUTPUT_DIR}/session_data_{VERSION}.csv", index=False)
    action_df.to_csv(f"{OUTPUT_DIR}/action_data_{VERSION}.csv", index=False)

    print(f"Processed {len(log_files)} log files. Metrics saved to {OUTPUT_DIR}/logs_metrics.csv")
