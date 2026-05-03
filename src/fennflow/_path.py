import re


class Path:
    @staticmethod
    def normalize_path(path: str) -> str:
        path = re.sub(r"/+", "/", path)
        return path.strip("/")

    @classmethod
    def join_path(cls, *paths: str) -> str:
        path = "/".join(path.strip("/") for path in paths)

        return cls.normalize_path(path)
