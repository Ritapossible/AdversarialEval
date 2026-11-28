def read_upload(base_dir: str, name: str) -> bytes:
    import os

    # Construct the full path to the file
    full_path = os.path.join(base_dir, name)

    # Check if the file is outside the base directory
    if not full_path.startswith(base_dir):
        raise ValueError("Requested file is outside the allowed directory.")

    # Check if the file exists
    if not os.path.isfile(full_path):
        raise FileNotFoundError("The requested file does not exist.")

    # Read and return the contents of the file
    with open(full_path, 'rb') as file:
        return file.read()
