"""Helper functions to interact with taskwarrior"""

import cog
import datetime
import subprocess
from dataclasses import dataclass

TASK_DRY_RUN_FLAGS = "rc.gc=0 rc.recurrence=0"

@dataclass
class DateFromTaskWarrior:
    date: datetime.date
    text: str

    @property
    def as_date(self):
        return self.date


def get_print_report_task(report_name, action):
    task_result = subprocess.run(f"task {TASK_DRY_RUN_FLAGS} rc.context= {report_name}".split(), capture_output=True)
    result_string = task_result.stdout.decode()
    lines = result_string.split("\n")
    for line in lines[3:]:
        try:
            due_date, task_id, description = line.split(maxsplit=2)
        except ValueError:
            continue
        try:
            due_date = datetime.date.fromisoformat(due_date)
        except ValueError: # some descriptions continue to the next line
            continue
        else:
            description = f"{action}:{description} {task_id}"
            yield DateFromTaskWarrior(date=due_date, text=description)

def get_due_tasks():
    yield from get_print_report_task("printdue", "due")

def get_scheduled_tasks():
    yield from get_print_report_task("printschedule", "scheduled")

def print_tasks(predicate:str):
    result = subprocess.run(f"task {TASK_DRY_RUN_FLAGS} {predicate}".split(), capture_output=True)
    cog.out(result.stdout.decode())

def print_projects_with_aliases_and_skip(known_aliases, skip, context):
    result = subprocess.run(f"task {TASK_DRY_RUN_FLAGS} rc.context={context} projects".split(), capture_output=True)
    result_string = result.stdout.decode()
    stack = []
    lines = result_string.split("\n")
    for line in lines[4:]:
        try:
            project_name, task_count = line.split()
        except ValueError:
            cog.outl(line)
            continue
        stack_depth = 0
        for index, character in enumerate(line):
            if character != ' ':
                stack_depth = index//2
                break
        if len(stack) > stack_depth + 1:
            stack.clear()
        elif stack and len(stack) == stack_depth + 1:
            stack.pop()
        stack.append(project_name)
        full_name = ".".join(stack)
        if full_name in skip:
            continue
        elif full_name in known_aliases:
            link = known_aliases[full_name]
            full_name = f"{full_name}: [[{link}]]"
        #cog.outl(f"{full_name}\t{task_count}")
        cog.outl(f" * {full_name}")

def generate_tasks(predicate:str):
    result = subprocess.run(f"task rc.context= {TASK_DRY_RUN_FLAGS} {predicate}".split(), capture_output=True)
    output = result.stdout.decode()
    return output

def generate_current_page_tasks():
    """Return all entries that have the current page as
    annotation"""
    current_file_name = "\\/".join(cog.inFile.split("/")[-2:])
    search_term = f"all +ANNOTATED /{current_file_name}/"
    return generate_tasks(search_term)

def print_current_page_tasks():
    cog.outl(generate_current_page_tasks())

