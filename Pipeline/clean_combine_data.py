import pandas as pd
import numpy as np
import re

# Suppress FutureWarning
pd.set_option('future.no_silent_downcasting', True)

def convert_height_to_inches(val):
    if isinstance(val, str):
        match = re.match(r"(\d+)'[\s]*(\d+\.?\d*)", val)
        if match:
            return round(int(match.group(1)) * 12 + float(match.group(2)), 2)
    return np.nan

def clean_anthro(filepath):
    all_data = []
    xls = pd.ExcelFile(filepath)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df['Year'] = sheet
        df.columns = df.columns.str.replace('\xa0', ' ').str.strip().str.title()
        df.replace("-", np.nan, inplace=True)

        # Convert key measurements to inches
        for col in ["Height W/O Shoes", "Height W/ Shoes", "Standing Reach", "Wingspan"]:
            if col in df.columns:
                df[col] = df[col].apply(convert_height_to_inches)

        df["Body Fat %"] = pd.to_numeric(df.get("Body Fat %", np.nan), errors='coerce')
        df["Weight (Lbs)"] = pd.to_numeric(df.get("Weight (Lbs)", np.nan), errors='coerce')
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

def clean_strength(filepath):
    all_data = []
    xls = pd.ExcelFile(filepath)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df['Year'] = sheet
        df.columns = df.columns.str.strip().str.title()
        df.replace("-", np.nan, inplace=True)
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

def clean_shooting(filepath):
    all_data = []
    xls = pd.ExcelFile(filepath)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df['Year'] = sheet
        df.columns = df.columns.str.strip().str.title()
        df.replace("-", np.nan, inplace=True)
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

if __name__ == "__main__":
    print("📥 Cleaning combine datasets...")

    anthro = clean_anthro("NBA_Combine_Anthrometrics_(2000-2025).xlsx")
    strength = clean_strength("NBA_Combine_Strength_Agility_(2000-2025).xlsx")
    shooting = clean_shooting("NBA_Combine_Shooting_(2021-2025).xlsx")

    # Ensure column names for merging
    for df in [anthro, strength, shooting]:
        df.columns = [col.strip().title() for col in df.columns]

    # Confirm "Player" and "Year" exist
    for df_name, df in zip(["Anthro", "Strength", "Shooting"], [anthro, strength, shooting]):
        if "Player" not in df.columns or "Year" not in df.columns:
            raise ValueError(f"❌ {df_name} DataFrame is missing 'Player' or 'Year' columns")

    # Merge all combine data
    combine_cleaned = anthro.merge(strength, on=["Player", "Year"], how="outer") \
                            .merge(shooting, on=["Player", "Year"], how="outer")

    # Output cleaned file
    combine_cleaned.to_csv("cleaned_combine_data.csv", index=False)
    print("✅ Combine data cleaned and saved to cleaned_combine_data.csv")