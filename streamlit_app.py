import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from pathlib import Path

# --- CONFIG ---
st.set_page_config(page_title="Friday Sail & Sizzle", layout="wide")

# --- TOP BANNER IMAGE ---
BANNER_IMAGE = "fss_mob_banner.png"
BANNER_PATH = Path(__file__).parent / BANNER_IMAGE

if BANNER_PATH.exists():
    st.image(str(BANNER_PATH), width="stretch")
else:
    st.warning(f"Banner image not found: {BANNER_PATH}")

# --- TITLE ---
st.title("Friday Sail & Sizzle - 2026 MOB - Entry Form")

# --- INSTRUCTIONS ---
st.markdown("""
### ℹ️ Instructions
To log your race:
- Ensure the entry is dated for the **Friday**
- Add up to three crew members for this race
- Enter your lap time using hours, minutes, and seconds
- Your result will appear on the weekly leaderboard

**Note:** Both weekly and annual leaderboards are displayed.
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

# --- GOOGLE SHEETS AUTH ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = st.secrets.get("GOOGLE_SERVICE_ACCOUNT")

if service_account_info is None:
    st.error("Google service account credentials are not configured.")
    st.stop()

try:
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/1mAUmYrkc1n37vrTkiZ-J8OsI5SnA7r-nYmdPIR04OZY/edit"
    )
    worksheet = sh.worksheet("Race Entries")
except Exception as e:
    st.error("Unable to connect to the Google Sheets backend.")
    st.exception(e)
    st.stop()

# --- SHEET HEADERS ---
expected_headers = [
    "Race Date",
    "Boat Name",
    "Skipper Name or Nickname",
    "Boat Type",
    "Crew Member 1",
    "Crew Member 2",
    "Crew Member 3",
    "Lap Hours",
    "Lap Minutes",
    "Lap Seconds",
    "Elapsed Time",
    "Corrected Time",
    "Comments or Improvement Ideas",
    "Submission Timestamp"
]

# --- Portsmouth Ratings ---
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
    "Shark 24": 107.0,
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

def format_timedelta(td):
    if pd.isna(td):
        return ""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def assign_points(rank, total):
    if total == 1:
        return 1
    if total == 2:
        return 2 - rank if rank < 2 else 0
    if total == 3:
        return max(0, 3 - rank)
    if total >= 4:
        if rank == 0:
            return 4
        if rank == 1:
            return 3
        if rank == 2:
            return 2
        return 1
    return 0

# --- FORM ---
with st.form("race_entry_form"):
    st.subheader("Race Details")

    race_date = st.date_input("Race Date (Fridays only)", value=datetime.today())
    boat_name = st.text_input("Boat Name")
    skipper_name = st.text_input("Skipper Name or Nickname")
    boat_type = st.selectbox("Boat Type", sorted(list(portsmouth_index.keys())))

    st.markdown("### Crew")
    crew_col1, crew_col2, crew_col3 = st.columns(3)

    with crew_col1:
        crew_member_1 = st.text_input("Crew Member 1")
    with crew_col2:
        crew_member_2 = st.text_input("Crew Member 2")
    with crew_col3:
        crew_member_3 = st.text_input("Crew Member 3")

    st.markdown("### Lap Time")

    lap_col1, lap_col2, lap_col3 = st.columns(3)

    with lap_col1:
        lap_hours = st.number_input("Hours", min_value=0, max_value=23, value=0, step=1)
    with lap_col2:
        lap_minutes = st.number_input("Minutes", min_value=0, max_value=59, value=30, step=1)
    with lap_col3:
        lap_seconds = st.number_input("Seconds", min_value=0, max_value=59, value=0, step=1)

    comments = st.text_area("Comments or Improvement Ideas")

    submitted = st.form_submit_button("Submit Entry")

    if submitted:
        if race_date.weekday() != 4:
            st.error("Race date must be a Friday.")
        else:
            elapsed = timedelta(
                hours=int(lap_hours),
                minutes=int(lap_minutes),
                seconds=int(lap_seconds)
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
                    int(lap_hours),
                    int(lap_minutes),
                    int(lap_seconds),
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

# --- LEADERBOARDS ---
st.subheader("📊 Weekly Leaderboard")

try:
    data = pd.DataFrame(worksheet.get_all_records(expected_headers=expected_headers))

    if data.empty:
        st.info("No race entries yet.")
    else:
        data["Race Date"] = pd.to_datetime(data["Race Date"], errors="coerce")
        data = data.dropna(subset=["Race Date"])

        data["Lap Hours"] = pd.to_numeric(data["Lap Hours"], errors="coerce").fillna(0)
        data["Lap Minutes"] = pd.to_numeric(data["Lap Minutes"], errors="coerce").fillna(0)
        data["Lap Seconds"] = pd.to_numeric(data["Lap Seconds"], errors="coerce").fillna(0)

        # Recalculate elapsed time from lap columns every time app loads
        data["Elapsed Time"] = data.apply(
            lambda row: timedelta(
                hours=int(row["Lap Hours"]),
                minutes=int(row["Lap Minutes"]),
                seconds=int(row["Lap Seconds"])
            ),
            axis=1
        )

        # Recalculate corrected time from boat type every time app loads
        data["Corrected Time"] = data.apply(
            lambda row: timedelta(
                seconds=round(
                    row["Elapsed Time"].total_seconds()
                    * (100.0 / portsmouth_index.get(row["Boat Type"], 100.0))
                )
            ),
            axis=1
        )

        data = data[data["Elapsed Time"] > timedelta(seconds=0)]

        if data.empty:
            st.warning("No valid race entries found.")
        else:
            latest_friday = data["Race Date"].max()
            week_data = data[data["Race Date"] == latest_friday].copy()
            week_data = week_data.sort_values("Corrected Time").reset_index(drop=True)

            num_boats = len(week_data)
            week_data["Points"] = [assign_points(i, num_boats) for i in range(num_boats)]

            week_data["Elapsed Time"] = week_data["Elapsed Time"].apply(format_timedelta)
            week_data["Corrected Time"] = week_data["Corrected Time"].apply(format_timedelta)

            st.dataframe(week_data[[
                "Skipper Name or Nickname",
                "Boat Name",
                "Boat Type",
                "Elapsed Time",
                "Corrected Time",
                "Points",
                "Submission Timestamp"
            ]], width="stretch")

    # --- ANNUAL LEADERBOARD ---
    st.subheader("🏆 Annual Leaderboard")

    if data.empty:
        st.info("No annual leaderboard entries available yet.")
    else:
        data["Race Year"] = data["Race Date"].dt.year

        result_rows = []

        for race_date, group in data.groupby("Race Date"):
            group = group.sort_values("Corrected Time").reset_index(drop=True)
            total = len(group)

            for i, row in group.iterrows():
                result_rows.append({
                    "Skipper Name or Nickname": row["Skipper Name or Nickname"],
                    "Race Year": row["Race Year"],
                    "Points": assign_points(i, total)
                })

        annual = pd.DataFrame(result_rows)

        if annual.empty:
            st.info("No annual leaderboard entries available yet.")
        else:
            annual = annual.groupby(
                ["Race Year", "Skipper Name or Nickname"],
                as_index=False
            )["Points"].sum()

            latest_year = annual["Race Year"].max()
            leaderboard = annual[annual["Race Year"] == latest_year].sort_values(
                "Points", ascending=False
            )

            st.dataframe(leaderboard, width="stretch")

    # --- ANNUAL CREW PARTICIPATION ---
    st.subheader("👥 Annual Crew Participation")

    if data.empty:
        st.info("No crew participation data available yet.")
    else:
        crew_columns = ["Crew Member 1", "Crew Member 2", "Crew Member 3"]
        crew_rows = []

        for _, row in data[crew_columns].fillna("").iterrows():
            crew_names = {str(name).strip() for name in row.values if str(name).strip()}
            crew_rows.extend(crew_names)

        if crew_rows:
            crew_counts = pd.Series(crew_rows).value_counts().reset_index()
            crew_counts.columns = ["Crew Member", "Crewed Count"]
            crew_counts = crew_counts.sort_values("Crewed Count", ascending=False)
            st.dataframe(crew_counts, width="stretch")
        else:
            st.info("No crew member data is available yet.")

except Exception as e:
    st.warning(f"Could not load leaderboards: {e}")