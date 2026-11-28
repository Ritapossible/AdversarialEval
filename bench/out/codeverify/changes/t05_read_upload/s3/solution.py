import os

def read_upload(base_dir: str, name: str) -> bytes:
    file_path = os.path.join(base_dir, name)
    
    # Check if the file is outside the base directory
    if not file_path.startswith(os.path.abspath(base_dir)):
        raise ValueError("Requested file would be outside the base directory")
    
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError("The requested file does not exist")
    
    # Read and return the contents of the file
    with open(file_path, 'rb') as file:
        return file.read()
