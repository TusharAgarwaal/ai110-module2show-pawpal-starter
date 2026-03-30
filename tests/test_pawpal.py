from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_task_status():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_to_pet_increases_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.tasks.append(Task(title="Breakfast", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1


def test_scheduler_respects_availability_windows_and_priority():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.tasks.append(Task(title="Late night snack", duration_minutes=20, priority="high", earliest_minute=23*60, latest_minute=24*60))
    pet.tasks.append(Task(title="Morning walk", duration_minutes=30, priority="medium", earliest_minute=8*60, latest_minute=10*60))

    owner = Owner(name="Jordan", daily_available_minutes=60, availability_windows=[(8*60, 11*60)], pets=[pet])
    plan = Scheduler().generate_plan(owner=owner)

    assert "Morning walk" in plan.explanation
    assert "Late night snack" not in plan.explanation

    # Late night snack is not feasible in owner's window and should be ignored
    assert len(plan.tasks) == 1
    assert plan.tasks[0].title == "Morning walk"


def test_owner_get_all_tasks():
    pet1 = Pet(name="Mochi", species="dog", age=3, tasks=[Task(title="Walk", duration_minutes=30, priority="high")])
    pet2 = Pet(name="Kitty", species="cat", age=2, tasks=[Task(title="Cuddle", duration_minutes=15, priority="low")])
    owner = Owner(name="Jordan", daily_available_minutes=120, pets=[pet1, pet2])

    all_tasks = owner.get_all_tasks()
    assert len(all_tasks) == 2


def test_owner_get_tasks_by_status_and_pet():
    pet1 = Pet(name="Mochi", species="dog", age=3, tasks=[Task(title="Walk", duration_minutes=30, priority="high", completed=True), Task(title="Play", duration_minutes=20, priority="medium")])
    pet2 = Pet(name="Kitty", species="cat", age=2, tasks=[Task(title="Cuddle", duration_minutes=15, priority="low")])
    owner = Owner(name="Jordan", daily_available_minutes=120, pets=[pet1, pet2])

    assert len(owner.get_tasks_by_status(completed=True)) == 1
    assert owner.get_tasks_by_status(completed=True)[0].title == "Walk"
    assert len(owner.get_tasks_by_status(completed=False)) == 2

    assert len(owner.get_tasks_by_status(completed=False, pet_name="Mochi")) == 1
    assert len(owner.get_tasks_by_status(completed=False, pet_name="Kitty")) == 1


def test_scheduler_conflict_detection_manual():
    task1 = Task(title="Task1", duration_minutes=30, priority="high", earliest_minute=480, latest_minute=520)
    task2 = Task(title="Task2", duration_minutes=30, priority="high", earliest_minute=490, latest_minute=530)

    scheduler = Scheduler()
    conflicts = scheduler.detect_conflicts([
        {"task": task1, "pet": "Mochi", "start": 480, "end": 510},
        {"task": task2, "pet": "Luna", "start": 490, "end": 520},
    ])

    assert len(conflicts) == 1
    assert "Task1" in conflicts[0] and "Task2" in conflicts[0]


def test_mark_complete_daily_recurring_updates_due_date():
    task = Task(title="Feed", duration_minutes=10, priority="high", frequency="daily")
    assert task.completed is False
    assert task.due_date is None

    next_task = task.mark_complete()
    assert task.completed is True
    assert task.due_date == date.today()

    assert next_task is not None
    assert next_task.frequency == "daily"
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
