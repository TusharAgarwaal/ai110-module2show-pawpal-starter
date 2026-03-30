import streamlit as st
from datetime import date
from pawpal_system import Task, Pet, Owner, Plan, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# ── Owner & Pet ───────────────────────────────────────────────────────────────

st.subheader("Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    daily_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=120)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

st.divider()

# ── Tasks ─────────────────────────────────────────────────────────────────────

st.subheader("Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        Task(title=task_title, duration_minutes=int(duration), priority=priority)
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table([
        {"title": t.title, "duration_minutes": t.duration_minutes, "priority": t.priority}
        for t in st.session_state.tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Generate Schedule ─────────────────────────────────────────────────────────

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        pet = Pet(name=pet_name, species=species, age=0, tasks=st.session_state.tasks)
        owner = Owner(
            name=owner_name,
            daily_available_minutes=int(daily_minutes),
            pets=[pet],
        )

        scheduler = Scheduler()

        # Sorting helper: display before scheduling
        sorted_tasks = sorted(
            owner.get_all_tasks(),
            key=lambda t: (t.earliest_minute, t.duration_minutes, t.title),
        )

        st.info("Tasks sorted by earliest start time")
        st.table([
            {
                "title": t.title,
                "pet": owner.get_tasks_for_pet("Mochi").count(t) and "Mochi" or "Luna" if hasattr(t, 'title') else "Unknown",
                "start": f"{t.earliest_minute//60:02d}:{t.earliest_minute%60:02d}",
                "duration": t.duration_minutes,
                "priority": t.priority,
                "status": "done" if t.completed else "todo",
            }
            for t in sorted_tasks
        ])

        plan = scheduler.generate_plan(owner=owner)

        st.success(f"Schedule for {date.today()}")
        st.info("Use the plan details below to track tasks and avoid conflicts")

        if plan.tasks:
            st.subheader("Final Plan")
            st.table([
                {
                    "title": task.title,
                    "duration": task.duration_minutes,
                    "priority": task.priority,
                    "window": f"{task.earliest_minute//60:02d}:{task.earliest_minute%60:02d} - {task.latest_minute//60:02d}:{task.latest_minute%60:02d}",
                    "due_date": task.due_date or "N/A",
                }
                for task in plan.tasks
            ])
        else:
            st.warning("No tasks could be scheduled. Check availability and task constraints.")

        if plan.conflicts:
            st.warning("Conflicts detected:")
            for conflict in plan.conflicts:
                st.warning(conflict)

