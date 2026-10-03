"""
clean_data.py
--------------
Cleans messy_employee_data.csv (raw_data.csv) and produces cleaned_data.csv.

Issues fixed:
1. Missing values      -> standardized all blank/"N/A"/"unknown" markers to NaN
2. Duplicate records    -> removed exact duplicate rows and duplicate EmployeeIDs
3. Incorrect data types -> Age, Salary, Rating converted to proper numeric types;
                           Join_Date converted to proper datetime
4. Inconsistent values  -> Gender, Department, City, Active standardized to
                           single consistent category per value
"""

import pandas as pd
from pathlib import Path
import numpy as np
import re

# ---------------------------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------------------------
df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "raw" / "raw_data.csv")
print(f"Raw shape: {df.shape}")

# ---------------------------------------------------------------------------
# 2. STANDARDIZE MISSING VALUE MARKERS
# ---------------------------------------------------------------------------
# The raw file uses several different strings to mean "missing":
# blank, "N/A", "n/a", "unknown", "Unknown" -> convert all to real NaN
MISSING_TOKENS = ["N/A", "n/a", "unknown", "Unknown", "", " "]
df.replace(MISSING_TOKENS, np.nan, inplace=True)

# ---------------------------------------------------------------------------
# 3. FULL NAME - trim extra internal/outer whitespace, Title Case
# ---------------------------------------------------------------------------
df["Full Name"] = (
    df["Full Name"]
    .astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
    .str.title()
)

# ---------------------------------------------------------------------------
# 4. AGE - convert word-numbers, strip "yrs", fix negatives, cast to numeric
# ---------------------------------------------------------------------------
WORD_TO_NUM = {"twenty-five": 25, "thirty": 30, "forty": 40, "fifty": 50}

def clean_age(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip().lower()
    if val in WORD_TO_NUM:
        return WORD_TO_NUM[val]
    val = val.replace("yrs", "").strip()
    try:
        num = float(val)
    except ValueError:
        return np.nan
    if num < 0 or num > 100:          # impossible age -> treat as error
        return np.nan
    return num

df["Age"] = df["Age"].apply(clean_age)

# ---------------------------------------------------------------------------
# 5. GENDER - map every spelling variant to Male / Female
# ---------------------------------------------------------------------------
GENDER_MAP = {
    "male": "Male", "m": "Male", "man": "Male",
    "female": "Female", "f": "Female", "woman": "Female",
}
df["Gender"] = df["Gender"].astype(str).str.strip().str.lower().map(GENDER_MAP)

# ---------------------------------------------------------------------------
# 6. DEPARTMENT - map casing / naming variants to one canonical label
# ---------------------------------------------------------------------------
DEPT_MAP = {
    "hr": "HR", "human resources": "HR",
    "sales": "Sales",
    "marketing": "Marketing",
    "operations": "Operations", "ops": "Operations",
    "finance": "Finance",
    "it": "IT", "it dept": "IT",
}
df["Department"] = df["Department"].astype(str).str.strip().str.lower().map(DEPT_MAP)

# ---------------------------------------------------------------------------
# 7. CITY - trim whitespace, Title Case, merge known duplicate names
# ---------------------------------------------------------------------------
CITY_MAP = {"bangalore": "Bengaluru"}  # canonical modern name

df["City"] = (
    df["City"]
    .astype(str)
    .str.strip()
    .str.lower()
    .replace(CITY_MAP)
    .str.title()
)
df["City"] = df["City"].replace("Nan", np.nan)

# ---------------------------------------------------------------------------
# 8. JOIN_DATE - parse many formats into one standard YYYY-MM-DD
# ---------------------------------------------------------------------------
DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%Y/%m/%d",
    "%B %d, %Y", "%d-%m-%Y", "%m-%d-%Y",
]

def clean_date(val):
    if pd.isna(val):
        return pd.NaT
    val = str(val).strip()
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(val, format=fmt)
        except ValueError:
            continue
    return pd.NaT  # couldn't parse -> missing

df["Join_Date"] = df["Join_Date"].apply(clean_date)

# ---------------------------------------------------------------------------
# 9. SALARY - strip currency symbols, commas, spaces; cast to numeric
# ---------------------------------------------------------------------------
def clean_salary(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    val = re.sub(r"[₹$,]", "", val)
    val = val.strip()
    try:
        return float(val)
    except ValueError:
        return np.nan

df["Salary"] = df["Salary"].apply(clean_salary)

# ---------------------------------------------------------------------------
# 10. EMAIL - lowercase for consistency
# ---------------------------------------------------------------------------
df["Email"] = df["Email"].astype(str).str.strip().str.lower().replace("nan", np.nan)

# ---------------------------------------------------------------------------
# 11. RATING - convert word numbers, clamp out-of-range (scale is 1-5)
# ---------------------------------------------------------------------------
RATING_WORD_MAP = {"five": 5}

def clean_rating(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip().lower()
    if val in RATING_WORD_MAP:
        return RATING_WORD_MAP[val]
    try:
        num = float(val)
    except ValueError:
        return np.nan
    if num < 1 or num > 5:   # impossible on a 1-5 scale -> treat as error
        return np.nan
    return num

df["Rating"] = df["Rating"].apply(clean_rating)

# ---------------------------------------------------------------------------
# 12. ACTIVE - map every representation to a real boolean
# ---------------------------------------------------------------------------
ACTIVE_MAP = {
    "yes": True, "y": True, "1": True, "true": True,
    "no": False, "n": False, "0": False, "false": False,
}
df["Active"] = df["Active"].astype(str).str.strip().str.lower().map(ACTIVE_MAP)

# ---------------------------------------------------------------------------
# 13. DUPLICATES
# ---------------------------------------------------------------------------
before = len(df)
df.drop_duplicates(inplace=True)                       # exact duplicate rows
df.drop_duplicates(subset="EmployeeID", keep="first", inplace=True)  # same ID, conflicting data
print(f"Removed {before - len(df)} duplicate rows")

# ---------------------------------------------------------------------------
# 14. SAVE
# ---------------------------------------------------------------------------
df.sort_values("EmployeeID", inplace=True)
df.to_csv(Path(__file__).resolve().parent.parent / "data" / "cleaned" / "cleaned_data.csv", index=False)
print(f"Cleaned shape: {df.shape}")
print("\nMissing values per column after cleaning:")
print(df.isna().sum())
