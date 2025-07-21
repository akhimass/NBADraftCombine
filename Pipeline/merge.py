import pandas as pd

def extract_year(sheetname):
    return str(sheetname)[:4]

def clean_name(s):
    if pd.isnull(s):
        return ""
    s = str(s).lower().replace('.', '').replace(',', '').replace('-', ' ')
    s = s.replace('jr', '').replace('sr', '').replace('iii', '').replace('ii', '')
    s = s.replace("'", "").replace('"', '').replace('  ', ' ').strip()
    return s

def stack_combine(file, player_col):
    dfs = []
    xl = pd.ExcelFile(file)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df['Year_Combine'] = extract_year(sheet)
        if player_col in df.columns:
            df['Player'] = df[player_col]
            dfs.append(df)
        else:
            print(f"➡️ Skipped {sheet}: '{player_col}' column not found")
    if not dfs:
        raise Exception(f"No valid sheets with '{player_col}' found in {file}")
    return pd.concat(dfs, ignore_index=True)

def stack_stats(file):
    dfs = []
    xl = pd.ExcelFile(file)
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df['Year'] = extract_year(sheet)
        player_col = None
        if 'Player' in df.columns:
            player_col = 'Player'
        elif 'PLAYER' in df.columns:
            player_col = 'PLAYER'
        if player_col:
            df['Player'] = df[player_col]
            dfs.append(df)
        else:
            print(f"➡️ Skipped {sheet}: No Player column")
    if not dfs:
        raise Exception(f"No valid sheets with Player found in {file}")
    return pd.concat(dfs, ignore_index=True)

# Fuzzy matcher for columns (handles invisible spaces, case, NBSP, etc)
def match_columns(desired_cols, actual_cols):
    def normalize(x): return x.lower().replace(' ', '').replace('\xa0', '')
    mapping = {}
    for col in desired_cols:
        col_norm = normalize(col)
        for ac in actual_cols:
            if normalize(ac) == col_norm:
                mapping[col] = ac
                break
    return mapping

# --- Your exact combine columns
combine_cols = [
    'BODY FAT %', 'HAND LENGTH (inches)', 'HAND WIDTH (inches)', 'HEIGHT W/O SHOES',
    'HEIGHT W/ SHOES', 'STANDING REACH', 'WEIGHT (LBS)', 'WINGSPAN',
    'Lane Agility Time (seconds)', 'Shuttle Run (seconds)', 'Three Quarter Sprint (seconds)',
    'Standing Vertical Leap (inches)', 'Max Vertical Leap (inches)', 'Max Bench Press (repetitions)'
]

# 1. Load combine data
anthro = stack_combine("NBA_Combine_Anthrometrics_(2000-2025).xlsx", player_col="PLAYER")
strength = stack_combine("NBA_Combine_Strength_Agility_(2000-2025).xlsx", player_col="PLAYER")
anthro['Player_clean'] = anthro['Player'].apply(clean_name)
strength['Player_clean'] = strength['Player'].apply(clean_name)
combine = anthro.merge(strength, on='Player_clean', how='outer', suffixes=('_anthro', '_strength'))
combine = combine.drop_duplicates(subset=['Player_clean'])

# Fuzzy-match combine columns for dropna filtering
combine_actual_cols = list(combine.columns)
colmap = match_columns(combine_cols, combine_actual_cols)
filtered_cols = [colmap[col] for col in combine_cols if col in colmap]

# Drop players with ALL combine metrics missing (i.e., didn't attend the combine)
combine = combine.dropna(subset=filtered_cols, how='all')

# 2. Load NBA stats & usage per player-year
trad = stack_stats("NBA_Traditional_Stats_(2010-25).xlsx")
usage = stack_stats("NBA_Usage_Stats (2010-25).xlsx")
for df in [trad, usage]:
    df['Player_clean'] = df['Player'].apply(clean_name)
    df['Year_clean'] = df['Year'].astype(str)

# 3. Merge combine to NBA stats (Player_clean only)
player_years = trad.merge(combine, on='Player_clean', how='inner', suffixes=('', '_combine'))

# 4. Merge usage (Player_clean + Year_clean)
player_years = player_years.merge(usage, on=['Player_clean', 'Year_clean'], how='left', suffixes=('', '_usage'))

# 5. Merge injuries (Player_clean + Year_clean)
inj = pd.read_excel("injury_spans_2000_2025.xlsx")
inj['Player_clean'] = inj['Player'].apply(clean_name)
inj['Year_clean'] = inj['Year'].astype(str).str[:4]
player_years = player_years.merge(inj, on=['Player_clean', 'Year_clean'], how='left', suffixes=('', '_injury'))

# 6. Drop duplicates
player_years = player_years.drop_duplicates(subset=['Player_clean', 'Year_clean'])

# 7. Output only combine participants and all their NBA career seasons
player_years.to_csv("combine_participants_nba_careers.csv", index=False)
print(f"✅ All combine participants with all their NBA stats/usage/injury in combine_participants_nba_careers.csv")
print(f"Rows: {len(player_years)} | Columns: {len(player_years.columns)}")