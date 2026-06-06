import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, time, timedelta
import json
import os  # ✅ needed for os.path.exists
from pathlib import Path  # ✅ ensures banner path works on Streamlit Cloud

# --- CONFIG ---
st.set_page_config(page_title="Friday Sail & Sizzle", layout="wide")

# --- TOP BANNER IMAGE ---
BANNER_IMAGE = "fss_mob_banner.png"  # in repo root
BANNER_PATH = Path(__file__).parent / BANNER_IMAGE  # ✅ robust path (same folder as this script)

if BANNER_PATH.exists():
    st.image(str(BANNER_PATH), use_container_width=True)
else:
    st.warning(f"Banner image not found: {BANNER_PATH}")

# --- TITLE ---
st.title("Friday Sail & Sizzle - 2026 MOB - Entry Form")
    
# --- INSTRUCTIONS ---
st.markdown("""
### ℹ️ Instructions
To log your race:
- Ensure the entry is dated fo the **Friday**- Add up to three crew members for this race- Provide your lap time in **HH:MM:SS** format using the time picker
- Your result will appear on the weekly leaderboard

**Note:** Both weekly and annual leaderboards are displayed. If no new entry is submitted this week, the last race's results will continue to show.
""")

# --- SCORING SYSTEM INFO ---
st.markdown("""
### ⛵ Scoring System
Each race is scored based on the number of participating boats:
- **1 boat** → 1 point  
- **2 boats** → 2 pts for 1st, 1 for 2nd  
- **3 boats** → 3 pts / 2 pts / 1 pt  
- **4+ boats** → 4 pts for 1st, 3 pts for 2nd, 2 pts for 3rd, 1 pt for all others  

Scoring is ranked by **Corrected Time using Portsmouth-based multiplier**.
""")

# --- AUTH ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
service_account_info = st.secrets["GOOGLE_SERVICE_ACCOUNT"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
gc = gspread.authorize(creds)
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1mAUmYrkc1n37vrTkiZ-J8OsI5SnA7r-nYmdPIR04OZY/edit")
worksheet = sh.worksheet("Race Entries")

# --- Portsmouth Ratings (simplified multiplier: 100 / rating) ---
portsmouth_index = {
    "29er": 78.0,
    "Abbott 22": 95.0,
    "Albacore": 92.8,
    "Ancom 23": 95.0,
    "Capricorn": 91.0,
    "Catalina 22": 96.3,
    "CL16": 97.5,
    "Crown 26": 91.5,
    "Hobie 14": 99.0,
    "Hobie 16": 76.0,
    "Hobie 17": 79.0,
    "Hobie 18": 74.0,
    "Hobie Tiger (F18)": 69.3,
    "Hobie Wildcat": 69.0,
    "Hobie Getaway": 83.0,
    "Hobie Wave": 92.0,
    "Hobie Dragoon": 85.0,
    "Hobie FX One": 70.0,
    "Hobie 20": 73.0,
    "Hobie 21": 72.0,    
    "Hunter 22": 90.0,
    "Laser": 91.1,
    "Laser II": 88.0,
    "Mutineer 15": 91.4,
    "Optimist": 123.6,
    "Paceship 23": 96.0,
    "Sandpiper": 105.0,
    "Schock 23": 89.0,
    "Shark 24": 107,
    "Siren": 101.2,
    "Sirius 21/22": 92.5,
    "Soling": 83.0,
    "Star": 87.0,
    "Tanzer 22": 94.0,
    "Tanzer 26": 90.5,
    "Tanzer 7.5": 91.0,
    "Venture macgregor": 96.0,
    "Wayfarer": 95.5,
    "Y-Flyer": 90.0,
    "Not Listed - Add in comments": 100.0
}

# --- FORM ---
with st.form("race_entry_form"):
    st.subheader("Race Details")

    race_date = st.date_input("Race Date (Fridays only)", value=datetime.today())
    boat_name = st.text_input("Boat Name")
    skipper_name = st.text_input("Skipper Name or Nickname")
    boat_type = st.selectbox("Boat Type", sorted(list(portsmouth_index.keys())))

    col1, col2, col3 = st.columns(3)
    with col1:
        crew_member_1 = st.text_input("Crew Member 1")
    with col2:
        crew_member_2 = st.text_input("Crew Member 2")
    with col3:
        crew_member_3 = st.text_input("Crew Member 3")

    lap_time = st.time_input(
        "Lap Time (HH:MM:SS)",
        value=time(0, 30, 0),
        step=1
    )

    comments = st.text_area("Comments or Improvement Ideas")

    submitted = st.form_submit_button("Submit Entry")

    if submitted:
        if race_date.weekday() != 4:
            st.error("Race date must be a Friday.")
        else:
            elapsed = timedelta(
                hours=lap_time.hour,
                minutes=lap_time.minute,
                seconds=lap_time.second
            )
            if elapsed <= timedelta(seconds=0):
                st.error("Lap time must be greater than 00:00:00.")
            else:
                portsmouth_rating = portsmouth_index.get(boat_type, 100.0)
                multiplier = 100.0 / portsmouth_rating if portsmouth_rating else 1.0
                corrected = timedelta(seconds=round(elapsed.total_seconds() * multiplier))

                row = [
                    race_date.strftime("%Y-%m-%d"),
                    boat_name,
                    skipper_name,
                    boat_type,
                    crew_member_1,
                    crew_member_2,
                    crew_member_3,
                    "",
                    "",
                    str(elapsed),
                    str(corrected),
                    comments,
                    datetime.now().isoformat()
                ]
                worksheet.append_row(row)
                st.success("Race entry submitted successfully!")

                st.markdown("""
                <div style="text-align:center; padding:30px;">
                <h2>🔥 Off to the BBQ!</h2>
                <p style="font-size:18px;">
                Nice work skipper — head up to the dock,
                grab a cold one and enjoy the sizzle.
                </p>
                </div>
                """, unsafe_allow_html=True)

                st.balloons()


# --- WEEKLY LEADERBOARD ---
st.subheader("\U0001F4CA Weekly Leaderboard")

try:
    expected_headers = [
        "Race Date", "Boat Name", "Skipper Name or Nickname", "Boat Type",
        "Crew Member 1", "Crew Member 2", "Crew Member 3",
        "Start Time", "Finish Time", "Elapsed Time", "Corrected Time",
        "Comments or Improvement Ideas", "Submission Timestamp"
    ]

    data = pd.DataFrame(worksheet.get_all_records(expected_headers=expected_headers))
    data["Race Date"] = pd.to_datetime(data["Race Date"], errors="coerce")
    data = data.dropna(subset=["Race Date"])

    latest_friday = data["Race Date"].max()
    week_data = data[data["Race Date"] == latest_friday].copy()

    # Filter malformed corrected times
    week_data = week_data[week_data["Corrected Time"].astype(str).str.strip() != ""]
    week_data = week_data[~week_data["Corrected Time"].astype(str).str.contains("nan", na=False)]

    if week_data.empty:
        st.warning("No valid entries found for the latest race. Check formatting or try re-entering a log.")
    else:
        week_data["Corrected Time"] = pd.to_timedelta(week_data["Corrected Time"], errors="coerce")
        week_data["Elapsed Time"] = pd.to_timedelta(week_data["Elapsed Time"], errors="coerce")
        week_data = week_data.dropna(subset=["Corrected Time", "Elapsed Time"])
        week_data = week_data.sort_values("Corrected Time")

        week_data["Corrected Time"] = week_data["Corrected Time"].dt.components.apply(
            lambda row: f"{int(row.hours):02}:{int(row.minutes):02}:{int(row.seconds):02}", axis=1
        )
        week_data["Elapsed Time"] = week_data["Elapsed Time"].dt.components.apply(
            lambda row: f"{int(row.hours):02}:{int(row.minutes):02}:{int(row.seconds):02}", axis=1
        )

        num_boats = len(week_data)

        def assign_points(rank, total):
            if total == 1:
                return 1
            elif total == 2:
                return 2 - rank if rank < 2 else 0
            elif total == 3:
                return max(0, 3 - rank)
            elif total >= 4:
                if rank == 0:
                    return 4
                elif rank == 1:
                    return 3
                elif rank == 2:
                    return 2
                else:
                    return 1
            return 0

        week_data["Points"] = [assign_points(i, num_boats) for i in range(num_boats)]

        st.dataframe(week_data[[
            "Skipper Name or Nickname",
            "Boat Name",
            "Elapsed Time",
            "Corrected Time",
            "Points",
            "Submission Timestamp"
        ]])

    st.subheader("\U0001F3C6 Annual Leaderboard")
    data = data[data["Corrected Time"].astype(str).str.strip() != ""]
    data = data[~data["Corrected Time"].astype(str).str.contains("nan", na=False)]
    data["Corrected Time"] = pd.to_timedelta(data["Corrected Time"], errors="coerce")
    data["Elapsed Time"] = pd.to_timedelta(data["Elapsed Time"], errors="coerce")
    data = data.dropna(subset=["Corrected Time", "Elapsed Time"])
    data = data.sort_values("Race Date")
    data["Race Year"] = data["Race Date"].dt.year

    def compute_annual_points(df):
        result_rows = []
        for date, group in df.groupby("Race Date"):
            group = group.sort_values("Corrected Time").reset_index(drop=True)
            total = len(group)
            for i, row in group.iterrows():
                points = assign_points(i, total)
                result_rows.append({
                    "Skipper Name or Nickname": row["Skipper Name or Nickname"],
                    "Race Year": row["Race Year"],
                    "Points": points
                })
        result_df = pd.DataFrame(result_rows)
        return result_df.groupby(["Race Year", "Skipper Name or Nickname"]).sum().reset_index()

    if data.empty:
        st.info("No valid annual leaderboard entries are available yet.")
    else:
        annual = compute_annual_points(data)
        if annual.empty:
            st.info("No valid annual leaderboard entries are available yet.")
        else:
            latest_year = annual["Race Year"].max()
            leaderboard = annual[annual["Race Year"] == latest_year].sort_values("Points", ascending=False)
            st.dataframe(leaderboard)

    st.subheader("\U0001F3C6 Annual Crew Participation")
    crew_columns = ["Crew Member 1", "Crew Member 2", "Crew Member 3"]
    crew_rows = []
    for _, row in data[crew_columns].fillna("").iterrows():
        crew_names = {str(name).strip() for name in row.values if str(name).strip()}
        crew_rows.extend(crew_names)

    if crew_rows:
        crew_counts = pd.Series(crew_rows).value_counts().reset_index()
        crew_counts.columns = ["Crew Member", "Crewed Count"]
        crew_counts = crew_counts.sort_values("Crewed Count", ascending=False)
        st.dataframe(crew_counts)
    else:
        st.info("No crew member data is available yet.")

except Exception as e:
    st.warning(f"Could not load leaderboards: {e}")






