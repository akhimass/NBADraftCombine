import pandas as pd

# Load merged data
df = pd.read_csv("combine_participants_nba_careers.csv")

# Convert Year_clean to integer for proper sorting (handles "2010", "2011" etc)
df['Year_clean'] = pd.to_numeric(df['Year_clean'], errors='coerce')

# Sort by Player and Year
df = df.sort_values(['Player_clean', 'Year_clean']).reset_index(drop=True)

# Put player info and combine metrics first
player_cols = ['Player', 'Player_clean', 'POS_arthro', 'Year_Combine']
combine_cols = [
    'BODY FAT %', 'HAND LENGTH (inches)', 'HAND WIDTH (inches)', 'HEIGHT W/O SHOES',
    'HEIGHT W/ SHOES', 'STANDING REACH', 'WEIGHT (LBS)', 'WINGSPAN',
    'Lane Agility Time (seconds)', 'Shuttle Run (seconds)', 'Three Quarter Sprint (seconds)',
    'Standing Vertical Leap (inches)', 'Max Vertical Leap (inches)', 'Max Bench Press (repetitions)'
]
# Add columns for the season's stats, usage, and injuries (grab all other columns not above)
other_cols = [col for col in df.columns if col not in player_cols + combine_cols and not col.endswith('_clean')]

# Ensure only available columns are selected (no KeyError)
final_cols = [col for col in player_cols + combine_cols + other_cols if col in df.columns]

# Reorder columns
df = df[final_cols]

# Save to Excel (for maximum readability and filtering in Excel/Google Sheets)
df.to_excel("combine_participants_nba_careers_sorted.xlsx", index=False)
print("✅ Excel file sorted by player and year: combine_participants_nba_careers_sorted.xlsx")