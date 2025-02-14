import pandas as pd
import numpy as np
import re
from automaton import machines

class SessionFSM:
    START_EVENT = "Button_close_Instructions"
    EXHIBIT_PREFIX = "Exhibit_"
    MENUEXHIBIT_PREFIX = "MenuExhibitButton"
    CONTENT_PREFIX = "OpenContent_"
    CTRL_PREFIX = "CTRL_"
    IMAGE_ZOOM = "UI_OpenZoomImage_Button"
    UI_CLOSE = "UI_ClosePanoPagePanelClose_Button"
    SESSION_END = "Finish_virtualNavigation"

    states = [
        'IDLE',           # Waiting for Button_close_Instructions
        'SESSION_ACTIVE', # Inside a session, tracking interactions
        'EXHIBIT_VIEW',   # Inside an exhibit (Exhibit_*)
        'CONTENT_VIEW',   # Viewing exhibit content (OpenContent_*)
        'SESSION_END'     # Ending session (Finish_virtualNavigation)
    ]

    transitions = [
        ('IDLE', 'SESSION_ACTIVE', 'start_session'),   # Start Session
        ('SESSION_ACTIVE', 'EXHIBIT_VIEW', 'enter_exhibit'),  # Enter Exhibit
        ('EXHIBIT_VIEW', 'CONTENT_VIEW', 'view_content'),   # View Exhibit Content
        ('CONTENT_VIEW', 'SESSION_ACTIVE', 'exit_exhibit')  # Close Exhibit
    ]

    # Ensure session can be closed from any state
    for state in states:
        transitions.append((state, "IDLE", "close_session"))

    def __init__(self, session_data):
        """Initialize FSM and process session logs"""
        self.fsm = machines.FiniteMachine()
        self.sessions = []
        self.current_session = None
        self.current_event = None

        # Set up FSM states and transitions
        for state in self.states:
            self.fsm.add_state(state)

        for transition in self.transitions:
            self.fsm.add_transition(*transition)

        self.fsm.default_start_state = 'IDLE'
        self.fsm.initialize()

        # Process session data
        self.process_sessions(session_data)

    def process_sessions(self, df):
        """Iterate through session data and process each row."""
        for _, row in df.iterrows():
            action, timestamp = row["Action"], row["Timestamp"]

            if action == self.SESSION_END:
                self._close_session(timestamp)
                continue

            if self.fsm.current_state == 'IDLE' and action == self.START_EVENT:
                self._start_session(timestamp)

            elif self.fsm.current_state == 'SESSION_ACTIVE' and (action.startswith(self.EXHIBIT_PREFIX) or action.startswith(self.MENUEXHIBIT_PREFIX)):
                self._enter_exhibit(action, timestamp)

            elif self.fsm.current_state == 'EXHIBIT_VIEW' and action.startswith(self.EXHIBIT_PREFIX):
                self._change_exhibit(action, timestamp)

            elif self.fsm.current_state == 'EXHIBIT_VIEW' and action.startswith(self.CONTENT_PREFIX):
                self._view_content(action, timestamp)

            elif self.fsm.current_state == 'CONTENT_VIEW' and action.startswith(self.CTRL_PREFIX):
                self.current_event["actions"].append((action, timestamp))

            elif self.fsm.current_state == 'CONTENT_VIEW' and action.startswith(self.IMAGE_ZOOM):
                self.current_event["actions"].append((action, timestamp))

            elif self.fsm.current_state == "CONTENT_VIEW" and action.startswith(self.UI_CLOSE):
                self._exit_exhibit(timestamp)

    def _start_session(self, timestamp):
        """Handles the start of a session."""
        self.fsm.process_event('start_session')
        self.current_session = {"start_time": timestamp, "events": [], "end_time": None}

    def _enter_exhibit(self, action, timestamp):
        """Handles entering an exhibit."""
        self.fsm.process_event('enter_exhibit')
        self.current_event = {"exhibit": action, "exhibit_id": None, "start_time": timestamp, "end_time": None, "actions": []}

    def _change_exhibit(self, action, timestamp):
        """Handles transitioning between exhibits."""
        self.current_event["end_time"] = timestamp
        self.current_session["events"].append(self.current_event)
        self.current_event = {"exhibit": action, "exhibit_id": None, "start_time": timestamp, "end_time": None, "actions": []}

    def _view_content(self, action, timestamp):
        """Handles viewing content inside an exhibit."""
        self.fsm.process_event('view_content')
        match = re.search(r"ExhibitID_(\d+)", action)
        if match:
            self.current_event["exhibit_id"] = match.group(1)
        self.current_event["actions"].append((action, timestamp))

    def _exit_exhibit(self, timestamp):
        """Handles exiting an exhibit."""
        self.fsm.process_event('exit_exhibit')
        self.current_event["end_time"] = timestamp
        self.current_session["events"].append(self.current_event)
        self.current_event = None

    def _close_session(self, timestamp):
        """Handles session closure."""
        if self.current_session:
            self.current_session["end_time"] = timestamp
            self.sessions.append(self.current_session)
            self.current_session = None
        self.fsm.process_event("close_session")

    def generate_session_dataframe(self):
        """Converts sessions into a DataFrame."""
        session_data = []
        action_data = []

        for session_id, session in enumerate(self.sessions):
            session_start = session["start_time"]
            session_end = session["end_time"]
            session_duration = session_end - session_start if session_end else None

            for event in session["events"]:
                event_start = event["start_time"]
                event_end = event["end_time"]
                event_duration = event_end - event_start if event_end else None
                actions_count = len(event["actions"])
                exhibit_id = event["exhibit_id"]

                session_data.append([
                    session_id, session_start, session_end, session_duration,
                    event["exhibit"], exhibit_id, event_start, event_end, event_duration, actions_count
                ])

                action_timestamps = [action[1] for action in event["actions"]]
                action_types = [action[0] for action in event["actions"]]
                action_ids = [
                    (match.group(1) if (match := re.search(r"ItemID_(\d+)", action[0])) else None)
                    for action in event["actions"]
                ]

                action_durations = np.diff(action_timestamps + [event_end]) if action_timestamps else [None] * len(action_timestamps)

                for action_type, action_timestamp, action_duration, action_id in zip(action_types, action_timestamps, action_durations, action_ids):
                    action_data.append([
                        session_id, session_start, session_end, session_duration,
                        event["exhibit"], exhibit_id, event_start, event_end, event_duration, actions_count,
                        action_type, action_id, action_timestamp, action_duration
                    ])

        df_sessions = pd.DataFrame(
            session_data,
            columns=[
                "SESSION_ID", 
                "SESSION_START", 
                "SESSION_END", 
                "SESSION_DURATION", 
                "EXHIBIT", 
                "EXHIBIT_ID", 
                "EVENT_START", 
                "EVENT_END", 
                "EVENT_DURATION", 
                "ACTIONS_COUNT"
            ]
        )

        df_actions = pd.DataFrame(
            action_data,
            columns=[
                "SESSION_ID", 
                "SESSION_START", 
                "SESSION_END", 
                "SESSION_DURATION", 
                "EXHIBIT", 
                "EXHIBIT_ID", 
                "EVENT_START",
                "EVENT_END", 
                "EVENT_DURATION",
                "ACTIONS_COUNT",
                "ACTION",
                "ITEM_ID",
                "ACTION_TIMESTAMP", 
                "ACTION_DURATION"
            ]
        )

        return df_sessions, df_actions
