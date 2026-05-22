# Curriculum Mapping

This repository contains a Streamlit dashboard and a dataset builder for exploring student course timing, grades, and major-related course patterns.

## Contents

- `Test App/app.py` — Streamlit dashboard for course timing and grade exploration.
- `Test App/output/build_dataset.py` — Data preparation script that processes CSU course, term, and student datapoints.
- `Test App/student_course_trajectory.csv` — Dataset used by the Streamlit dashboard.
- `Test App/output/course_datapoints.tsv` — Course datapoints used by `build_dataset.py`.
- `Test App/output/student_datapoints.tsv` — Student datapoints used by `build_dataset.py`.
- `Test App/output/term_datapoints.tsv` — Term datapoints used by `build_dataset.py`.
- `.gitignore` — Git ignore rules for common temporary and environment files.

## Getting Started

### Prerequisites

- Python 3.9+ (or compatible)
- `pip` package manager

### Install dependencies

```bash
pip install streamlit pandas plotly
```

### Run the dashboard

From the repository root:

```bash
cd "y:\Curriculum Mapping\Test App"
streamlit run app.py
```

### Run the dataset builder

From the repository root:

```bash
cd "y:\Curriculum Mapping\Test App\output"
python build_dataset.py
```

## Notes

- The Streamlit app loads `student_course_trajectory.csv` from the `Test App` folder.
- The build script expects TSV files in `Test App/output` and creates a consolidated dataframe for further analysis.

## Author

Created from the Curriculum Mapping project for course timing and grading analysis.
