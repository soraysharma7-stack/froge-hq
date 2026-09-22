"""Employee registry — employees are DATA + ROLE + CAPABILITIES + SKILLS + TOOLS + PERMISSIONS.

Employees are DORMANT until activated by a mission. New employees can be added
to the registry without rewriting the system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EmployeeState(str, Enum):
    DORMANT = "DORMANT"
    AVAILABLE = "AVAILABLE"
    QUEUED = "QUEUED"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass
class Employee:
    id: str
    name: str
    department: str
    role: str
    personality: str
    capabilities: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    security_level: int = 1
    enabled: bool = True
    state: EmployeeState = EmployeeState.DORMANT

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "personality": self.personality,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "tools": self.tools,
            "security_level": self.security_level,
            "enabled": self.enabled,
            "state": self.state.value,
        }


_REGISTRY: dict[str, Employee] = {}


def register(employee: Employee) -> None:
    _REGISTRY[employee.id] = employee


def get(employee_id: str) -> Employee | None:
    return _REGISTRY.get(employee_id)


def all_employees() -> list[Employee]:
    return list(_REGISTRY.values())


def seed_defaults() -> None:
    register(Employee(
        id="maya", name="Maya", department="orchestration",
        role="Chief AI Orchestrator",
        personality="strategic, calm, direct, honest, concise",
        capabilities=["orchestration", "planning", "delegation", "verification"],
        skills=["mission_planning"], tools=[], security_level=5,
    ))
    register(Employee(
        id="alex", name="Alex", department="software_engineering",
        role="Software Engineer",
        personality="methodical, pragmatic",
        capabilities=["coding", "file_operations"],
        skills=["filesystem_write"], tools=["workspace_file_writer"], security_level=2,
    ))
    register(Employee(
        id="sam", name="Sam", department="qa",
        role="QA Engineer",
        personality="skeptical, evidence-driven",
        capabilities=["testing", "verification"],
        skills=["filesystem_verify"], tools=["workspace_file_verifier"], security_level=2,
    ))
    register(Employee(
        id="rex", name="Rex", department="security",
        role="Security Lead",
        personality="cautious, rule-bound",
        capabilities=["policy_enforcement", "audit"],
        skills=[], tools=[], security_level=4,
    ))


seed_defaults()
