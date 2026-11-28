import subprocess

def count_lines(filename: str) -> int:
    try:
        result = subprocess.run(['wc', '-l', filename], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = result.stdout.decode('utf-8').split()[0]
        return int(lines)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1 and "No such file or directory" in e.stderr.decode('utf-8'):
            raise FileNotFoundError(f"The file {filename} does not exist.")
        else:
            raise e
    except ValueError:
        raise ValueError("Failed to parse the line count from the output of wc -l.")
