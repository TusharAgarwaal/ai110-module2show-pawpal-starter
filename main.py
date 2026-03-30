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
        Task(
            title="Playtime",
            duration_minutes=20,
            priority="medium",
            earliest_minute=17 * 60,  # 5:00 PM
            latest_minute=19 * 60,    # 7:00 PM
            category="enrichment",
        ),
        Task(
            title="Evening feeding",
            duration_minutes=10,
            priority="high",
            earliest_minute=18 * 60,  # 6:00 PM
            latest_minute=19 * 60,    # 7:00 PM
            category="feeding",
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
