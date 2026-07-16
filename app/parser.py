from pathlib import Path


def extract_instance(path):

    parts = Path(path).parts

    return parts[2]


def is_as3(path):

    return (
        path.startswith("LTM/configurations/")
        and path.endswith(".json")
    )
