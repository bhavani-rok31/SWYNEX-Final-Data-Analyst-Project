# Excel Cleaning Steps — messy_employee_data.csv

Open `raw_data.csv` in Excel and follow these steps. This is the manual/exploratory
pass — it mirrors the logic in `python/clean_data.py` and `sql/clean_data.sql`.

## 1. Find missing values
- Select the data range → **Home → Conditional Formatting → Highlight Cells Rules → Blanks**
- Also use **Ctrl+F → Find All** to search for `N/A` and `unknown`, since those are
  "hidden" missing values, not true blanks.
- Use `=COUNTBLANK(A2:A70)` per column to get exact counts.

## 2. Find duplicate records
- Select all data → **Data tab → Remove Duplicates** (uncheck "My data has headers"
  only if needed; run it once WITHOUT deleting first — Excel will tell you how many
  duplicate rows it found before removing them).
- For duplicate **EmployeeIDs with different data** (not exact duplicates), use:
  `=COUNTIF($A$2:$A$70, A2) > 1` in a helper column to flag them, then review manually.

## 3. Fix incorrect data types
- **Age**: select column → Data → Text to Columns → Finish (forces Excel to
  re-evaluate numeric text). Manually fix word-values like "thirty" → 30.
- **Join_Date**: select column → Data → Text to Columns → step 3 → choose Date (DMY)
  — but because this column mixes multiple formats, you'll need to fix format
  groups separately, then apply one consistent Date format via
  **Format Cells → Date → YYYY-MM-DD**.
- **Salary**: use Find & Replace to strip `$`, `₹`, and `,` characters, then
  Format Cells → Number.

## 4. Fix inconsistent values
- **Gender**: use Find & Replace (Ctrl+H) to map every variant to one value:
  `MALE`, `M`, `Man` → `Male`; `FEMALE`, `F`, `Woman` → `Female`.
- **Department**: map `hr`/`HR`/`Human Resources` → `HR`; `Ops`/`operations` →
  `Operations`; `IT Dept` → `IT`, etc.
- **City**: use `=TRIM(PROPER(A2))` in a helper column to remove extra spaces and
  standardize casing, then Find & Replace `Bangalore` → `Bengaluru`.
- **Active**: map `Yes`/`Y`/`1`/`TRUE` → `Yes`; `No`/`N`/`0`/`FALSE` → `No`.

## 5. Save your work
Save this pass as `excel/employee_data_excel_cleaned.xlsx` and keep it — even
though the final submitted `cleaned_data.csv` is produced by the Python script,
this file demonstrates you can do the same fixes manually in Excel.
