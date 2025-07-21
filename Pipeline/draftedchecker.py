import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

# Suppress warnings for a cleaner output
warnings.filterwarnings('ignore')

# --- Part 1: Data Loading ---

def standardize_player_name(name):
    """Standardizes player names for consistent merging across files."""
    if pd.isna(name):
        return None
    name = str(name).lower()
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)     # Normalize whitespace
    name = re.sub(r'\s+(jr|sr|ii|iii|iv)$', '', name) # Remove suffixes
    return name.strip()

# --- Main Script Execution ---

print("Starting the NBA Draft Analysis Pipeline...")

# --- Load Data from Provided Files ---
try:
    # **CORRECTED: Use pd.read_excel for the .xlsx file**
    combine_file = 'combine_participants_nba_careers_sorted.xlsx'
    combine_df = pd.read_excel(combine_file)
    print(f"Successfully loaded '{combine_file}'.")

    # Load the pre-cleaned draft history CSV
    draft_history_file = 'cleaned_draft_history.csv'
    draft_history_df = pd.read_csv(draft_history_file)
    print(f"Successfully loaded '{draft_history_file}'.")

except FileNotFoundError as e:
    print(f"\n--- FATAL FILE NOT FOUND ERROR ---\n{e}\nPlease ensure both '{combine_file}' and '{draft_history_file}' are in the same directory as this script.\n---------------------------------")
    exit()
except Exception as e:
    print(f"\n--- FATAL FILE LOADING ERROR ---\nAn error occurred while reading the files: {e}\n---------------------------------")
    exit()

# --- Part 2: Filter to Drafted Players Only ---
print("Filtering for players who participated in the combine and were drafted...")

# Standardize player names in both dataframes for an accurate comparison.
combine_df['Player_std'] = combine_df['Player'].apply(standardize_player_name)
draft_history_df['Player_std'] = draft_history_df['Player'].apply(standardize_player_name)

# Create a Python 'set' of all drafted players for very fast lookup.
drafted_players_set = set(draft_history_df['Player_std'])

# Filter the combine dataframe to keep only players who were drafted.
drafted_combine_players_df = combine_df[combine_df['Player_std'].isin(drafted_players_set)].copy()

# Export the list of drafted players as requested
output_filename = 'drafted_combine_participants.csv'
drafted_combine_players_df.to_csv(output_filename, index=False)
print(f"Successfully filtered the list. A file named '{output_filename}' with {len(drafted_combine_players_df)} drafted players has been created.")
