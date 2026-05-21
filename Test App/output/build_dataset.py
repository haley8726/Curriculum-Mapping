import pandas as pd

print("SCRIPT IS RUNNING")
# -----------------------------------
# LOAD FILES
# -----------------------------------
courses = pd.read_csv("course_datapoints.tsv", sep="\t")
terms = pd.read_csv("term_datapoints.tsv", sep="\t")

courses.columns = courses.columns.str.strip()
terms.columns = terms.columns.str.strip()



# -----------------------------------
# CLEAN COURSE DATA
# -----------------------------------

# Keep only real graded courses at CSU
courses = courses[
    (courses["record_source"] == "completed_csu") &
    (courses["counts_toward_gpa"] == True) &
    (courses["course_grade"].notna())
]

# Remove non-graded lab shells (NGC)
courses = courses[courses["course_grade"] != "NGC"]  # labs/recitations 【1-f88b03】  

# Create course key (no section splitting)
courses["course_key"] = courses["course_subject"] + "-" + courses["course_number"].astype(str)

# -----------------------------------
# CREATE TERM ORDER
# -----------------------------------

terms["term_order"] = terms["term_year"] * 10 + terms["term_season_order"]
print("TERM COLUMNS:", terms.columns.tolist())
# -----------------------------------
# BUILD CUMULATIVE CSU CREDITS
# -----------------------------------

terms = terms.sort_values(["student_id_hash", "term_order"])

terms["csu_credits_at_time"] = terms.groupby("student_id_hash")["hours_earned"].cumsum()

# -----------------------------------
# HANDLE TRANSFER CREDITS
# -----------------------------------

# Get transfer credits from student file (optional)
students = pd.read_csv("student_datapoints.tsv", sep="\t")
students.columns = students.columns.str.strip()

transfer_lookup = students.set_index("student_id_hash")["transfer_credit_hours_earned"].fillna(0)

terms["transfer_credits"] = terms["student_id_hash"].map(transfer_lookup).fillna(0)

# Add transfer credits ONLY to first term
terms["is_first_term"] = terms.groupby("student_id_hash")["term_order"].transform("min") == terms["term_order"]

terms["all_credits_term"] = terms["hours_earned"]

terms.loc[terms["is_first_term"], "all_credits_term"] += terms["transfer_credits"]

terms["all_credits_at_time"] = terms.groupby("student_id_hash")["all_credits_term"].cumsum()

# -----------------------------------
# MERGE COURSES + TERMS
# -----------------------------------

df = courses.merge(
    terms[[
        "student_id_hash",
        "term",
        "term_order",
        "csu_credits_at_time",
        "all_credits_at_time",
        "class_level",
        "major"
    ]],
    on=["student_id_hash", "term"],
    how="left"
)

# -----------------------------------
# CLEAN COLUMN NAMES
# -----------------------------------

df = df.rename(columns={
    "class_level": "term_class_level",
    "major": "major_at_time"
})

# -----------------------------------
# ADD ATTEMPT NUMBER (REPEATS)
# -----------------------------------

df = df.sort_values(["student_id_hash", "course_key", "term_order"])

df["attempt_number"] = df.groupby(
    ["student_id_hash", "course_key"]
).cumcount() + 1

df["is_repeat"] = df["attempt_number"] > 1

# -----------------------------------
# KEEP ONLY IMPORTANT FIELDS
# -----------------------------------

final_df = df[[
    "student_id_hash",
    "term",
    "term_year",   # ✅ FIXED HERE
    "term_order",
    "course_key",
    "course_grade",
    "grade_points_4_scale",
    "attempt_number",
    "is_repeat",
    "term_class_level",
    "major_at_time",
    "csu_credits_at_time",
    "all_credits_at_time"
]]

# Rename grade points for clarity
final_df = final_df.rename(columns={
    "grade_points_4_scale": "grade_points"
})

# -----------------------------------
# SAVE OUTPUT
# -----------------------------------
final_df["term_season"] = final_df["term"].str.extract(r'(Spring|Summer|Fall)')
final_df.to_csv("student_course_trajectory.csv", index=False)

print("✅ student_course_trajectory.csv created!")
