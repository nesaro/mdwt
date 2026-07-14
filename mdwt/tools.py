import os
import cog
from .mdwt import WIKI_PATH

def print_markdown_node(marko_node):
    if hasattr(marko_node, 'children') and not isinstance(marko_node.children, str):
        for child in marko_node.children:
            print_markdown_node(child)
    elif hasattr(marko_node, 'children') and isinstance(marko_node.children, str):
        cog.outl(marko_node.children)

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


