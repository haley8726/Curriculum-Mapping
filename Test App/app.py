import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------
# TITLE + DESCRIPTION
# ------------------------------
st.title("Course Timing & Grade Explorer")

st.markdown("""
This dashboard explores **when students take courses and how they perform**, 
broken down by major. Use the filters below to explore patterns across programs.
""")

# ------------------------------
# LOAD DATA
# ------------------------------
df = pd.read_csv("student_course_trajectory.csv", low_memory=False)

# Ensure clean columns
df.columns = df.columns.str.strip()

# ------------------------------
# DERIVED FIELDS
# ------------------------------
major_colors = {
    "Biomedical Sciences": "#8dd3c7",
    "Health and Exercise Science": "#ffffb3",
    "Neuroscience": "#bebada",
    "Biology": "#fb8072",
    "Psychology": "#80b1d3",
    "Other": "#fdb462"
}
df["term_credit_load"] = df["csu_credits_at_time"] - df.groupby("student_id_hash")["csu_credits_at_time"].shift(1).fillna(0)
# Extract term season
df["term_season"] = df["term"].str.extract(r'(Spring|Summer|Fall)')

# Create orderable term
season_order = {"Spring": 1, "Summer": 2, "Fall": 3}
df["term_order"] = df["term_year"] * 10 + df["term_season"].map(season_order)

# Label attempt type
df["attempt_type"] = df["attempt_number"].apply(
    lambda x: "First Attempt" if x == 1 else "Repeat"
)

# ------------------------------
# FILTERS
# ------------------------------
st.markdown("### Filters")

# ✅ Credit mode
credit_mode = st.selectbox(
    "Credit Type",
    ["CSU Credits Only", "All Credits (Including Transfer)"]
)

if credit_mode == "CSU Credits Only":
    df["credits_at_time"] = df["csu_credits_at_time"]
else:
    df["credits_at_time"] = df["all_credits_at_time"]

# ✅ Attempt filter
attempt_filter = st.selectbox(
    "Attempt Type",
    ["All Attempts", "First Attempt Only", "Repeats Only"]
)

if attempt_filter == "First Attempt Only":
    df = df[df["attempt_number"] == 1]
elif attempt_filter == "Repeats Only":
    df = df[df["attempt_number"] > 1]

# ------------------------------
# TIME FILTER
# ------------------------------
df["term_label"] = df["term_season"] + " " + df["term_year"].astype(str)

term_options = (
    df[["term_label", "term_order"]]
    .drop_duplicates()
    .sort_values("term_order")
)

term_list = term_options["term_label"].tolist()

start_term = st.selectbox("Start Term", term_list, index=0)
end_term = st.selectbox("End Term", term_list, index=len(term_list)-1)

start_value = term_options[term_options["term_label"] == start_term]["term_order"].values[0]
end_value = term_options[term_options["term_label"] == end_term]["term_order"].values[0]

df = df[
    (df["term_order"] >= start_value) &
    (df["term_order"] <= end_value)
]

# ------------------------------
# CLEAN GRADE ORDER
# ------------------------------
grade_order = [
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D", "F", "W"
]

df["course_grade"] = pd.Categorical(
    df["course_grade"],
    categories=grade_order,
    ordered=True
)

# ------------------------------
# AGGREGATE
# ------------------------------
agg = (
    df.groupby([
        "course_key",
        "major_at_time",
        "term_class_level",
        "term_season",
        "course_grade"
    ])
    .size()
    .reset_index(name="total_enrollments")
)

# Easier label
agg["major_group"] = agg["major_at_time"]

# ------------------------------
# CLASS LEVEL ORDER
# ------------------------------
level_order = ["Freshman", "Sophomore", "Junior", "Senior"]

agg["term_class_level"] = pd.Categorical(
    agg["term_class_level"],
    categories=level_order,
    ordered=True
)

# ------------------------------
# COURSE SELECTOR
# ------------------------------
course_list = sorted(agg["course_key"].unique())

course_search = st.text_input("Search for a course (e.g., BMS-300)")

filtered_courses = [
    c for c in course_list if course_search.upper() in c
] if course_search else course_list

selected_course = st.selectbox("Select a course", filtered_courses)

filtered_df = agg[agg["course_key"] == selected_course]

# ============================================================
# ✅ GRAPH 1: TIMING BY MAJOR
# ============================================================

st.markdown("## When Students Take This Course")

timing_df = filtered_df.groupby(
    ["major_group", "term_class_level"]
)["total_enrollments"].sum().reset_index()

timing_df["total_by_major"] = timing_df.groupby("major_group")["total_enrollments"].transform("sum")
timing_df["percent"] = timing_df["total_enrollments"] / timing_df["total_by_major"] * 100

fig1 = px.bar(
    timing_df,
    x="term_class_level",
    y="percent",
    color="major_group",
    text="total_enrollments",
    barmode="group",
    category_orders={"term_class_level": level_order}
)

fig1.update_traces(texttemplate='n=%{text}', textposition='outside')

st.plotly_chart(fig1, use_container_width=True)

# ============================================================
# ✅ GRAPH 2: GRADE DISTRIBUTION
# ============================================================

st.markdown("---")
st.markdown("## How Students Perform")

grade_df = filtered_df.groupby(
    ["major_group", "course_grade"]
)["total_enrollments"].sum().reset_index()

grade_df["total_by_major"] = grade_df.groupby("major_group")["total_enrollments"].transform("sum")
grade_df["percent"] = grade_df["total_enrollments"] / grade_df["total_by_major"] * 100

fig2 = px.bar(
    grade_df,
    x="course_grade",
    y="percent",
    color="major_group",
    text="total_enrollments",
    barmode="group",
    category_orders={"course_grade": grade_order}
)

fig2.update_traces(texttemplate='n=%{text}', textposition='outside')

st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# ✅ GRAPH 3: TIMING VS PERFORMANCE
# ============================================================

st.markdown("---")
st.markdown("## How Timing Relates to Performance")

selected_major = st.selectbox(
    "Select a Major",
    ["All"] + sorted(filtered_df["major_group"].unique())
)

filtered_major_df = filtered_df.copy()

if selected_major != "All":
    filtered_major_df = filtered_major_df[
        filtered_major_df["major_group"] == selected_major
    ]

valid_grades = ["A", "B", "C", "F", "W"]

filtered_major_df = filtered_major_df[
    filtered_major_df["course_grade"].isin(valid_grades)
]

timing_grade_df = filtered_major_df.groupby(
    ["term_class_level", "course_grade"]
)["total_enrollments"].sum().reset_index()

timing_grade_df["total_per_level"] = timing_grade_df.groupby(
    "term_class_level"
)["total_enrollments"].transform("sum")

timing_grade_df["percent"] = timing_grade_df["total_enrollments"] / timing_grade_df["total_per_level"] * 100

fig3 = px.bar(
    timing_grade_df,
    x="term_class_level",
    y="percent",
    color="course_grade",
    text="total_enrollments",
    barmode="group",
    category_orders={
        "term_class_level": level_order,
        "course_grade": grade_order
    }
)

fig3.update_traces(texttemplate='n=%{text}', textposition='outside')

st.plotly_chart(fig3, use_container_width=True)
# ============================================================
# ✅ GRAPH 4: PERFORMANCE BY SEMESTER CREDIT LOAD
# ============================================================

st.markdown("---")

st.markdown("## How Course Load Relates to Performance")

st.markdown(
    "This chart shows how **student grades vary based on the number of credits taken during a semester**. "
    "It helps identify whether heavier or lighter course loads are associated with better or worse outcomes. "
    "Each bar represents the **percentage of grades earned** within a given credit load range, "
    "with labels showing the total number of course attempts (n)."
)


# Optional sub-filter (within selected range)
# -----------------------------------
# TERM FILTER FOR GRAPH 4 ✅ CLEAN VERSION
# -----------------------------------

with st.expander("Filter Terms for Credit Load Analysis", expanded=False):

    all_terms = sorted(df["term_label"].unique())

    selected_terms_for_load = st.multiselect(
        "Semesters to Include",
        options=all_terms,
        default=all_terms
    )

st.caption(f"{len(selected_terms_for_load)} of {len(all_terms)} terms selected")

# Apply filter
load_df = df[df["term_label"].isin(selected_terms_for_load)]

# Bin credit load (optional — makes plot cleaner)
load_df["credit_load_bin"] = pd.cut(
    load_df["term_credit_load"],
    bins=[0, 6, 12, 15, 18, 30],
    labels=["0-6", "7-12", "13-15", "16-18", "19+"]
)

# Aggregate
credit_perf_df = load_df.groupby(
    ["credit_load_bin", "course_grade"]
).size().reset_index(name="count")

credit_perf_df["total"] = credit_perf_df.groupby("credit_load_bin")["count"].transform("sum")

credit_perf_df["percent"] = credit_perf_df["count"] / credit_perf_df["total"] * 100

# Grade colors
grade_colors = {
    "A+": "#1a9850", "A": "#1a9850", "A-": "#66bd63",
    "B+": "#a6d96a", "B": "#d9ef8b", "B-": "#fee08b",
    "C+": "#fdae61", "C": "#f46d43", "C-": "#d73027",
    "D": "#a50026", "F": "#67001f", "W": "#999999"
}

fig4 = px.bar(
    credit_perf_df,
    x="credit_load_bin",
    y="percent",
    color="course_grade",
    text="count",
    barmode="group",
    category_orders={
        "course_grade": grade_order
    },
    color_discrete_map=grade_colors
)

fig4.update_traces(
    texttemplate='n=%{text}',
    textposition='outside'
)

fig4.update_layout(
    yaxis_title="Percent of Students",
    xaxis_title="Semester Credit Load",
    bargap=0.2,
    bargroupgap=0.1,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(fig4, use_container_width=True)