-- ============================================================
-- clean_data.sql
-- Written for PostgreSQL (minor syntax tweaks needed for MySQL/SQL Server)
--
-- Purpose: load the raw messy employee data, IDENTIFY the same four
-- categories of issues found in Excel/Python, then produce a cleaned table.
-- ============================================================

-- ------------------------------------------------------------
-- STEP 1: Create a raw staging table (all columns as TEXT,
-- because the raw data has mixed/incorrect types per column)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS employees_raw;
CREATE TABLE employees_raw (
    EmployeeID  TEXT,
    Full_Name   TEXT,
    Age         TEXT,
    Gender      TEXT,
    Department  TEXT,
    City        TEXT,
    Join_Date   TEXT,
    Salary      TEXT,
    Email       TEXT,
    Rating      TEXT,
    Active      TEXT
);

-- Load data (psql example):
-- \COPY employees_raw FROM 'raw_data.csv' WITH (FORMAT csv, HEADER true);

-- ------------------------------------------------------------
-- STEP 2: IDENTIFY ISSUES
-- ------------------------------------------------------------

-- 2a. Missing values per column (counts blanks, NULL, 'N/A', 'unknown')
SELECT
    SUM(CASE WHEN Age        IS NULL OR Age        IN ('N/A','unknown','') THEN 1 ELSE 0 END) AS missing_age,
    SUM(CASE WHEN Gender     IS NULL OR Gender      = ''                    THEN 1 ELSE 0 END) AS missing_gender,
    SUM(CASE WHEN Department IS NULL OR Department  = ''                    THEN 1 ELSE 0 END) AS missing_department,
    SUM(CASE WHEN City       IS NULL OR City        = ''                    THEN 1 ELSE 0 END) AS missing_city,
    SUM(CASE WHEN Salary     IS NULL OR Salary      IN ('unknown','')       THEN 1 ELSE 0 END) AS missing_salary,
    SUM(CASE WHEN Email      IS NULL OR Email       = ''                    THEN 1 ELSE 0 END) AS missing_email,
    SUM(CASE WHEN Rating     IS NULL OR Rating      IN ('N/A','')           THEN 1 ELSE 0 END) AS missing_rating
FROM employees_raw;

-- 2b. Duplicate EmployeeIDs (same ID appearing more than once)
SELECT EmployeeID, COUNT(*) AS occurrences
FROM employees_raw
GROUP BY EmployeeID
HAVING COUNT(*) > 1;

-- 2c. Fully duplicated rows (every column identical)
SELECT EmployeeID, Full_Name, Age, Gender, Department, City, Join_Date,
       Salary, Email, Rating, Active, COUNT(*) AS occurrences
FROM employees_raw
GROUP BY EmployeeID, Full_Name, Age, Gender, Department, City, Join_Date,
         Salary, Email, Rating, Active
HAVING COUNT(*) > 1;

-- 2d. Distinct spellings/casings used in categorical columns (inconsistent values)
SELECT DISTINCT Gender     FROM employees_raw ORDER BY 1;
SELECT DISTINCT Department FROM employees_raw ORDER BY 1;
SELECT DISTINCT City       FROM employees_raw ORDER BY 1;
SELECT DISTINCT Active     FROM employees_raw ORDER BY 1;

-- ------------------------------------------------------------
-- STEP 3: CLEAN -> build employees_clean
-- ------------------------------------------------------------
DROP TABLE IF EXISTS employees_clean;

CREATE TABLE employees_clean AS
WITH deduped AS (
    -- keep only the first occurrence of each EmployeeID
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY EmployeeID ORDER BY EmployeeID) AS rn
    FROM employees_raw
)
SELECT
    EmployeeID,
    INITCAP(TRIM(REGEXP_REPLACE(Full_Name, '\s+', ' ', 'g'))) AS full_name,

    -- Age: strip "yrs", cast to number, discard impossible/word values
    CASE
        WHEN Age ~ '^[0-9]+(\.0)?$' AND Age::NUMERIC BETWEEN 0 AND 100 THEN Age::NUMERIC
        WHEN Age ~ '^[0-9]+ yrs$' THEN REPLACE(Age, ' yrs', '')::NUMERIC
        ELSE NULL
    END AS age,

    -- Gender: standardize every spelling to Male / Female
    CASE LOWER(TRIM(Gender))
        WHEN 'male' THEN 'Male' WHEN 'm' THEN 'Male' WHEN 'man' THEN 'Male'
        WHEN 'female' THEN 'Female' WHEN 'f' THEN 'Female' WHEN 'woman' THEN 'Female'
        ELSE NULL
    END AS gender,

    -- Department: standardize
    CASE LOWER(TRIM(Department))
        WHEN 'hr' THEN 'HR' WHEN 'human resources' THEN 'HR'
        WHEN 'sales' THEN 'Sales'
        WHEN 'marketing' THEN 'Marketing'
        WHEN 'operations' THEN 'Operations' WHEN 'ops' THEN 'Operations'
        WHEN 'finance' THEN 'Finance'
        WHEN 'it' THEN 'IT' WHEN 'it dept' THEN 'IT'
        ELSE NULL
    END AS department,

    -- City: trim, standardize casing and merge Bangalore/Bengaluru
    INITCAP(REPLACE(LOWER(TRIM(City)), 'bangalore', 'bengaluru')) AS city,

    -- Join_Date: cast common formats to DATE (extend as needed)
    COALESCE(
        TO_DATE(Join_Date, 'YYYY-MM-DD'),
        TO_DATE(Join_Date, 'DD/MM/YYYY'),
        TO_DATE(Join_Date, 'DD-Mon-YYYY'),
        TO_DATE(Join_Date, 'YYYY/MM/DD'),
        TO_DATE(Join_Date, 'Month DD, YYYY'),
        TO_DATE(Join_Date, 'DD-MM-YYYY')
    ) AS join_date,

    -- Salary: strip currency symbols/commas/spaces, cast to numeric
    CASE
        WHEN Salary IS NULL OR Salary IN ('unknown','') THEN NULL
        ELSE REPLACE(REPLACE(REPLACE(TRIM(Salary), '$',''), '₹',''), ',','')::NUMERIC
    END AS salary,

    LOWER(TRIM(Email)) AS email,

    -- Rating: convert word, discard out-of-range (scale is 1-5)
    CASE
        WHEN LOWER(TRIM(Rating)) = 'five' THEN 5
        WHEN Rating ~ '^[0-9]+(\.[0-9])?$' AND Rating::NUMERIC BETWEEN 1 AND 5 THEN Rating::NUMERIC
        ELSE NULL
    END AS rating,

    -- Active: map every representation to boolean
    CASE LOWER(TRIM(Active))
        WHEN 'yes' THEN TRUE WHEN 'y' THEN TRUE WHEN '1' THEN TRUE WHEN 'true' THEN TRUE
        WHEN 'no' THEN FALSE WHEN 'n' THEN FALSE WHEN '0' THEN FALSE WHEN 'false' THEN FALSE
        ELSE NULL
    END AS active
FROM deduped
WHERE rn = 1;

-- ------------------------------------------------------------
-- STEP 4: VALIDATE the cleaned table
-- ------------------------------------------------------------
SELECT COUNT(*) AS total_rows FROM employees_clean;
SELECT COUNT(*) AS distinct_ids FROM (SELECT DISTINCT EmployeeID FROM employees_clean) t;
SELECT DISTINCT gender FROM employees_clean;
SELECT DISTINCT department FROM employees_clean;
