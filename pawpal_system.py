from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple


def hhmm_to_minutes(value: str) -> int:
    """Convert HH:MM string to minutes since midnight."""
    try:
        hours, mins = value.split(":")
        return int(hours) * 60 + int(mins)
    except Exception:
        raise ValueError(f"Invalid HH:MM format: {value}")


def minutes_to_hhmm(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM string."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    frequency: str = "once"  # once|daily|weekly
    completed: bool = False
    earliest_minute: int = 0
    latest_minute: int = 24 * 60
    category: str = ""
    notes: str = ""
    due_date: Optional[date] = None

    PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
    FREQUENCY_WEIGHTS = {"once": 0, "daily": 1, "weekly": 0.5}

    def is_valid(self) -> bool:
        return bool(
            self.title
            and self.duration_minutes > 0
            and self.priority in self.PRIORITY_WEIGHTS
            and 0 <= self.earliest_minute < self.latest_minute <= 24 * 60
            and self.duration_minutes <= (self.latest_minute - self.earliest_minute)
        )

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh incomplete copy of this task for its next occurrence, or None if frequency is 'once'."""
        if self.frequency not in {"daily", "weekly"}:
            return None

        recurrence = deepcopy(self)
        recurrence.completed = False

        # Shift due_date by the recurrence interval (if set), otherwise from today.
        base_date = recurrence.due_date or date.today()
        if self.frequency == "daily":
            recurrence.due_date = base_date + timedelta(days=1)
        elif self.frequency == "weekly":
            recurrence.due_date = base_date + timedelta(weeks=1)

        return recurrence

    def mark_complete(self) -> Optional[Task]:
        """Mark this task as completed and return the next occurrence if it is recurring."""
        self.completed = True

        # Set due date to now for completed task if unset
        if self.due_date is None:
            self.due_date = date.today()

        next_task = self.next_occurrence()
        return next_task

    def urgency_score(self, current_time: int = 0) -> float:
        if current_time >= self.latest_minute:
            return -1
        time_until_deadline = self.latest_minute - current_time
        slack = max(1, time_until_deadline - self.duration_minutes)
        priority_weight = self.PRIORITY_WEIGHTS.get(self.priority, 0)
        frequency_weight = self.FREQUENCY_WEIGHTS.get(self.frequency, 0)
        window_factor = 1 / slack
        return priority_weight * 100 + window_factor * 100 + frequency_weight * 10


@dataclass
class Pet:
    name: str
    species: str
    age: int
    needs: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)

    def complete_task(self, task: Task) -> None:
        """Mark a task complete and append the next occurrence to this pet's task list if recurring."""
        next_task = task.mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)


@dataclass
class Owner:
    name: str
    daily_available_minutes: int
    availability_windows: List[Tuple[int, int]] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def get_all_tasks(self) -> List[Task]:
        return [task for pet in self.pets for task in pet.tasks]

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []

    def get_tasks_by_status(self, completed: bool = False, pet_name: Optional[str] = None) -> List[Task]:
        """Filter tasks by completion status and optionally pet name."""
        tasks = self.get_tasks_for_pet(pet_name) if pet_name else self.get_all_tasks()
        return [t for t in tasks if t.completed == completed]

    def set_availability_windows_from_strings(self, windows: List[str]) -> None:
        """Set availability windows from strings like '08:30-12:00'."""
        parsed = []
        for s in windows:
            start, end = s.split("-")
            parsed_start = hhmm_to_minutes(start.strip())
            parsed_end = hhmm_to_minutes(end.strip())
            parsed.append((parsed_start, parsed_end))
        self.availability_windows = sorted(parsed, key=lambda w: w[0])

    def is_task_feasible(self, task: Task) -> bool:
        if not task.is_valid() or task.completed:
            return False
        if not self.availability_windows:
            return True
        for win_start, win_end in self.availability_windows:
            if task.earliest_minute < win_end and task.latest_minute > win_start:
                if (max(task.earliest_minute, win_start) + task.duration_minutes) <= min(task.latest_minute, win_end):
                    return True
        return False


@dataclass
class Plan:
    plan_date: date
    tasks: List[Task] = field(default_factory=list)
    total_duration: int = 0
    explanation: str = ""
    task_schedule: List[Dict[str, int]] = field(default_factory=list)  # each item: {'task': Task, 'pet': str, 'start': int, 'end': int}
    conflicts: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.tasks) == 0


class Scheduler:
    def detect_conflicts(self, task_schedule: List[Dict[str, int]]) -> List[str]:
        conflicts = []
        for i in range(len(task_schedule)):
            for j in range(i + 1, len(task_schedule)):
                a = task_schedule[i]
                b = task_schedule[j]
                # overlap check: a.start < b.end and b.start < a.end
                if a['start'] < b['end'] and b['start'] < a['end']:
                    conflicts.append(
                        f"Conflict between '{a['task'].title}' (pet {a['pet']}) at {minutes_to_hhmm(a['start'])}-{minutes_to_hhmm(a['end'])} "
                        f"and '{b['task'].title}' (pet {b['pet']}) at {minutes_to_hhmm(b['start'])}-{minutes_to_hhmm(b['end'])}."
                    )
        return conflicts

    def expand_recurring_tasks(self, tasks: List[Task]) -> List[Task]:
        expanded: List[Task] = []
        for task in tasks:
            expanded.append(task)
            if task.frequency in {"daily", "weekly"} and not task.completed:
                recurring = deepcopy(task)
                recurring.frequency = "once"
                recurring.notes = f"Recurring event ({task.frequency})"
                expanded.append(recurring)
        return expanded

    def generate_plan(
        self,
        owner: Owner,
        pet: Optional[Pet] = None,
        tasks: Optional[List[Task]] = None,
    ) -> Plan:
        if tasks is not None:
            all_tasks = tasks
        elif pet is not None:
            all_tasks = pet.tasks
        else:
            all_tasks = owner.get_all_tasks()

        # map tasks back to pet names for conflict reporting
        task_to_pet = {id(t): p.name for p in owner.pets for t in p.tasks}

        all_tasks = self.expand_recurring_tasks(all_tasks)

        if owner.daily_available_minutes <= 0:
            return Plan(plan_date=date.today(), explanation="No available owner minutes.")

        feasible_tasks = [t for t in all_tasks if owner.is_task_feasible(t)]
        if not feasible_tasks:
            return Plan(plan_date=date.today(), explanation="No feasible tasks to schedule.")

        selected = self.select_tasks(owner, feasible_tasks)

        windows = sorted(owner.availability_windows, key=lambda w: w[0]) if owner.availability_windows else [(0, 24 * 60)]
        current_time = windows[0][0]
        window_idx = 0

        scheduled = []
        dropped = []

        task_schedule = []

        for task in selected:
            task_scheduled = False
            while window_idx < len(windows):
                win_start, win_end = windows[window_idx]
                candidate_start = max(current_time, win_start, task.earliest_minute)
                candidate_end = candidate_start + task.duration_minutes

                if candidate_end <= min(win_end, task.latest_minute):
                    # conflict detection can find overlaps in already scheduled periods
                    overlap = any(
                        (candidate_start < slot['end'] and slot['start'] < candidate_end)
                        for slot in task_schedule
                    )
                    if overlap:
                        dropped.append((task, "Conflict with existing scheduled task"))
                        task_scheduled = True
                        break

                    scheduled.append(task)
                    task_schedule.append({
                        'task': task,
                        'pet': task_to_pet.get(id(task), 'unknown'),
                        'start': candidate_start,
                        'end': candidate_end,
                    })
                    current_time = candidate_end
                    task_scheduled = True
                    break

                if candidate_start >= win_end:
                    window_idx += 1
                    if window_idx < len(windows):
                        current_time = windows[window_idx][0]
                    continue

                dropped.append((task, f"No slot in window {win_start}-{win_end}"))
                task_scheduled = True
                break

            if not task_scheduled and window_idx >= len(windows):
                dropped.append((task, "No remaining availability window"))

        total_duration = sum(task.duration_minutes for task in scheduled)
        plan = Plan(
            plan_date=date.today(),
            tasks=scheduled,
            total_duration=total_duration,
            task_schedule=task_schedule,
        )

        plan.conflicts = self.detect_conflicts(task_schedule)
        plan.explanation = self.explain_plan(plan, dropped)
        return plan

    def select_tasks(self, owner: Owner, tasks: List[Task]) -> List[Task]:
        remaining = owner.daily_available_minutes
        scored = sorted(
            tasks,
            key=lambda t: (-t.urgency_score(), t.earliest_minute, t.duration_minutes, t.title),
        )

        selected = []
        for task in scored:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes

        return selected

    def explain_plan(self, plan: Plan, dropped: Optional[List[Tuple[Task, str]]] = None) -> str:
        if plan.is_empty() and not dropped:
            return "No tasks could be scheduled for today."

        lines = [f"Scheduled {len(plan.tasks)} tasks, total {plan.total_duration} minutes:"]
        for i, task in enumerate(plan.tasks, start=1):
            lines.append(
                f"{i}. {task.title} ({task.priority}, {task.duration_minutes}m)"
                + (f", window {task.earliest_minute}-{task.latest_minute}" if task.earliest_minute or task.latest_minute != 24 * 60 else "")
            )

        if dropped:
            lines.append(f"\nDropped {len(dropped)} tasks due to constraints:")
            for t, reason in dropped:
                lines.append(f" - {t.title}: {reason}")

        if plan.conflicts:
            lines.append(f"\nDetected {len(plan.conflicts)} conflict(s):")
            for conflict in plan.conflicts:
                lines.append(f" - {conflict}")

        return "\n".join(lines)
