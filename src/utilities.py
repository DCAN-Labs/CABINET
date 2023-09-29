import argparse
import os

def valid_readable_json(path):
    """
    :param path: Parameter to check if it represents a valid .json file path
    :return: String representing a valid .json file path
    """
    try:
        assert os.access(path, os.R_OK)
        assert os.path.splitext(path)[-1] == ".json"
        return path
    except (OSError, TypeError, AssertionError, ValueError,
            argparse.ArgumentTypeError):
        raise argparse.ArgumentTypeError(f"{path} is not a path to a readable .json file")
