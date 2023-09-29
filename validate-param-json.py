#!/usr/bin/env python3
# coding: utf-8

"""
Script for validating cabinet input parameter jsons without running the whole pipeline
"""
from src.utilities import get_args
from src.validate import validate_parameter_json

def main():
    # Get and validate command-line arguments and parameters from .JSON file
    args = get_args()
    validate_parameter_json(args.parameter_json)


if __name__ == "__main__":
    main()