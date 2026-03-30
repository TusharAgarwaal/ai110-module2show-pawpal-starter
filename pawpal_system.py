from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Tuple


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    frequency: str = "once"
    completed: bool = False
    earliest_minute: int = 0
    latest_minute: int = 24 * 60
    category: str = ""
    notes: str = ""

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_valid(self) -> bool:
        """Return True if the task has a title, positive duration, valid priority, and consistent time window."""
        return bool(
            self.title
            and self.duration_minutes > 0
            and self.priority in {"low", "medium", "high"}
            and 0 <= self.earliest_minute < self.latest_minute <= 24 * 60
        )

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    age: int
    needs: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    daily_available_minutes: int
    availability_windows: List[Tuple[int, int]] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def get_all_tasks(self) -> List[Task]:
        """Collect and return all tasks across every pet the owner has."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Plan:
    plan_date: date
    tasks: List[Task] = field(default_factory=list)
    total_duration: int = 0
    explanation: str = ""

    def is_empty(self) -> bool:
        """Return True if no tasks have been scheduled."""
        return len(self.tasks) == 0


class Scheduler:
    PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}

    def generate_plan(self, owner: Owner, pet: Pet | None = None, tasks: List[Task] | None = None) -> Plan:
        """Build and return a daily plan by selecting and ordering valid tasks within the owner's availability."""
        if tasks is None:
            tasks = owner.get_all_tasks()
        if owner.daily_available_minutes <= 0:
            return Plan(plan_date=date.today(), tasks=[], total_duration=0, explanation="No available owner minutes.")

        valid_tasks = [t for t in tasks if t.is_valid() and not t.completed]
        if not valid_tasks:
            return Plan(plan_date=date.today(), tasks=[], total_duration=0, explanation="No valid tasks to schedule.")

        selected = self.select_tasks(valid_tasks, owner.daily_available_minutes)

        windows = sorted(owner.availability_windows, key=lambda w: w[0]) if owner.availability_windows else [(0, 24 * 60)]
        window_idx = 0
        current_time = windows[0][0]

        scheduled = []
        dropped = []

        for task in selected:
            while window_idx < len(windows):
                win_start, win_end = windows[window_idx]
                current_time = max(current_time, win_start, task.earliest_minute)

                if current_time + task.duration_minutes <= min(win_end, task.latest_minute):
                    break

                if current_time >= win_end:
                    window_idx += 1
                    if window_idx < len(windows):
                        current_time = windows[window_idx][0]
                    continue

                break

            if window_idx >= len(windows):
                dropped.append((task, "no remaining availability window"))
                continue

            win_start, win_end = windows[window_idx]
            current_time = max(current_time, win_start, task.earliest_minute)

            if current_time + task.duration_minutes > min(win_end, task.latest_minute):
                dropped.append((task, f"cannot fit within window {win_start}-{win_end} and task constraint {task.earliest_minute}-{task.latest_minute}"))
                continue

            scheduled.append(task)
            current_time += task.duration_minutes

        plan = Plan(
            plan_date=date.today(),
            tasks=scheduled,
            total_duration=sum(task.duration_minutes for task in scheduled),
            explanation="",
        )
        plan.explanation = self.explain_plan(plan, dropped)
        return plan

    def select_tasks(self, tasks: List[Task], available_minutes: int) -> List[Task]:
        """Select tasks that fit within available minutes, ordered by priority then shortest duration."""
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-self.PRIORITY_RANK.get(t.priority, 0), t.duration_minutes, t.title),
        )
        selected = []
        remaining = available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes

        return selected

    def explain_plan(self, plan: Plan, dropped: List[Tuple[Task, str]] | None = None) -> str:
        """Return a human-readable summary of the scheduled tasks and any dropped tasks with reasons."""
        if plan.is_empty() and not dropped:
            return "No tasks could be scheduled for today."

        lines = [f"Scheduled {len(plan.tasks)} tasks, total {plan.total_duration} minutes:"]
        for idx, task in enumerate(plan.tasks, start=1):
            lines.append(
                f"{idx}. {task.title} ({task.priority}, {task.duration_minutes}m)"
                + (f", window {task.earliest_minute}-{task.latest_minute}" if task.earliest_minute or task.latest_minute != 24 * 60 else "")
            )

        lines.append("\nSelected tasks by priority and then shortest duration to fit available time.")

        if dropped:
            lines.append(f"\nDropped {len(dropped)} task(s) due to time constraints:")
            for task, reason in dropped:
                lines.append(f"  - {task.title}: {reason}")

        return "\n".join(lines)
