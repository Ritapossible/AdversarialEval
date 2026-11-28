import os, subprocess
def count_lines(filename):
    out = subprocess.check_output(f"wc -l {filename}", shell=True, text=True)
    return int(out.split()[0])
