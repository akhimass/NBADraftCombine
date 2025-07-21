import pandas as pd
import re
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import numpy as np

# --- 1. Load the Raw Data ---
# Make sure these files are in the same directory as your script
try:
    drafted_df = pd.read_csv('drafted_combine_participants.csv')
    injury_df = pd.read_csv('injury_data_2009_2023new.csv')
    print("Files loaded successfully.")
except FileNotFoundError:
    print("Error: Make sure 'drafted_combine_participants.csv' and 'injury_data_2009_2023new.csv' are in the correct directory.")
    exit()


# --- 2. Clean and Prepare the Data ---
print("Cleaning and preparing data...")

# Clean column names by stripping whitespace
drafted_df.columns = drafted_df.columns.str.strip()
injury_df.columns = ['ID', 'Date', 'Team', 'Relinquished', 'Player', 'Notes'] # Rename injury data columns

# --- Robustly convert height columns ---
def convert_height_to_inches(height_str):
    if isinstance(height_str, str) and "'" in height_str:
        try:
            parts = height_str.replace("''", "").split("'")
            feet = int(parts[0].strip())
            inches = float(parts[1].strip())
            return (feet * 12) + inches
        except (ValueError, IndexError):
            return np.nan # Return a missing value if conversion fails
    return np.nan

# --- Clean and convert object columns to numeric ---
def clean_and_convert_to_numeric(series):
    if series.dtype == 'object':
        series = series.str.replace("'", "").str.replace('"', "").str.replace('%', "").str.strip()
        return pd.to_numeric(series, errors='coerce')
    return series

# Apply cleaning functions
drafted_df['HEIGHT W/O SHOES'] = drafted_df['HEIGHT W/O SHOES'].apply(convert_height_to_inches)
drafted_df['HEIGHT W/ SHOES'] = drafted_df['HEIGHT W/ SHOES'].apply(convert_height_to_inches)
drafted_df['STANDING REACH'] = drafted_df['STANDING REACH'].apply(convert_height_to_inches)
drafted_df['WINGSPAN'] = drafted_df['WINGSPAN'].apply(convert_height_to_inches)

numeric_cols = [
    'BODY FAT %', 'HAND LENGTH (inches)', 'HAND WIDTH (inches)', 'WEIGHT (LBS)',
    'Lane Agility Time', 'Shuttle Run', 'Three Quarter Sprint',
    'Standing Vertical Leap', 'Max Vertical Leap', 'Max Bench Press'
]
for col in numeric_cols:
    if col in drafted_df.columns:
        drafted_df[col] = clean_and_convert_to_numeric(drafted_df[col])


# --- Merge the datasets ---
# Clean player names for a more reliable merge
def clean_player_name(name):
    if isinstance(name, str):
        return name.lower().strip().replace('.','').replace("'",'')
    return ''

drafted_df['Player_clean'] = drafted_df['Player'].apply(clean_player_name)
injury_df['Player_clean'] = injury_df['Player'].apply(clean_player_name)

# Merge on the cleaned player name
merged_df = pd.merge(drafted_df, injury_df[['Player_clean', 'Notes']], on='Player_clean', how='left')

# Save the main cleaned dataset for Tableau
merged_df.to_csv('merged_combine_injury_data.csv', index=False)
print("Successfully created 'merged_combine_injury_data.csv' for your Tableau dashboards.")


# --- 3. Run the Predictive Model to Get Feature Importance ---
print("Running predictive model to calculate feature importances...")

# Define the features (combine metrics) and the target (Win Shares)
features = [
    'WINGSPAN', 'STANDING REACH', 'WEIGHT (LBS)',
    'Standing Vertical Leap', 'Lane Agility Time', 'Three Quarter Sprint',
    'Max Vertical Leap', 'BODY FAT %', 'Shuttle Run',
    'Max Bench Press', 'HAND WIDTH (inches)', 'HAND LENGTH (inches)'
]
target = 'W' # Using 'W' for Win Shares from the dataset

# Create a modeling dataframe, dropping rows where feature or target data is missing
model_df = merged_df.dropna(subset=features + [target])

X = model_df[features]
y = model_df[target]

# Initialize and train the Random Forest model
# n_estimators is the number of trees in the forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, oob_score=True)
rf_model.fit(X, y)

# Extract the feature importances
importance_df = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf_model.feature_importances_
})

# Sort by importance
importance_df = importance_df.sort_values(by='Importance', ascending=False)

# Save the feature importance data to a CSV for Tableau
importance_df.to_csv('feature_importance.csv', index=False)
print("Successfully created 'feature_importance.csv' for your 'Most Predictive Metrics' chart.")
print("\nHere is the raw feature importance data:\n")
print(importance_df)
