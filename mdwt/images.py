import cog
import subprocess

def _replace_str_index(text, position, replacement):
    replacement_len = len(replacement)
    return f'{text[:position]}{replacement}{text[position+replacement_len:]}'


def print_image(filepath, width=60, height=10, *, invert=False, annotations=()):
    """Create a image preview in text"""
    if invert:
        invert_str = "--invert "
    else:
        invert_str = ""
    str_to_run = f"chafa --passthrough none --relative off -f symbols -c none -s {width}x{height} {invert_str}--symbols all-wedge-legacy-braille"
    output_str = subprocess.run(str_to_run.split() + [filepath], capture_output=True,
                           check=True).stdout.decode()
    output_str_list = output_str.split("\n")
    for percent_x, percent_y, message in annotations:
        nearest_entry = int(abs(percent_y*height/100))
        position = int(abs(percent_x*width/100))
        output_str_list[nearest_entry] = _replace_str_index(output_str_list[nearest_entry], position, message)
        
    cog.out("\n".join(output_str_list))
    cog.outl("```")
    cog.outl(f"![actual image]({filepath})")
    cog.outl("```")

