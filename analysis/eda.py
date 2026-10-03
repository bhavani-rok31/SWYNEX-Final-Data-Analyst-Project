"""Task 2 - Exploratory Data Analysis on the cleaned employee dataset from Task 1.
Run:  python eda.py   (reads data/cleaned/cleaned_data.csv, writes images/charts/ and analysis/summary_stats.csv)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "images" / "charts"
CH.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({"figure.dpi": 130, "savefig.bbox": "tight"})

df = pd.read_csv(ROOT / "data" / "cleaned" / "cleaned_data.csv", parse_dates=["Join_Date"])
df["Active"] = df["Active"].map({True: True, False: False, "True": True, "False": False})

# ---------- 1. Overview ----------
print("Shape:", df.shape)
print("\nMissing values:\n", df.isna().sum())
print("Rows with at least one missing value:", df.isna().any(axis=1).sum(), "of", len(df))
print("Fully complete rows:", len(df.dropna()))
summary = df[["Age", "Salary", "Rating"]].describe().T
summary["skew"] = df[["Age", "Salary", "Rating"]].skew()
summary["missing_%"] = (df[["Age", "Salary", "Rating"]].isna().mean() * 100).round(1)
summary.round(2).to_csv(ROOT / "analysis" / "summary_stats.csv")
print("\n", summary.round(2))

# ---------- 2. Outliers (IQR) ----------
for c in ["Age", "Salary", "Rating"]:
    s = df[c].dropna()
    q1, q3 = s.quantile([.25, .75]); iqr = q3 - q1
    n = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
    print(f"IQR outliers in {c}: {n}")

# ---------- 3. Group statistics ----------
by_dept = df.groupby("Department").agg(n=("EmployeeID", "count"), avg_salary=("Salary", "mean"),
                                       avg_rating=("Rating", "mean"),
                                       inactive_rate=("Active", lambda s: (s == False).sum() / s.notna().sum()))
by_city = df.groupby("City").agg(n=("EmployeeID", "count"), avg_salary=("Salary", "mean"), avg_rating=("Rating", "mean"))
by_gender = df.groupby("Gender").agg(n=("EmployeeID", "count"), avg_salary=("Salary", "mean"), avg_rating=("Rating", "mean"))
df["Join_Year"] = df["Join_Date"].dt.year
by_cohort = df.groupby("Join_Year").agg(n=("EmployeeID", "count"), avg_salary=("Salary", "mean"), avg_rating=("Rating", "mean"))
print("\n", by_dept.round(2), "\n", by_city.round(2), "\n", by_gender.round(2), "\n", by_cohort.round(2))

# ---------- 4. Hypothesis tests ----------
m, f = (df[df.Gender == g].Salary.dropna() for g in ["Male", "Female"])
print("\nSalary Male vs Female: means", round(m.mean()), round(f.mean()),
      "| Welch t-test p =", round(stats.ttest_ind(m, f, equal_var=False).pvalue, 3))
d = df.dropna(subset=["Salary", "Rating"])
rho, p = stats.spearmanr(d.Salary, d.Rating)
print(f"Salary vs Rating Spearman rho={rho:.2f}, p={p:.2f} (n={len(d)})")

# ---------- 5. Charts ----------
# 5.1 Missing values
miss = (df.isna().mean() * 100).sort_values(ascending=False)
miss = miss[miss > 0]
fig, ax = plt.subplots(figsize=(7, 4))
sns.barplot(x=miss.values, y=miss.index, ax=ax, color="#c44e52")
for i, v in enumerate(miss.values): ax.text(v + .5, i, f"{v:.0f}%", va="center")
ax.set_xlabel("% missing"); ax.set_title("Missing values by column (60 rows)")
fig.savefig(CH / "01_missing_values.png"); plt.close(fig)

# 5.2 Distributions
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, c in zip(axes, ["Age", "Salary", "Rating"]):
    sns.histplot(df[c].dropna(), kde=True, ax=ax, bins=10)
    ax.axvline(df[c].mean(), color="red", ls="--", label="mean"); ax.axvline(df[c].median(), color="green", ls=":", label="median")
    ax.set_title(f"Distribution of {c}"); ax.legend()
fig.savefig(CH / "02_distributions.png"); plt.close(fig)

# 5.3 Salary by gender
fig, ax = plt.subplots(figsize=(6, 4.5))
sns.boxplot(data=df, x="Gender", y="Salary", ax=ax, showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black"})
sns.stripplot(data=df, x="Gender", y="Salary", ax=ax, color="black", alpha=.4)
ax.set_title("Salary by gender (diamond = mean)")
fig.savefig(CH / "03_salary_by_gender.png"); plt.close(fig)

# 5.4 Dept salary & rating
order = by_dept.sort_values("avg_salary", ascending=False).index
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
sns.barplot(x=by_dept.loc[order].avg_salary, y=order, ax=axes[0], color="#4c72b0")
for i, (v, n) in enumerate(zip(by_dept.loc[order].avg_salary, by_dept.loc[order].n)): axes[0].text(v + 500, i, f"{v/1000:.0f}k (n={n})", va="center")
axes[0].set_title("Average salary by department"); axes[0].set_xlabel("Avg salary")
o2 = by_dept.sort_values("avg_rating", ascending=False).index
sns.barplot(x=by_dept.loc[o2].avg_rating, y=o2, ax=axes[1], color="#55a868")
for i, v in enumerate(by_dept.loc[o2].avg_rating): axes[1].text(v + .03, i, f"{v:.1f}", va="center")
axes[1].set_title("Average rating by department"); axes[1].set_xlim(0, 5.5)
fig.savefig(CH / "04_department_salary_rating.png"); plt.close(fig)

# 5.5 City salary
c = by_city.sort_values("avg_salary")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(c.index, c.avg_salary, color="#8172b2")
for i, (v, n) in enumerate(zip(c.avg_salary, c.n)): ax.text(v + 500, i, f"{v/1000:.0f}k (n={n})", va="center")
ax.set_title("Average salary by city"); ax.set_xlabel("Avg salary")
fig.savefig(CH / "05_city_salary.png"); plt.close(fig)

# 5.6 Join cohort trend
fig, ax1 = plt.subplots(figsize=(7, 4.5))
ax1.plot(by_cohort.index, by_cohort.avg_salary, "o-", color="#4c72b0", label="Avg salary")
ax1.set_ylabel("Avg salary", color="#4c72b0"); ax1.set_xticks(by_cohort.index); ax1.set_xlabel("Join year")
ax2 = ax1.twinx(); ax2.plot(by_cohort.index, by_cohort.avg_rating, "s--", color="#c44e52"); ax2.set_ylabel("Avg rating", color="#c44e52"); ax2.set_ylim(1, 5)
ax2.grid(False); ax1.set_title("Newer hires: higher pay, lower ratings")
fig.savefig(CH / "06_join_cohort_trend.png"); plt.close(fig)

# 5.7 Salary vs rating
fig, ax = plt.subplots(figsize=(7, 5))
sns.scatterplot(data=d, x="Salary", y="Rating", hue="Active", style="Active", s=90, ax=ax)
sns.regplot(data=d, x="Salary", y="Rating", scatter=False, color="gray", ax=ax)
ax.set_title(f"Salary vs performance rating (Spearman rho = {rho:.2f}, p = {p:.2f})")
fig.savefig(CH / "07_salary_vs_rating.png"); plt.close(fig)

# 5.8 Inactive rate by department
r = by_dept.sort_values("inactive_rate", ascending=False)
fig, ax = plt.subplots(figsize=(7, 4.5))
sns.barplot(x=r.inactive_rate * 100, y=r.index, ax=ax, color="#dd8452")
for i, v in enumerate(r.inactive_rate * 100): ax.text(v + 1, i, f"{v:.0f}%", va="center")
ax.set_xlabel("% employees inactive"); ax.set_title("Inactive rate by department (where Active is known)")
fig.savefig(CH / "08_inactive_by_department.png"); plt.close(fig)

# 5.9 Correlation heatmap
fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(df[["Age", "Salary", "Rating"]].corr(), annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
ax.set_title("Correlation (pairwise complete)")
fig.savefig(CH / "09_correlation.png"); plt.close(fig)

# 5.10 Join date batches
fig, ax = plt.subplots(figsize=(7, 4))
jd = df["Join_Date"].dt.date.value_counts().sort_index()
sns.barplot(x=[str(x) for x in jd.index], y=jd.values, ax=ax, color="#64b5cd")
ax.set_title("Employees per Join_Date (only 4 distinct dates)"); ax.set_ylabel("Employees")
fig.savefig(CH / "10_join_date_batches.png"); plt.close(fig)
print("\nCharts saved to", CH)
