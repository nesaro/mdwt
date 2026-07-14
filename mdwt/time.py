import datetime
import glob
import cog
from .mdwt import WIKI_PATH

def print_links_to_day_file(day_string, prefix=""):
    import os.path
    day_without_hyphens = day_string.replace("-", "")
    list_of_paths = glob.glob(f'**/{day_without_hyphens}*.md', root_dir=WIKI_PATH, recursive=True)
    list_of_files = [os.path.basename(x) for x in list_of_paths]
    list_of_files_no_extension = sorted([os.path.splitext(x)[0] for x in list_of_files])
    for doc in list_of_files_no_extension:
        cog.outl(f"{prefix}* [[{doc}]]")
    
