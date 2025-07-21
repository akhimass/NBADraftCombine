import pandas as pd

def load_clean_draft_history(path):
    # Read all sheets, taking row 1 as the header
    sheets = pd.read_excel(path, sheet_name=None, header=0)
    parts = []
    for name, df in sheets.items():
        # Only keep the columns we care about
        needed = ['Player', 'Team', 'Year', 'Round Number', 'Round Pick']
        missing = [c for c in needed if c not in df.columns]
        if missing:
            print(f"⚠️ Skipping '{name}': missing {missing}")
            continue

        sub = df[needed].dropna(subset=['Player'])
        print(f"✅ {name}: {len(sub)} players")
        parts.append(sub)

    if not parts:
        raise RuntimeError("No valid draft sheets found!")

    draft = pd.concat(parts, ignore_index=True)
    draft.to_csv("cleaned_draft_history.csv", index=False)
    print(f"\n🚀 Exported cleaned_draft_history.csv ({len(draft)} rows)")
    print(draft.head())
    return draft

if __name__ == "__main__":
    load_clean_draft_history("NBA_Draft_History_(2000-2025).xlsx")