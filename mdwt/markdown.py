import re
import cog

ZETTLR_LINK = re.compile(r"\[\[([A-z0-9]*)\]\]")

def print_markdown_node(marko_node):
    if hasattr(marko_node, 'children') and not isinstance(marko_node.children, str):
        for child in marko_node.children:
            print_markdown_node(child)
    elif hasattr(marko_node, 'children') and isinstance(marko_node.children, str):
        cog.outl(marko_node.children)

def print_active(filename:str):
    """Print active section in a file"""
    import marko
    md_parser = marko.Markdown()
    from .mdwt import WIKI_PATH
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



def find_links_in_markdown_text_recursive(marko_node):
    import marko
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
    import marko
    with open(path) as f:
        md_parser = marko.Markdown()
        parsed = md_parser.parse(f.read())
        result = [x[0] for x in find_links_in_markdown_text_recursive(parsed)]
        print(result)
        return result


