"""
TODO Checklist Validator

A script to parse, validate, and report on TODO items from a markdown file.

This tool extracts tasks formatted in a specific way, validates their
properties like priority and effort, and checks for inconsistencies.
It is designed to be run from the command line, providing the path to the
markdown file as an argument.

Usage:
    python todo_checklist_validator.py /path/to/your/tasks.md
"""
import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# --- Constants and Configuration ---

# Regex to capture components of a TODO item.
# It uses named groups for clarity and makes the dependencies part optional.
TODO_REGEX = re.compile(
    r"-\s*\[\s*\]\s*(?P<task>.+?)\s*"
    r"\((?:Priority:\s*(?P<priority>\w+))?,"
    r"\s*(?:Effort:\s*(?P<effort>\d+))?,"
    r"\s*(?:Dependencies:\s*(?P<deps>.*?))?\)"
)

# --- Enums and Data Classes ---


class Priority(Enum):
    """Enumeration for task priorities."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class TodoItem:
    """Represents a single TODO item with its properties."""
    task: str
    priority: Priority
    effort: int
    dependencies: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"TodoItem(task='{self.task}', priority={self.priority.name}, "
            f"effort={self.effort}, dependencies={self.dependencies})"
        )

# --- Core Functions ---


def extract_todos_from_file(file_path: str) -> Optional[List[TodoItem]]:
    """
    Extracts and parses TODO items from a given markdown file.

    Args:
        file_path: The path to the markdown file.

    Returns:
        A list of parsed TodoItem objects, or None if a fatal error occurs.
    """
    todos: List[TodoItem] = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file, 1):
                match = TODO_REGEX.match(line)
                if not match:
                    continue

                data = match.groupdict()
                try:
                    effort = int(data.get("effort") or 0)

                    dependencies_str = data.get("deps") or ""
                    dependencies = [
                        dep.strip()
                        for dep in dependencies_str.split(',')
                        if dep.strip()
                    ]

                    todo = TodoItem(
                        task=data["task"].strip(),
                        priority=Priority(
                            data.get("priority", "Medium").strip()
                        ),
                        effort=effort,
                        dependencies=dependencies,
                    )
                    todos.append(todo)
                except (ValueError, TypeError) as e:
                    logging.warning(
                        "Skipping malformed TODO on line %d: %s (%s)",
                        i, line.strip(), e
                    )
    except FileNotFoundError:
        logging.error("File not found: %s", file_path)
        return None
    except OSError as e:
        logging.error(
            "An OS error occurred while reading %s: %s", file_path, e
        )
        return None
    return todos


def validate_todo_checklist(todos: List[TodoItem]) -> List[str]:
    """
    Validates a list of TODO items for completeness and logical consistency.

    Args:
        todos: A list of TodoItem objects.

    Returns:
        A list of string descriptions of any validation errors found.
    """
    errors: List[str] = []
    task_names = {todo.task for todo in todos}

    for todo in todos:
        if not todo.task:
            errors.append(
                f"Found a TODO item with an empty task description: {todo}"
            )

        if todo.effort <= 0:
            errors.append(
                f"Effort for task '{todo.task}' must be a positive "
                f"integer, but got {todo.effort}."
            )

        for dep in todo.dependencies:
            if not dep:
                errors.append(f"Task '{todo.task}' has an empty dependency.")
            elif dep not in task_names:
                errors.append(
                    f"Task '{todo.task}' has an undefined dependency: '{dep}'"
                )
    return errors

# --- Main Execution ---


def run_validation(file_path: str) -> int:
    """
    Runs the core validation logic on a given file.

    Args:
        file_path: The path to the markdown file.

    Returns:
        An exit code: 0 for success, 1 for failure.
    """
    logging.info("Starting validation for: %s", file_path)

    todos = extract_todos_from_file(file_path)
    if todos is None:
        logging.error("Aborting due to fatal error.")
        return 1

    if not todos:
        logging.warning(
            "No TODO items were extracted. Please check the file format."
        )
        return 0  # Not a failure, but nothing to do.

    errors = validate_todo_checklist(todos)

    print("\n--- Extracted TODO Items ---")
    for todo in todos:
        print(todo)
    print("--------------------------")

    if errors:
        logging.error(
            "\nTODO Checklist Validation Failed with %d errors:", len(errors)
        )
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        logging.info("\nTODO Checklist Validation Passed!")
        return 0


def main() -> int:
    """
    Parses command-line arguments and runs the validation.

    Returns:
        An exit code from the validation run.
    """
    logging.basicConfig(
        level=logging.INFO, format='%(levelname)s: %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="Validate a TODO checklist in a markdown file."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the markdown file containing the TODO list.",
        default=".kiro/specs/phoenix-hydra-system-review/tasks.md",
        nargs='?'
    )
    args = parser.parse_args()

    return run_validation(args.file_path)


if __name__ == "__main__":
    sys.exit(main())
