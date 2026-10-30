import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="School Result Analytics Dashboard", page_icon="📊", layout="wide")
DATA_DIR = Path(__file__).parent / "data"

CLASSES = {
    "Class XII – Commerce": {
        "file": "class_xii_commerce.csv",
        "subjects": ["English", "Accountancy", "Business_Studies", "Economics", "Informatics_Practices"],
    },
    "Class XI – Science": {
        "file": "class_xi_science.csv",
        "subjects": ["English", "Physics", "Chemistry", "Mathematics", "Biology"],
    },
}

st.title("SCHOOL RESULT ANALYTICS DASHBOARD")
st.caption("One dashboard for Class XII Commerce and Class XI Science")
st.info("The CSV templates contain fictional/demo data only. The below-40 support flag is illustrative, not an official board pass/fail decision.")

class_name = st.sidebar.selectbox("Select class", list(CLASSES))
cfg = CLASSES[class_name]
path = DATA_DIR / cfg["file"]
upload = st.sidebar.file_uploader("Upload CSV for this class", type=["csv"])

if upload is not None:
    raw = pd.read_csv(upload)
elif path.exists():
    raw = pd.read_csv(path)
else:
    st.error(f"Missing data/{cfg['file']}. Upload this file to the data folder in GitHub.")
    st.stop()

subjects = cfg["subjects"]
required = ["Student_ID", "Student_Name", "Section"] + subjects
missing = [c for c in required if c not in raw.columns]
if missing:
    st.error("Missing CSV columns: " + ", ".join(missing))
    st.stop()

data = raw.copy()
for s in subjects:
    data[s] = pd.to_numeric(data[s], errors="coerce")
if data[subjects].isna().any().any():
    st.error("Some marks are blank or non-numeric. Please correct the CSV.")
    st.stop()
if any(((data[s] < 0) | (data[s] > 100)).any() for s in subjects):
    st.error("All marks must be between 0 and 100 in this version.")
    st.stop()

data["Total"] = data[subjects].sum(axis=1)
data["Percentage"] = (data["Total"] / (len(subjects) * 100) * 100).round(2)
data["Needs_Support"] = data[subjects].lt(40).any(axis=1)

sections = ["All"] + sorted(data["Section"].dropna().astype(str).unique().tolist())
section = st.sidebar.selectbox("Select section", sections)
if section != "All":
    data = data[data["Section"].astype(str) == section]
if data.empty:
    st.warning("No student records found for this selection.")
    st.stop()

a,b,c,d = st.columns(4)
a.metric("Students", data["Student_ID"].nunique())
b.metric("Class average", f"{data['Percentage'].mean():.1f}%")
c.metric("Highest percentage", f"{data['Percentage'].max():.1f}%")
d.metric("Flagged for support", int(data["Needs_Support"].sum()))

st.subheader(f"{class_name} — Student-wise results")
cols = ["Student_ID", "Student_Name", "Section"] + subjects + ["Total", "Percentage", "Needs_Support"]
st.dataframe(data[cols].sort_values("Percentage", ascending=False), use_container_width=True)

left,right = st.columns(2)
with left:
    avg = data[subjects].mean().rename_axis("Subject").reset_index(name="Average_Mark")
    avg["Subject"] = avg["Subject"].str.replace("_", " ")
    st.plotly_chart(px.bar(avg, x="Subject", y="Average_Mark", range_y=[0,100],
                           title="Subject-wise average", text_auto=".1f"), use_container_width=True)
with right:
    st.plotly_chart(px.histogram(data, x="Percentage", nbins=10,
                                 title="Student percentage distribution"), use_container_width=True)

st.subheader("Top 5 students")
st.dataframe(data.nlargest(min(5, len(data)), "Percentage")[["Student_ID","Student_Name","Percentage"]],
             use_container_width=True)
st.subheader("Students who may need additional support")
support = data[data["Needs_Support"]]
if support.empty:
    st.success("No students are flagged by the demonstration rule.")
else:
    st.dataframe(support[["Student_ID","Student_Name","Section"] + subjects], use_container_width=True)

st.download_button("Download class analysis CSV", data[cols].to_csv(index=False).encode("utf-8"),
                   "school_result_analysis.csv", "text/csv")
st.caption("Privacy: keep identifiable student information in an approved, access-controlled location.")
