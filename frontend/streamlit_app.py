from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Daily Routine Optimizer", layout="wide")
st.title("🧠 Daily Routine Optimizer")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Add Task")
    with st.form("task_form"):
        title = st.text_input("Task title")
        description = st.text_area("Description")
        priority = st.slider("Priority", 1, 5, 3)
        task_type = st.selectbox("Task type", ["work", "health", "study", "personal", "general"])
        assigned_dt = st.datetime_input("Assigned time", value=datetime.now() + timedelta(hours=1))
        duration = st.number_input("Duration (minutes)", min_value=5, value=30)
        reminder = st.number_input("Reminder minutes before", min_value=0, value=10)
        submitted = st.form_submit_button("Create task")

    if submitted and title:
        payload = {
            "title": title,
            "description": description,
            "priority": priority,
            "task_type": task_type,
            "assigned_time": assigned_dt.isoformat(),
            "duration_minutes": int(duration),
            "reminder_minutes_before": int(reminder),
        }
        resp = requests.post(f"{API_URL}/tasks", json=payload, timeout=20)
        st.success(f"Task created: {resp.json()['title']}")

with col2:
    st.subheader("Dashboard")
    tasks = requests.get(f"{API_URL}/tasks", timeout=20).json()
    analytics = requests.get(f"{API_URL}/analytics", timeout=20).json()

    a, b, c, d = st.columns(4)
    a.metric("Total", analytics["total_tasks"])
    b.metric("Completed", analytics["completed_tasks"])
    c.metric("Completion Rate", f"{analytics['completion_rate']*100:.1f}%")
    d.metric("Streak", analytics["streak_days"])

    st.write("### Most productive hours", analytics["most_productive_hours"])
    st.write("### Completion by task type")
    st.bar_chart(pd.Series(analytics["completion_by_task_type"]))

    st.write("### Calendar / Schedule")
    if tasks:
        df = pd.DataFrame(tasks)
        df["assigned_time"] = pd.to_datetime(df["assigned_time"])
        st.dataframe(df[["title", "task_type", "priority", "assigned_time", "status"]], use_container_width=True)

    st.write("### AI Suggestions")
    if st.button("Generate optimized alarm suggestions"):
        suggestions = requests.get(f"{API_URL}/ml/suggestions", timeout=20).json()
        st.json(suggestions)
