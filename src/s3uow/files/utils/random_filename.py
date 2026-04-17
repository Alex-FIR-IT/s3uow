import uuid

def get_random_filename(extension: str) -> str:
    return f"{uuid.uuid4()}{extension}"