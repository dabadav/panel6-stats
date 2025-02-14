import pandas as pd
import matplotlib.pyplot as plt

def time_metrics(df):
    # Time per Item
    time_per_item = df.groupby("ITEM_ID")["ACTION_DURATION"].sum().dropna()
    time_per_item.plot(kind="bar", title="Total Time Spent per Item", xlabel="Item ID", ylabel="Time Spent (seconds)")
    plt.show()

    # Number of Interactions per Item
    interactions_per_item = df.groupby("ITEM_ID")["ACTION"].count().dropna()
    interactions_per_item.plot(kind="bar", title="Number of Interactions per Item", xlabel="Item ID", ylabel="Interaction Count")
    plt.show()

    # Overall Time per Session
    session_durations = df.groupby("SESSION_ID")["SESSION_DURATION"].first()
    session_durations.plot(kind="bar", title="Total Session Durations", xlabel="Session ID", ylabel="Duration (seconds)")
    plt.show()

    # Display numeric results in a table
    result_df = pd.DataFrame({
        "Total Time Spent (s)": time_per_item,
        "Number of Interactions": interactions_per_item
    }).fillna(0)

    return result_df