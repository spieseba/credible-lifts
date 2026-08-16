"""Build dataset from competitions.csv and athletes.csv

Run from repo root: uv run python -m credible_lifts.processing.build_dataset
"""

from pathlib import Path

import numpy as np
import pandas as pd

PARSED = Path("data/parsed")
PROCESSED = Path("data/processed")
PERMANENTS = {4588, 4772, 20956, 24170, 35335, 46935, 48461, 55779} # non-fetchable aid pages
DOUBLE_LISTED_ROWS = { # bogus half of double-listed results (category contradicts bodyweight), 2026-08-16
    (4430, 3974, "M 75 kg"), (54071, 3384, "M 56 kg"), (55777, 3507, "W +81 kg")}
CHECKED_GENDERS = { # Manually verified against cached pages / results, 2026-08-16
    52020: "W",   # Malay Tauber, female youth lifter
    52074: "W"}   # Lotta Frank, female youth lifter

# load csv files into dataframes
def load():
    return (pd.read_csv(PARSED / "competitions.csv"), pd.read_csv(PARSED / "athletes.csv"))

# remove competition results without a valid total
def drop_invalid_totals(df):
    valid_totals = df["total"] > 0 # earlier eras have nans while newer eras were imputed with 0s
    print(f"Drop {(~valid_totals).sum()} rows without valid totals.")
    return df[valid_totals] 

# remove results of athletes with less than 3 entries
def drop_underrepresented(df):
    athlete_id_counts = df["athlete_id"].value_counts()
    athlete_ids_to_keep = athlete_id_counts[athlete_id_counts >= 3]
    keep = df["athlete_id"].isin(athlete_ids_to_keep.index)
    print(f"Drop {(~keep).sum()} rows of {len(athlete_id_counts) - len(athlete_ids_to_keep)} athletes with less than 3 valid totals.")
    return df[keep]

# remove results of athletes with dead bio pages
def drop_dead_pages(df_comp, df_athl):
    no_bio = ~df_comp["athlete_id"].isin(df_athl["athlete_id"])
    missing_ids = set(df_comp.loc[no_bio, "athlete_id"])
    assert missing_ids == PERMANENTS
    print(f"Drop {no_bio.sum()} rows of {len(missing_ids)} athletes with dead bio pages.")
    return df_comp[~no_bio]

# remove results with implausable bodyweights
def drop_implausible_bodyweights(df):
    invalid_bw = ~(df["bodyweight"] >= 20) # catches 0, tiny garbage, and nans
    print(f"Drop {invalid_bw.sum()} rows with implausible bodyweight.")
    return df[~invalid_bw]

# drop the bogus half of double-listed results
def drop_double_listed(df):
    invalid = df.set_index(["athlete_id", "competition_id", "category"]).index.isin(DOUBLE_LISTED_ROWS)
    assert invalid.sum() == len(DOUBLE_LISTED_ROWS)
    print(f"Drop {invalid.sum()} double-listed rows whose category contradicts bodyweight.")
    return df[~invalid]

# drop duplicates: can only have one performance per athlete per day
def drop_duplicates(df):
    is_dup = df.duplicated(subset=["athlete_id", "date", "total"])
    print(f"Drop {is_dup.sum()} duplicated rows.")
    return df[~is_dup]

def opposite_gender(gender):
    if gender == 'M':
        return 'W'
    elif gender == 'W':
        return 'M'
    else:
        raise ValueError(f"Specified gender = {gender} unknown.")

# Resolve competition gender with gender from athlete bio 
def resolve_gender(df):
    df = df.copy()
    # Check if there are mismatches
    df_gender = df[~df["gender"].isna()][["athlete_id","gender", "gender_bio"]]
    df_gender_mismatch = df_gender["gender"] != df_gender["gender_bio"]
    aids_gender_mismatch = df_gender[df_gender_mismatch]["athlete_id"].unique()

    aids_to_be_checked = []
    aids_overridden = [] # bio contradicted by unanimous competition results
    decisions = {}
    for aid, df_aid in df[df["athlete_id"].isin(aids_gender_mismatch)].groupby("athlete_id"):
        # resolve gender with bio gender...
        gender = df_aid["gender_bio"].unique()[0]
        # unless all competition rows of aid disagree 
        gender_counts = df_aid["gender"].value_counts()
        if gender not in gender_counts:
            opp_gender = opposite_gender(gender)
            # exception: only one competition result with gender available -> Check by hand
            if gender_counts[opp_gender] < 2:
                if aid in CHECKED_GENDERS:
                    gender = CHECKED_GENDERS[aid]
                else:
                    aids_to_be_checked.append(aid)
            else:
                gender = opp_gender
                aids_overridden.append(aid)
        decisions[aid] = gender
    assert not aids_to_be_checked, f"Check: {aids_to_be_checked}"
    print(f"Resolve gender for {len(aids_gender_mismatch)} mismatch athletes: "
          f"{len(aids_overridden)} bios overridden by unanimous results, {len(CHECKED_GENDERS)} verified by hand.")
    # Store decisions in dataset and fill "gender" column with gender_bio values
    n_missing_gender = df["gender"].isna().sum()
    df["gender"] = df["athlete_id"].map(decisions).fillna(df["gender_bio"])
    print(f"Fill {n_missing_gender} rows without gender from resolved athlete gender.")
    assert df["gender"].notna().all()
    assert (df.groupby("athlete_id")["gender"].nunique() == 1).all()
    # drop gender_bio
    df = df.drop(columns="gender_bio")
    return df

def drop_missing_birthdates(df):
    missing_birthdates = df["birthdate"] == "0000-00-00"
    print(f"Drop {missing_birthdates.sum()} rows of {df.loc[missing_birthdates, "athlete_id"].nunique()} athletes with missing birthdates") 
    return df[~missing_birthdates]

def impute_birthdates(df):
    df = df.copy()
    # Year-only birthdates appear as month "00" or as "01-01" placeholders (932 Jan-1 vs ~32 expected by chance).
    # Impute both to the year's midpoint 07-01; costs the O(30) genuine Jan-1 birthdays the same <=6-month error
    year_only = (df["birthdate"].str[5:7] == "00") | (df["birthdate"].str[5:] == "01-01")
    df["birthdate_precision"] = np.where(year_only, "year", "full")
    # impute 00 months with 07-01
    df.loc[year_only, "birthdate"] = df.loc[year_only, "birthdate"].str[:4] + "-07-01"
    print(f"Impute {year_only.sum()} rows of {df.loc[year_only, 'athlete_id'].nunique()} athletes "
          f"with year-only birthdates to July 1; {(~year_only).sum()} rows keep exact birthdates.")
    for dcol in ["birthdate", "date"]:
        df[dcol] = pd.to_datetime(df[dcol])
    return df

def compute_age(df):
    df = df.copy()
    df["age"] = (df["date"] - df["birthdate"]).dt.days / 365.25
    return df

def drop_implausible_ages(df):
    # Ages outside (8, 90) are considered namesakes results merged
    # onto a wrong athlete page
    implausible = (df["age"] <= 8) | (df["age"] >= 90)
    print(f"Drop {implausible.sum()} rows of {df.loc[implausible, 'athlete_id'].nunique()} athletes with implausible ages.")
    return df[~implausible]

if __name__ == "__main__":

    df_competitions, df_athletes = load()

    # Competitions cleanup
    print("--- Clean up competition dataset ---")
    df_competitions = drop_invalid_totals(df_competitions)
    df_competitions = drop_underrepresented(df_competitions)
    df_competitions = drop_dead_pages(df_competitions, df_athletes)
    df_competitions = drop_implausible_bodyweights(df_competitions)
    print()

    # Join cleaned up competitions with athletes on athlete_id
    print("Join competition with athlete dataset")
    df = df_competitions.merge(df_athletes, 
                               how="left", on="athlete_id", 
                               suffixes=("", "_bio"), validate="m:1")
    print()

    # Cleanup joined dataset
    print("--- Clean up joined dataset ---")
    df = drop_double_listed(df)
    df = drop_duplicates(df)
    print()

    print("--- Resolve gender ---")
    df = resolve_gender(df)
    print()

    print("--- Compute ages ---")
    df = drop_missing_birthdates(df)
    df = impute_birthdates(df)
    df = compute_age(df)
    df = drop_implausible_ages(df)
    print()

    # re-check >= 3 after all row drops
    print("--- Drop athletes with < 3 results after cleanup ---")
    df = drop_underrepresented(df)
    print()

    # one canonical athlete-level name, from the bio
    print("--- Cleanup output df and write to CSV ---")

    df = df.drop(columns="athlete_name").rename(columns={"athlete_name_bio": "athlete_name"})

    df_output = df[[
        "athlete_id", "athlete_name", "nation", "nation_bio",
        "gender", "birthdate", "birthdate_precision", "age",
        "competition_id", "competition_name", "date", "bodyweight",
        "category", "rank", "club", "sn1", "sn2", "sn3", "best_snatch",
        "cj1", "cj2", "cj3", "best_cj", "total", "sinclair"
        ]]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "dataset.csv"
    df_output.to_csv(out_path, index=False)
    print(f"Kept {len(df_output)} rows from {df_output['athlete_id'].nunique()} athletes -> {out_path}")

