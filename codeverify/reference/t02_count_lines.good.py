import os, subprocess
def count_lines(filename):
    if not os.path.isfile(filename): raise FileNotFoundError(filename)
    out = subprocess.run(["wc", "-l", "--", filename], capture_output=True, text=True, check=True).stdout
    return int(out.split()[0])
