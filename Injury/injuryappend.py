import pandas as pd
import re

def extract_injury_type(reason):
    reason = str(reason).lower()
    for keyword in [
        'acl', 'achilles', 'mcl', 'meniscus', 'groin', 'hamstring', 'patella', 'knee', 'back',
        'shoulder', 'ankle', 'concussion', 'foot', 'hand', 'wrist', 'elbow', 'hip', 'fracture', 'surgery'
    ]:
        if re.search(rf'\b{keyword}\b', reason):
            return keyword.capitalize()
    return None

def load_and_clean_injury_data(csv_path):
    # Load with known column names
    df = pd.read_csv(csv_path, skiprows=1, names=["Player", "Status", "Reason", "Team", "Game", "Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Reason"] = df["Reason"].fillna("")
    df["InjuryType"] = df["Reason"].apply(extract_injury_type)
    return df

def group_injury_spans(df):
    grouped = df.groupby(["Player", "Team", "Reason"])
    spans = []
    for (player, team, reason), group in grouped:
        start = group["Date"].min()
        end = group["Date"].max()
        spans.append({
            "Player": player,
            "Team": team,
            "StartDate": start.date() if pd.notnull(start) else None,
            "EndDate": end.date() if pd.notnull(end) else None,
            "InjuryLengthDays": (end - start).days if pd.notnull(start) and pd.notnull(end) else None,
            "InjuryNotes": reason,
            "InjuryType": extract_injury_type(reason),
            "Year": start.year if pd.notnull(start) else None
        })
    return pd.DataFrame(spans)

def append_to_existing(injury_spans_df, old_file_path, new_file_path):
    # Load old data
    old_df = pd.read_excel(old_file_path)

    # Combine
    combined = pd.concat([old_df, injury_spans_df], ignore_index=True)

    # Save updated file
    combined.to_excel(new_file_path, index=False)
    print(f"✅ New file saved: {new_file_path}")

if __name__ == "__main__":
    # File paths
    csv_2023 = "Injury Database - 2023-24 Regular Season.csv"
    csv_2024 = "Injury Database - 2024-25 Regular Season.csv"
    old_spans_xlsx = "injury_spans_2000_2023.xlsx"
    new_spans_xlsx = "injury_spans_2000_2025.xlsx"

    # Process
    df_2023 = load_and_clean_injury_data(csv_2023)
    df_2024 = load_and_clean_injury_data(csv_2024)
    combined_new = pd.concat([df_2023, df_2024], ignore_index=True)
    new_spans = group_injury_spans(combined_new)
    append_to_existing(new_spans, old_spans_xlsx, new_spans_xlsx)