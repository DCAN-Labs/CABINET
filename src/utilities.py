import argparse
import os

def get_args():
    """
    :return args: Namespace object containing the command line arguments
    """
    parser = argparse.ArgumentParser("CABINET")

    # Required positional arguments
    parser.add_argument(
        "parameter_json", type=valid_readable_json,
        help=("Required. Valid path to existing readable parameter .JSON "
            "file. See README.md and example parameter .JSON files for more "
            "information on parameters.")
    )
    # Option flag arguments
    parser.add_argument(
        "--dryrun", action="store_true",
        help=("Include this flag to validate the parameter JSON without running any containers.")
    )
    args = parser.parse_args()
    return args

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
