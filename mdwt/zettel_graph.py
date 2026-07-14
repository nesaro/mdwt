"""Functions that generate lists and trees of nodes emulating a
dependency tree"""

from .tools import get_file_base_name

def get_file_base_name_and_prefix(full_path):
    current_file_name = os.path.basename(full_path)
    current_file_base_name, *_ = os.path.splitext(current_file_name)
    return current_file_base_name, os.path.relpath(os.path.dirname(full_path), start="/home/nesaro/wiki/")

class ZettelTree:
    def __init__(self, content, prefix=""):
        self.content = content
        self.prefix = prefix
        self.children = []

def all_substrings(string):
    from itertools import combinations
    return {string[x:y] for x, y in combinations(
            range(len(string) + 1), r = 2)}

def recursive_enumerate(node):
    for index, child in enumerate(node.children):
        yield child, [index] 
        for grandchild, grandindex in recursive_enumerate(child):
            yield grandchild, [index] + grandindex


def _generate_tree_from_root(wiki_root):
    result = {}
    abbrevations_per_file = {}
    files_per_abbreviation = defaultdict(set)
    base = ZettelTree(content="")
    if isinstance(wiki_root, str):
        wiki_root = [wiki_root]
    wiki_files = []
    for root in wiki_root:
        wiki_files += glob.glob(os.path.join(root, "**/*.md"), recursive=True)
    base_name_to_full_name = {get_file_base_name(x):x for x in wiki_files}
    wiki_files_base_name = sorted([get_file_base_name_and_prefix(x) for x in wiki_files])
    for wiki_base_name, directory in wiki_files_base_name:
        with open(base_name_to_full_name[wiki_base_name]) as f:
            if wiki_base_name not in result:
                new_entry = ZettelTree(wiki_base_name, directory)
                result[wiki_base_name] = new_entry
            found = False
            try:
                for line in f:
                    links = re.findall(r"\[\[(.*)\]\]", line)
                    for link in links:
                        if link == wiki_base_name:
                            continue
                        if link not in result:
                            result[link] = ZettelTree(link, directory)
                        if new_entry in result[link].children:
                            continue
                        result[link].children.append(new_entry)
                else:
                    base.children.append(new_entry)
            except UnicodeDecodeError:
                cog.outl(wiki_base_name)
    return base

def print_linear_index(wiki_root, only_indexes=False):
    fixed_prefix_size=0
    result = {}
    abbrevations_per_file = {}
    files_per_abbreviation = defaultdict(set)
    base = ZettelTree(content="")
    wiki_files = glob.glob(os.path.join(wiki_root, "**/*.md"), recursive=True)
    base_name_to_full_name = {get_file_base_name(x):x for x in wiki_files}
    always_first_items = ["people", "home_log", "books",
    "job_log", "adelin", "simple", "daedalus", "colonyDSL", "iwoca",
                          "102frinton", "schools", "places"]
    def order_for_linear_index(x):
        if x in always_first_items:
            return ("00000000" +
                    str(always_first_items.index(x)))[-4:]
        return x
    wiki_files_base_name = sorted([get_file_base_name(x) for x in wiki_files],
                                  key=order_for_linear_index)
    for wiki_base_name in wiki_files_base_name:
        is_zettel = re.match(r"^\d{14}", wiki_base_name)
        if is_zettel:
            rest_of_string = wiki_base_name[0:]
        else:
            rest_of_string = wiki_base_name
        if only_indexes and is_zettel:
            continue
        is_date = re.match(r"\d{4}-\d{2}-\d{2}$", wiki_base_name)
        if only_indexes and is_date:
            continue
        is_week = re.match(r"\d{4}-W\d{2}$", wiki_base_name)
        if only_indexes and is_week:
            continue
        is_year = re.match(r"\d{4}$", wiki_base_name)
        if only_indexes and is_year:
            continue
        substrings = all_substrings(rest_of_string.lower())
        substrings = {x for x in substrings if 2 < len(x) < 8
                      and "_" not in x
                      and "-" not in x}
        abbrevations_per_file[rest_of_string] = substrings
        for x in substrings:
            files_per_abbreviation[x].add(rest_of_string)
        if not only_indexes and not is_zettel:
            continue
        prefix = wiki_base_name[:fixed_prefix_size]
        if fixed_prefix_size and prefix not in result:
            fixed_fake_root = ZettelTree(prefix)
            result[prefix] = fixed_fake_root
            base.children.append(fixed_fake_root)
        elif not fixed_prefix_size:
            fixed_fake_root = base
        else:
            fixed_fake_root = result[prefix]

        
        with open(base_name_to_full_name[wiki_base_name]) as f:
            new_entry = ZettelTree(wiki_base_name)
            result[wiki_base_name] = new_entry
            found = False
            for line in f:
                links = re.findall(r"\[\[(.*)\]\]", line)
                for link in links:
                    if link in result:
                        result[link].children.append(new_entry)
                        found = True
                        break
                if found:
                    break
            else:
                fixed_fake_root.children.append(new_entry)

    indexed_results = [(node, index) for node, index in recursive_enumerate(base)]
    indexed_results = sorted(indexed_results, key=lambda x:x[1])
    for page, combined_index in indexed_results:
        if len(page.content) == fixed_prefix_size:
            continue
        zettel_index = ZettelIndex(combined_index)
        zettel_str = str(zettel_index)
        indent = " " * len(combined_index)
        abbreviations = abbrevations_per_file[page.content[0:]]
        unique_abbreviations = {x for x in abbreviations if
                                len(files_per_abbreviation[x]) == 1}
        sorted_abbreviations = sorted(unique_abbreviations, key=lambda
                                      x:(len(x),x))
        sorted_abbreviation = next((x for x in sorted_abbreviations), "")
        cog.outl(f"{indent}* [[{page.content}]]")

def max_date_per_node(node):
    from itertools import chain
    return max([node.content[:14]] + [max_date_per_node(x) for x in node.children])

def recursive_enumerate_last_touch(node):
    unsorted_first_nodes = []
    for child in node.children:
        unsorted_first_nodes.append((max_date_per_node(child), child))
    sorted_first_nodes = sorted(unsorted_first_nodes, key=lambda x:x[0])
    for index, (max_date, child) in enumerate(sorted_first_nodes):
        yield child, []
        yield from recursive_enumerate(child)


def print_zettel_index_last_update(wiki_root, number_entries):
    base = _generate_tree_from_root(wiki_root)
    indexed_results = list(recursive_enumerate_last_touch(base))
    depth_0_positions = [index for index,x in
                         enumerate(indexed_results) if not x[1]]
    try:
        actual_entry_position = depth_0_positions[-number_entries]
    except IndexError:
        actual_entry_position = -number_entries
    for node, index in indexed_results[actual_entry_position:]:
        if len(node.content) == fixed_prefix_size:
            continue
        indent = " " * len(index)
        cog.outl(f"{indent}* [[{node.content}]]")


def print_orphan_index(wiki_root):
    base = _generate_tree_from_root(wiki_root)
    indexed_results = [(node, index) for node, index in recursive_enumerate(base)]
    self_indexed_nodes = [node for node, index in
                            indexed_results if node.content in
                            ZETTEL_INDEXES]
    root_index = 0
    section_length = 20
    new_section = False
    previous_depth = 0
    for page, combined_index in indexed_results:
        node_to_print = f"[[{page.content}]] *{page.prefix}*"
        indent = "  " * (len(combined_index)-1)
        cog.outl(f"{combined_index} {indent}* {node_to_print}")


