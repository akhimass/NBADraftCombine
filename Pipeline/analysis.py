import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns

# 1) Load & normalize column names
df = pd.read_csv("drafted_combine_participants.csv")
df.columns = [re.sub(r"\s+", " ", c.replace(u"\xa0"," ")).strip() for c in df.columns]

KEY = "Player_clean"

# 2) Combine metrics list
raw_metrics = [
    "WINGSPAN", "BODY FAT %", "HAND LENGTH (inches)", "HAND WIDTH (inches)",
    "HEIGHT W/O SHOES", "HEIGHT W/ SHOES", "STANDING REACH", "WEIGHT (LBS)",
    "Lane Agility Time", "Shuttle Run", "Three Quarter Sprint",
    "Standing Vertical Leap", "Max Vertical Leap", "Max Bench Press"
]
# pick only those that exist
cmb = [m for m in raw_metrics if m in df.columns]
print(f"Detected combine metrics with columns: {cmb}")

# 3) Cast to numeric and count non‐nulls
valid_metrics = []
for m in cmb:
    df[m] = pd.to_numeric(df[m].astype(str).str.replace(r"[^\d\.]", ""), errors="coerce")
    non_null = df[m].notna().sum()
    print(f"  → {m}: {non_null} non-null values")
    if non_null > 10:     # require at least 10 values to include
        valid_metrics.append(m)
print(f"Using metrics for correlation: {valid_metrics}")

# 4) Seasons & career arc
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
seasons = df.groupby(KEY)["Year"].nunique().rename("Seasons_Played")
df = df.merge(seasons, on=KEY)
df["Career_Arc"] = pd.cut(
    df["Seasons_Played"],
    bins=[-1,0,3,7,100],
    labels=["None","Early (1–3 yrs)","Mid (4–7 yrs)","Late (8+ yrs)"]
)

# 5) Performance tier via PPG
df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
df["GP"]  = pd.to_numeric(df["GP"],  errors="coerce")
df["PPG"] = df["PTS"] / df["GP"].replace(0, np.nan)
avg_ppg = df.groupby(KEY)["PPG"].mean().rename("Avg_PPG")
df = df.merge(avg_ppg, on=KEY)
df["Perf_Tier"] = pd.qcut(
    df["Avg_PPG"], 4,
    labels=["Bottom 25%","25–50%","50–75%","Top 25%"],
    duplicates="drop"
)

# 6) Injuries
df["InjuryLengthDays"] = pd.to_numeric(df.get("InjuryLengthDays"), errors="coerce")
inj_count = df.groupby(KEY)["InjuryLengthDays"].count().rename("Injury_Count")
inj_sev   = df.groupby(KEY)["InjuryLengthDays"].mean().rename("Avg_Injury_Days")
df = df.merge(inj_count, on=KEY).merge(inj_sev, on=KEY)

# 7) Correlation & fallback
outcomes = ["Seasons_Played","Avg_PPG","Injury_Count","Avg_Injury_Days"]
corr_cols = [c for c in valid_metrics + outcomes if c in df.columns]
print(f"Final corr columns: {corr_cols}")

corr_df = df[corr_cols].dropna()
if len(corr_df) >= 10:
    plt.figure(figsize=(10,8))
    cm = corr_df.corr()
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="coolwarm", linewidths=.5)
    plt.title("Combine Metrics ↔ Career & Injury Outcomes")
    plt.tight_layout()
    plt.savefig("correlation_combine_outcomes.png", dpi=300)
    plt.close()
    print("✅ correlation_combine_outcomes.png saved")
else:
    print("⚠️ Not enough data for correlation heatmap, falling back to histograms")
    for m in valid_metrics:
        plt.figure()
        df[m].hist(bins=20)
        plt.title(f"Distribution of {m}")
        plt.savefig(f"hist_{m.replace(' ','_')}.png", dpi=200)
        plt.close()

# 8) Archetype Profiles with fallbacks
med_inj = df["Injury_Count"].median()
success = df[
    (df["Career_Arc"]=="Late (8+ yrs)") &
    (df["Perf_Tier"]=="Top 25%") &
    (df["Injury_Count"] <= med_inj)
]
risk = df[
    (df["Career_Arc"]=="Early (1–3 yrs)") |
    (df["Injury_Count"] >= df["Injury_Count"].quantile(0.75))
]
if success.empty or risk.empty:
    print("⚠️ Success or Risk group empty—relaxing thresholds")
    success = df[df["Perf_Tier"]=="Top 25%"]
    risk    = df[df["Perf_Tier"]=="Bottom 25%"]

def summarize(grp, label):
    s = grp[valid_metrics].mean()
    out = pd.DataFrame([s], index=[label])
    out["N_Players"] = grp[KEY].nunique()
    return out

succ_sum = summarize(success, "Success_Profile")
risk_sum = summarize(risk,    "Risk_Profile")
profiles = pd.concat([succ_sum, risk_sum])
profiles.to_csv("profile_combine_summary.csv")
print("✅ profile_combine_summary.csv saved")

# 9) Plot profiles
plt.figure(figsize=(10,6))
profiles[valid_metrics].T.plot(kind="bar", figsize=(10,6))
plt.title("Combine Signatures: Success vs Risk")
plt.tight_layout()
plt.savefig("archetype_signatures.png", dpi=300)
plt.close()
print("✅ archetype_signatures.png saved")

# 10) Export player-level summary
export_cols = [KEY,"Career_Arc","Perf_Tier","Seasons_Played","Avg_PPG","Injury_Count","Avg_Injury_Days"] + valid_metrics
export_cols = [c for c in export_cols if c in df.columns]
player_sum = df[export_cols].drop_duplicates()
player_sum.to_csv("player_level_analysis.csv", index=False)
print("✅ player_level_analysis.csv saved")
