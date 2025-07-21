import pandas as pd
import re

def extract_injury_type(note, keywords):
    note = note.lower()
    for keyword in keywords:
        if re.search(rf'\b{keyword}\b', note):
            return keyword.capitalize()
    return None

def process_injury_periods(input_csv, output_xlsx):
    # Load CSV with no headers
    df = pd.read_csv(input_csv, header=None)
    df.columns = ['Index', 'Date', 'Team', 'Acquired', 'Relinquished', 'Notes']
    df.drop(columns=['Index'], inplace=True)

    # Parse dates and filter by year
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Year'] = df['Date'].dt.year
    df = df[(df['Year'] >= 2000) & (df['Year'] <= 2023)]

    # Fill Notes safely
    df['Notes'] = df['Notes'].fillna('').astype(str)

    # Injury keywords
    injury_keywords = [
        'acl', 'achilles', 'mcl', 'torn meniscus', 'groin', 'hamstring',
        'patella', 'knee', 'back', 'shoulder', 'ankle', 'concussion',
        'foot', 'hand', 'wrist', 'elbow', 'hip', 'fracture', 'surgery'
    ]

    # Separate Acquired (placed on IL) and Relinquished (removed from IL)
    acquired_df = df[df['Acquired'].notna()].copy()
    acquired_df['Player'] = acquired_df['Acquired']
    acquired_df['IL_Action'] = 'Acquired'
    acquired_df['InjuryType'] = acquired_df['Notes'].apply(lambda note: extract_injury_type(note, injury_keywords))

    relinquished_df = df[df['Relinquished'].notna()].copy()
    relinquished_df['Player'] = relinquished_df['Relinquished']
    relinquished_df['IL_Action'] = 'Relinquished'

    # Merge Acquired and Relinquished by Player and Team
    merged = pd.merge(
        acquired_df,
        relinquished_df,
        on=['Player', 'Team'],
        suffixes=('_start', '_end'),
        how='inner'
    )

    # Filter valid pairs (relinquish date after acquire date)
    merged = merged[merged['Date_end'] > merged['Date_start']]

    # Drop duplicate entries (optional: keep earliest matches only)
    merged = merged.sort_values(by=['Player', 'Date_start', 'Date_end'])
    merged = merged.drop_duplicates(subset=['Player', 'Date_start'], keep='first')

    # Calculate injury duration
    merged['InjuryLengthDays'] = (merged['Date_end'] - merged['Date_start']).dt.days

    # Final columns
    final = merged[[
        'Player',
        'Team',
        'Date_start',
        'Date_end',
        'InjuryLengthDays',
        'Notes_start',
        'InjuryType',
        'Year_start'
    ]].rename(columns={
        'Date_start': 'StartDate',
        'Date_end': 'EndDate',
        'Notes_start': 'InjuryNotes',
        'Year_start': 'Year'
    })

    # Save to Excel
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        final.to_excel(writer, index=False)

    print(f"✅ Injury span file saved to: {output_xlsx}")

# Example usage
if __name__ == "__main__":
    input_csv = "injury_data_1951_2023.csv"
    output_xlsx = "injury_spans_2000_2023.xlsx"
    process_injury_periods(input_csv, output_xlsx)