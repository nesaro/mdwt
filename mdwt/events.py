"""
Event functions to print and filter.
Events are stored in a directory as markdown files with
a frontmatter header
"""

import datetime
from collections import defaultdict
import glob
import os
import cog
import re
from dateutil.relativedelta import relativedelta
from .tools import get_file_base_name
from .mdwt import WIKI_PATH

EVENTS_PATH = os.path.join(WIKI_PATH, "events/")

class ZettelEvent:
    def __init__(self, name, metadata):
        self.name = name
        self.metadata = metadata

    @property
    def entry(self):
        return datetime.datetime.strptime(self.name[:14], "%Y%m%d%H%M%S")

    @property
    def start(self):
        value = self.metadata["start"]
        return self.to_datetime(value)

    @property
    def end(self):
        value = self.metadata["end"]
        return self.to_datetime(value)

    @staticmethod
    def to_datetime(value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time(0,0))
        if isinstance(value, int):
            return datetime.datetime.strptime(str(value), "%Y%m%d%H%M%S")
        if isinstance(value, str):
            if len(value) == 16:
                #20210929T181757Z
                return datetime.datetime.strptime(value, "%Y%m%dT%H%M%SZ")
            elif len(value) == 14:
                return datetime.datetime.strptime(value, "%Y%m%d%H%M%S")
        raise ValueError(value)
        
    def generate_expected_children_timestamp(self):
        recursion = self.recur_or_none
        if not recursion:
            raise Exception
        if recursion.endswith("month"):
            unit = "month"
            number = int(recursion[:-5] or 1)
        elif recursion.endswith("months"):
            unit = "month"
            number = int(recursion[:-6] or 1)
        elif recursion.endswith("monthly"):
            unit = "month"
            number = int(recursion[:-7] or 1)
        elif recursion.endswith("year"):
            unit = "year"
            number = int(recursion[:-4] or 1)
        elif recursion.endswith("years"):
            unit = "year"
            number = int(recursion[:-5] or 1)
        elif recursion.endswith("yearly"):
            unit = "year"
            number = int(recursion[:-6] or 1)
        elif recursion.endswith("week"):
            unit = "week"
            number = int(recursion[:-4] or 1) * 7
        elif recursion.endswith("weeks"):
            unit = "week"
            number = int(recursion[:-5] or 1) * 7
        elif recursion.endswith("weekly"):
            unit = "week"
            number = int(recursion[:-6] or 1) * 7
        elif recursion.endswith("days"):
            unit = "day"
            number = int(recursion[:-4] or 1)
        else:
            raise ValueError(recursion)
        now = datetime.datetime.now()
        current = self.start
        while True:
            yield current
            if current > now:
                break
            if unit == "day":
                current += datetime.timedelta(days=1)
            elif unit == "week":
                current += datetime.timedelta(days=7)
            elif unit == "month":
                current += relativedelta(months=1)
            elif unit == "year":
                current += relativedelta(months=12)
            else:
                raise ValueError

    @property
    def recur_or_none(self):
        return self.metadata.get("recur")

    @property
    def is_current(self):
        now = datetime.datetime.now()
        return self.start <= now < self.end

class EventRepository:
    def __init__(self, dict_of_events):
        self.events = dict_of_events

    @classmethod
    def from_directory(cls, root):
        result = {}
        abbrevations_per_file = {}
        files_per_abbreviation = defaultdict(set)
        wiki_files = glob.glob(os.path.join(root, "**/*.md"), recursive=True)
        base_name_to_full_name = {get_file_base_name(x):x for x in wiki_files}
        wiki_files_base_name = sorted([get_file_base_name(x) for x in wiki_files])
        for wiki_base_name in wiki_files_base_name:
            is_zettel = re.match(r"\d{14}", wiki_base_name)
            import frontmatter
            with open(base_name_to_full_name[wiki_base_name]) as f:
                content = frontmatter.load(f)
                metadata = dict(content.metadata)
                metadata["name"] = wiki_base_name
                new_entry = ZettelEvent(wiki_base_name, metadata=metadata)
                result[wiki_base_name] = new_entry
        return cls(result)

    def apply_filter(self, custom_filter):
        return self.__class__({x:y for x,y in self.events.items() if
                               custom_filter(y)})

def event_pp(repository, zettel_task):
    metadata = zettel_task.metadata
    start = zettel_task.start
    end = zettel_task.end
    short_format = "%y-%m-%d %H:%M"
    start_str = start.strftime(short_format)
    end_str = end.strftime(short_format)
    now = datetime.datetime.now()
    return f"{start_str} - {end_str}"
    if start < now < end:
        return "⏰"
    return ""

def print_events(root, custom_filter=None, printer=event_pp,
                 prefix=""):
    repository = EventRepository.from_directory(root)
    if custom_filter:
        repository = repository.apply_filter(custom_filter)
    for page, task in sorted(repository.events.items(), key=lambda x: x[1].start):
        cog.outl(f"{prefix}* {printer(repository, task) : >1} [[{page}]]")

def create_recurring_events():
    now = datetime.datetime.now()
    #now = datetime.datetime(2021,1,1)
    wiki_files = glob.glob(os.path.join(EVENTS_PATH, "**/*.md"), recursive=True)
    for wiki_file in wiki_files:
        import frontmatter
        #cog.outl("XXX")
        with open(wiki_file) as f:
            content = frontmatter.load(f)
        wiki_base_name = get_file_base_name(wiki_file)
        new_entry = ZettelEvent(wiki_base_name, metadata=content.metadata)
        if recurring := new_entry.recur_or_none:
            #cog.outl(str(wiki_base_name))
            #cog.outl(str(recurring))
            future_children_datetimes = [x for x in
                                         new_entry.generate_expected_children_timestamp()
                                         if now <= x < now + datetime.timedelta(days=366)]
            #cog.outl(str(content.metadata))
            #cog.outl(str(content))
            for future_event in future_children_datetimes:
                difference = future_event - new_entry.metadata["start"]
                timestamp = future_event.strftime("%Y%m%d%H%M%S")
                expected_new_filename = timestamp + wiki_base_name[14:]
                #cog.outl(str(timestamp))
                #cog.outl(str(expected_new_filename))
                new_path = f"{EVENTS_PATH}/{expected_new_filename}.md"
                already_exists = os.path.exists(new_path)
                if already_exists:
                    continue
                new_metadata = dict(content.metadata)
                new_metadata.pop("rtype", None)
                new_metadata.pop("urgency", None)
                new_metadata.pop("uuid", None)
                new_metadata.pop("id", None)
                new_metadata.pop("mask", None)
                new_metadata.pop("uuid", None)
                new_metadata.pop("entry", None)
                new_metadata.pop("modified", None)
                new_metadata.pop("recur", None)
                new_metadata["end"] = new_metadata["end"] + difference
                new_metadata["start"] = new_metadata["start"] + difference
                new_metadata["parent"] = wiki_base_name
                #cog.outl(str(new_metadata))
                new_content = str(content) + f"\n * parent: [[{wiki_base_name}]]"
                new_post = frontmatter.Post(new_content, **new_metadata)
                with open(new_path, "wb") as cf:
                    frontmatter.dump(new_post, cf)
                
def print_event_index():
    def custom_filter(x):
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0,
                                                microsecond=0)
        in_2_weeks = today + datetime.timedelta(days=14)
        starts_within_2_weeks = today <= x.start < in_2_weeks
        ends_within_2weeks = today <= x.end < in_2_weeks
        return x.is_current or starts_within_2_weeks or ends_within_2weeks
    return print_events(EVENTS_PATH, custom_filter=custom_filter)

def print_events_daily(date_string, *, printer=event_pp, prefix="",
                       ignore_end=False):
    date = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
    start_of_day = datetime.datetime.combine(date, datetime.time(0,0))
    start_of_next_day = start_of_day + datetime.timedelta(days=1)
    def filter_dates(x):
        if ignore_end:
            return x.start < start_of_next_day and x.start >= start_of_day
        else:
            return x.start < start_of_next_day and x.end >= start_of_day
    print_events(EVENTS_PATH,
                 filter_dates,printer=printer,prefix=prefix)
