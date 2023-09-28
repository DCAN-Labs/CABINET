#!/usr/bin/env python3
# coding: utf-8

"""
Script for validating cabinet input parameter jsons without running the whole pipeline
"""

from src.utilities import (
    make_logger,
    get_args,
    validate_parameter_json
)

def main():
    logger = make_logger()  # Make object to log error/warning/status messages

    # Get and validate command-line arguments and parameters from .JSON file
    args = get_args()
    validate_parameter_json(args.parameter_json, logger)


if __name__ == "__main__":
    main()