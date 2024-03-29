#!/usr/bin/env python3

from contextlib import contextmanager
import argparse
import subprocess
import os
import sys
import marko
import glob
from typing import List
from dataclasses import dataclass, field
import datetime
import yaml
import random
import re



SAMPLE_LIMIT = 6000
HOME_PATH = os.environ['HOME']
WIKI_PATH = os.path.join(HOME_PATH, 'wiki/')
METADATA_FILE = os.path.join(HOME_PATH, 'wiki.metadata.yaml')
ZETTLR_LINK = re.compile(r"\[\[([A-z0-9]*)\]\]")
ZETTLR_NODE = re.compile(r"(\d{14})-.*")

@dataclass
class ZettelNode:
    path: str

    @property
    def name(self):
        return extract_name_from_markdown_path(self.path)

    @property
    def basename(self):
        return extract_name_from_markdown_path(self.path).split("/")[-1]

    @property
    def folder(self) -> str:
        return '/'.join(self.name.split('/')[:-2])


@dataclass
class ZettelNodeWithDate(ZettelNode):
    added_to_repo_on: datetime.datetime
    children: List['ZettelNode'] = field(default_factory=list)

    @classmethod
    def from_path(cls, path, *, metadata):
        return cls(path=path, added_to_repo_on=extract_datetime_from_path(path, metadata))

    @property
    def children_sorted_by_date(self):
        return sorted(self.children, key=lambda x:(x.added_to_repo_on, x.name))


def node_printer(node, level=0):
    print(" " * level + f" * [{node.name}](../{node.name}) [{node.added_to_repo_on.date()}] - [[{node.basename}]]")
    for child in node.children_sorted_by_date:
        node_printer(child, level=level+1)


def extract_name_from_markdown_path(x):
    if not x.startswith(WIKI_PATH):
        raise ValueError
    return x[len(WIKI_PATH):-len('.md')]

def generate_path_from_name(x):
    return os.path.join(WIKI_PATH, f"{x}.md")

@contextmanager
def metadata_context():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE) as f:
                metadata = yaml.safe_load(f)
        else:
            metadata = {}
        yield metadata
    finally:
        with open(METADATA_FILE, 'w') as f:
            yaml.dump(metadata, f)



def extract_datetime_from_path(x, metadata):
    if x not in metadata or not metadata[x].get('added_to_repo_on'):
        result = subprocess.run(f"git log --diff-filter=A --follow --format=%aD -1 -- ".split() + [x], capture_output=True).stdout.decode().rstrip()
        result = datetime.datetime.strptime(result, "%a, %d %b %Y %H:%M:%S %z")
        if x not in metadata:
            metadata[x] = {}
        metadata[x]['added_to_repo_on'] = result
    return metadata[x].get('added_to_repo_on')


def find_links_in_markdown_text_recursive(marko_node):
    if isinstance(marko_node, marko.inline.Link):
        yield marko_node.dest, marko_node.children[0].children
    elif hasattr(marko_node, 'children') and not isinstance(marko_node.children, str):
        for child in marko_node.children:
            yield from find_links_in_markdown_text_recursive(child)
    elif isinstance(marko_node, marko.inline.RawText):
        content = marko_node.children
        if search:= ZETTLR_LINK.search(content):
            link_content = search.group(1)
            print(link_content)

def find_links_in_file(path):
    with open(path) as f:
        md_parser = marko.Markdown()
        parsed = md_parser.parse(f.read())
        result = [x[0] for x in find_links_in_markdown_text_recursive(parsed)]
        print(result)
        return result


def to_relative_root_path(current_path, relative_path):
    current_path_list = current_path.split('/')
    while relative_path.startswith('../'):
        try:
            current_path_list.pop()
        except IndexError:
            pass
        relative_path = relative_path[len('../'):]
    if not current_path_list:
        return relative_path
    return ("/".join(current_path_list) + "/" + relative_path).lstrip("/")

def find_links_in_node(node: ZettelNode):
    path = generate_path_from_name(node.name)
    print(path)
    result = [to_relative_root_path(node.folder, x) for x in find_links_in_file(path)]
    print(node, result)
    return result
    

def discover_files_that_mention_word(word):
    import subprocess
    sp = subprocess.run(['ag', '-l', '-G', '\\\*.md', '-Q', word, WIKI_PATH], capture_output=True)
    return sp.stdout.decode().split()
    
def main():
    # create the top-level parser
    parser = argparse.ArgumentParser(prog='mdwt')
    subparsers = parser.add_subparsers(title="command", dest='command', help='sub-command help')
   
    parser_d = subparsers.add_parser('todo', aliases=['d'], help='todo')

    parser_b = subparsers.add_parser('backlinks', aliases=['b'])
    parser_b.add_argument('filename', type=str, help='File to search backlinks for')

    parser_l = subparsers.add_parser('links', aliases=['l'])
    parser_l.add_argument('filename', type=str, help='File to search links for')

    parser_l = subparsers.add_parser('link_ratio', aliases=['lr'])
    parser_l.add_argument('filename', type=str, help='File to get link ratio for')

    parser_g = subparsers.add_parser('graph', aliases=['g'])
    parser_g.add_argument('filename', type=str, help='File to generate a graph for')

    parser_z = subparsers.add_parser('zettelkasten', aliases=['z'], help='Generate Zettelkasten file based on git time')

    args = parser.parse_args()

    if args.command in ("graph", 'g'):
        if not os.path.exists(args.filename):
            print("File does not exist")
            sys.exit(1)
        MAX_DEPTH=1000
        import networkx as nx
        G = nx.DiGraph()
        already_visited =  set()
        root = extract_name_from_markdown_path(args.filename)
        nodes_to_visit = {(root, 0)}
        G.add_node(root)
        while nodes_to_visit:
            current, depth = nodes_to_visit.pop()
            print(current, nodes_to_visit)
            #if depth > MAX_DEPTH:
            #    continue
            #if current != root and current == "zettelKasten":
            #    continue
            current_node = ZettelNode(path=generate_path_from_name(current))
            try:
                destinations = find_links_in_node(current_node)
                print(destinations)
                if len(destinations) > SAMPLE_LIMIT:
                    destinations = random.sample(destinations, SAMPLE_LIMIT)
            except FileNotFoundError:
                print("Not found?", current)
                pass
            else:
                for destination in destinations:
                    if destination.startswith('http') or destination.startswith('file') or destination.startswith("~/"):
                        continue
                    if destination.endswith(".md"):
                        destination = destination[:-3]
                    if destination not in already_visited:
                        G.add_node(destination)
                        nodes_to_visit.add((destination, depth+1))
                    G.add_edge(current, destination)
            already_visited.add(current)
        nodes_that_mention = [extract_name_from_markdown_path(x) for x in discover_files_that_mention_word(root)]
        for back_mention in nodes_that_mention:
            if root != "zettelKasten" and back_mention == "zettelKasten":
                continue
            #G.add_node(back_mention)
            try:
                destinations = find_links_in_file(generate_path_from_name(back_mention))
            except Exception:
                continue
            for destination in destinations:
                if destination in set(nodes_that_mention) | {root}:
                    G.add_edge(back_mention, destination)
        import matplotlib.pyplot as plt
        pos = nx.spring_layout(G, k=1, iterations=5000)
        #pos = nx.planar_layout(G)
        nx.draw(G, pos, with_labels=True)
        plt.show()
                
    elif args.command in ("links", 'l'):
        if not os.path.exists(args.filename):
            print("File does not exist")
            sys.exit(1)
        else:
            with open(args.filename) as f:
                md_parser = marko.Markdown()
                parsed = md_parser.parse(f.read())
                print(list(find_links_in_markdown_text_recursive(parsed)))
    elif args.command in ("backlinks", "b"):
        from pathlib import Path
        basefilename = Path(args.filename).stem
        search_term = basefilename.strip()
        if result := ZETTLR_NODE.search(basefilename):
            search_term = result.group(1)
        result = subprocess.run(f"grep --include=*.md -R {search_term} {WIKI_PATH}".split(), capture_output=True)
        for line in result.stdout.decode().split("\n"):
            if line:
                print(line)
    elif args.command in ("link_ratio", 'lr'):
        if not os.path.exists(args.filename):
            print("File does not exist")
            sys.exit(1)
        else:
            with open(args.filename) as f:
                file_content = f.read()
                md_parser = marko.Markdown()
                parsed = md_parser.parse(file_content)
                number_of_links = len(list(find_links_in_markdown_text_recursive(parsed)))
                number_of_words = len(file_content.split())
                if number_of_links == 0:
                    print(number_of_words * 10, args.filename)
                else:
                    print(number_of_words // number_of_links, args.filename)
    elif args.command in ("todo", 'd'):
        file_paths = glob.glob(os.path.join(WIKI_PATH, '*.md'))
        for file_path in file_paths:
            with open(file_path) as f:
                try:
                    for line in f.readlines():
                        #print(line)
                        import re
                        current_match = re.match(r'^\d*TODO:\d*(.*)\d*', line) # TODO Add DONE
                        if current_match:
                            todo_expression = current_match.groups()[0]
                            if 'DONE' in todo_expression:
                                pass
                            else:
                                print(todo_expression.strip())

                except UnicodeDecodeError:
                    print(f"file {file_path} failed")
                    continue
    elif args.command in ("zettelkasten", 'z'):
        file_paths = glob.glob(os.path.join(WIKI_PATH, '**/*.md'), recursive=True)
        sorted_file_paths = sorted(file_paths, key=lambda x:len(x))
        nodes = {}
        root_node_names = set()
        with metadata_context() as metadata:
            for path in sorted_file_paths:
                try:
                    new_node = ZettelNodeWithDate.from_path(path, metadata=metadata)
                except ValueError:
                    print(f"failed {path}")
                    continue
                import re
                if re.match(r"\d{4}-\d{2}-\d{2}", new_node.name):
                    continue
                if re.match(r"diary\/.*", new_node.name):
                    continue
                if re.match(r"tasknotes\/.*", new_node.name):
                    continue
                if re.match(r"\d{14}.*", new_node.name):
                    continue
                try:
                    *_, last = (existing_node for x, existing_node in nodes.items() if new_node.name.startswith(x))
                except ValueError:
                    root_node_names.add(new_node.name)
                else:
                    last.children.append(new_node)
                finally:
                    nodes[new_node.name] = new_node
        root_nodes = {x:y for x,y in nodes.items() if x in root_node_names}
        sorted_nodes = sorted(root_nodes.values(), key=lambda x:(x.added_to_repo_on, x.name))
        print("""# ZettelKasten

20220729205531
generated with

`mdwt z > ~/wiki/zettelKasten.md`
                
        """)
        for node in sorted_nodes:
            node_printer(node)
        



if __name__ == "__main__":
    main()
