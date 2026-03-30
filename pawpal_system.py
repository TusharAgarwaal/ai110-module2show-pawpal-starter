from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Tuple


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    earliest_minute: int = 0
    latest_minute: int = 24 * 60
    category: str = ""
    notes: str = ""

    def is_valid(self) -> bool:
        return bool(self.title and self.duration_minutes > 0 and self.priority in {"low", "medium", "high"})


@dataclass
class Pet:
    name: str
    species: str
    age: int
    needs: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)


@dataclass
class Owner:
    name: str
    daily_available_minutes: int
    availability_windows: List[Tuple[int, int]] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)


@dataclass
class Plan:
    plan_date: date
    tasks: List[Task] = field(default_factory=list)
    total_duration: int = 0
    explanation: str = ""

    def is_empty(self) -> bool:
        return len(self.tasks) == 0


class Scheduler:
    def generate_plan(self, owner: Owner, pet: Pet, tasks: List[Task]) -> Plan:
        raise NotImplementedError("Scheduler.generate_plan must be implemented")

    def select_tasks(self, tasks: List[Task], available_minutes: int) -> List[Task]:
        raise NotImplementedError("Scheduler.select_tasks must be implemented")

    def explain_plan(self, plan: Plan) -> str:
        raise NotImplementedError("Scheduler.explain_plan must be implemented")
