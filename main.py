from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

# ── Pets ──────────────────────────────────────────────────────────────────────

mochi = Pet(
    name="Mochi",
    species="dog",
    age=3,
    tasks=[
        Task(
            title="Morning walk",
            duration_minutes=30,
            priority="high",
            earliest_minute=7 * 60,   # 7:00 AM
            latest_minute=9 * 60,     # 9:00 AM
            category="exercise",
        ),
        Task(
            title="Breakfast",
            duration_minutes=10,
            priority="high",
            earliest_minute=7 * 60,   # 7:00 AM
            latest_minute=8 * 60,     # 8:00 AM
            category="feeding",
        ),
    ],
)

luna = Pet(
    name="Luna",
    species="cat",
    age=5,
    tasks=[
        # Intentionally out of chronological order to demonstrate sorting/filtering
        Task(
            title="Evening feeding",
            duration_minutes=10,
            priority="high",
            earliest_minute=18 * 60,  # 6:00 PM
            latest_minute=19 * 60,    # 7:00 PM
            category="feeding",
        ),
        Task(
            title="Playtime",
            duration_minutes=20,
            priority="medium",
            earliest_minute=17 * 60,  # 5:00 PM
            latest_minute=19 * 60,    # 7:00 PM
            category="enrichment",
        ),
    ],
)

# ── Owner ─────────────────────────────────────────────────────────────────────

jordan = Owner(
    name="Jordan",
    daily_available_minutes=120,
    availability_windows=[
        (7 * 60, 9 * 60),    # 7:00–9:00 AM
        (17 * 60, 19 * 60),  # 5:00–7:00 PM
    ],
    pets=[mochi, luna],
)

# ── Add out-of-order tasks and status filtering demo ───────────────────────────

mochi.tasks.append(
    Task(
        title="Late afternoon brush",  # this will be sorted by scheduler logic
        duration_minutes=15,
        priority="low",
        earliest_minute=16 * 60,
        latest_minute=18 * 60,
        category="grooming",
    )
)

# Mark one task completed to test completed filtering
mochi.tasks[0].mark_complete()  # Morning walk done

print("\n--- TASK FILTER/STATUS DEMO ---")
print("All tasks (unfiltered):")
for t in jordan.get_all_tasks():
    print(f"  - [{t.priority}] {t.title} ({'done' if t.completed else 'todo'})")

print("\nIncomplete tasks for Jordan:")
for t in jordan.get_tasks_by_status(completed=False):
    print(f"  - {t.title} (pet-aware, incomplete)")

print("\nTasks for Mochi (incomplete):")
for t in jordan.get_tasks_by_status(completed=False, pet_name='Mochi'):
    print(f"  - {t.title}")

# ── Schedule ──────────────────────────────────────────────────────────────────

scheduler = Scheduler()
plan = scheduler.generate_plan(owner=jordan)

# ── Output ────────────────────────────────────────────────────────────────────

print("=" * 50)
print(f"  Today's Schedule — {date.today()}")
print(f"  Owner : {jordan.name}")
print(f"  Pets  : {', '.join(p.name for p in jordan.pets)}")
print("=" * 50)
print(plan.explanation)
print("=" * 50)
