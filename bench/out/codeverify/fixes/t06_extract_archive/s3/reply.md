1. ```requirements.txt```
```
```

2. ```python
import tarfile
from pathlib import Path

def extract_archive(tar_path: str, dest: str) -> list[str]:
    extracted_files = []
    with tarfile.open(tar_path, 'r:gz') as tar:
        for member in tar.getmembers():
            # Check if the file would be written outside of dest
            if not Path(member.name).resolve().is_relative_to(dest):
                raise ValueError("File would be written outside of destination")
            # Extract the file
            tar.extract(member, path=dest)
            extracted_files.append(member.name[len(dest):].lstrip('/'))
    return sorted(extracted_files)
```