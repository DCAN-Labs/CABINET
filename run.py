#!/usr/bin/env python3
# coding: utf-8

# Import standard libraries
from datetime import datetime

# Custom local imports
from src.utilities import (
    exit_with_time_info,
    get_args,
    run_all_stages
)

from src.logger import LOGGER
from src.validate import validate_parameter_json

def main():
    start_time = datetime.now()  # Time how long the script takes

    # Get and validate command-line arguments and parameters from .JSON file
    args = get_args() 
    json_args = validate_parameter_json(args.parameter_json)
    LOGGER.info(f"Identified stages to be run: {json_args['cabinet']['stages']}")
    
    # Run every stage that the parameter file says to run
    success = run_all_stages(json_args)

    # Show user how long the pipeline took and end the pipeline here
    exit_with_time_info(start_time, success)


if __name__ == "__main__":
    main()
