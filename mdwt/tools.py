import os
import datetime
import re
import cog
import subprocess
from dataclasses import dataclass
from .mdwt import HOME_PATH, WIKI_PATH

TODAY = datetime.date.today()

TASK_DRY_RUN_FLAGS = "rc.gc=0 rc.recurrence=0"

@dataclass
class DateFromTaskWarrior:
    date: datetime.date
    text: str

    @property
    def as_date(self):
        return self.date


@dataclass
class DateFromCalendar:
    month: int
    day: int
    text: str

    @property
    def as_date(self):
        if self.month < TODAY.month or (self.month == TODAY.month and self.day < TODAY.day):
            year = TODAY.year+1
        else:
            year = TODAY.year
        return datetime.date(year, self.month, self.day)

def comment_remover(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)

def print_markdown_node(marko_node):
    if hasattr(marko_node, 'children') and not isinstance(marko_node.children, str):
        for child in marko_node.children:
            print_markdown_node(child)
    elif hasattr(marko_node, 'children') and isinstance(marko_node.children, str):
        cog.outl(marko_node.children)

#def print_calendar():
#    import subprocess;cog.outl("")
#    result = subprocess.run("calendar -w -A14".split(), capture_output=True)
#    cog.out(result.stdout.decode());cog.outl("")

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

def print_calendar():
    cog.outl("")
    calendar_regexp = re.compile("(\d{1,2})/(\d{1,2})\s(.*)")
    events = []
    with open(os.path.join(HOME_PATH,".calendar/calendar")) as f:
        content = f.read()
        content = comment_remover(content)
        for line in content.split('\n'):
            if match := calendar_regexp.match(line):
                month, day, text = match.groups()
                events.append(DateFromCalendar(int(month), int(day), text))
                
    events = [x for x in events if x.as_date >= TODAY]
    events += list(get_due_tasks())
    events += list(get_scheduled_tasks())
    events = sorted(events, key=lambda x: x.as_date)
    for index, event in enumerate(events):
        event_date = event.as_date
        if event_date > TODAY + datetime.timedelta(days=14) and index > 7:
            break
        event_string = event_date.strftime("%a %b %d")
        if event_date == TODAY:
            cog.outl(f"**{event_string}	{event.text}**")
        else:
            cog.outl(f"{event_string}	{event.text}")

def print_active(filename):
    import marko
    md_parser = marko.Markdown()
    with open(os.path.join(WIKI_PATH, filename)) as f:
        parsed = md_parser.parse(f.read())
        seen_active = False
        for child in parsed.children:
            if isinstance(child, marko.block.Heading):
                if not seen_active and child.children[0].children.lower() == "active":
                    seen_active = True
                elif seen_active:
                    break
            elif seen_active:
                print_markdown_node(child)


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
