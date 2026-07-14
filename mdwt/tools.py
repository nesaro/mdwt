import os

def get_file_base_name(full_path):
    current_file_name = os.path.basename(full_path)
    current_file_base_name, *_ = os.path.splitext(current_file_name)
    return current_file_base_name

