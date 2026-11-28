import os
import tarfile

def extract_archive(tar_path: str, dest: str) -> list[str]:
    extracted_files = []
    
    with tarfile.open(tar_path, 'r:gz') as tar:
        for member in tar.getmembers():
            # Check if the file is within the destination directory
            if not member.path.startswith(os.path.normpath(dest)):
                raise ValueError("Attempted to write outside the destination directory")
            
            # Extract the file
            tar.extract(member, dest)
            
            # Add the relative path to the list
            extracted_files.append(member.path[len(dest):].lstrip('/'))
    
    # Sort the list of extracted files
    return sorted(extracted_files)
