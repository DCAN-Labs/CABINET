#!/usr/bin/env python3
# coding: utf-8

"""
Common source for utility functions used by CABINET :)
Barry Tikalsky: tikal004@umn.edu
"""
# Import standard libraries
import argparse
from datetime import datetime
import json
import os
import subprocess
import sys
import logging

# NOTE All functions below are in alphabetical order.

def exit_with_time_info(start_time, success):
    """
    Terminate the pipeline after displaying a message showing how long it ran
    :param start_time: datetime.datetime object of when the script started
    :param success: bool, whether all stages were successful
    """
    print("CABINET {}: {}"
          .format("took this long to run all stages successfully" if success else "ran for this long but some stages were not successful",
                  datetime.now() - start_time))
    sys.exit(0 if success else 1)

def extract_from_json(json_path):
    """
    :param json_path: String, a valid path to a real readable .json file
    :return: Dictionary, the contents of the file at json_path
    """
    with open(json_path, "r") as infile:
        return json.load(infile)

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
    args = parser.parse_args()
    return args

def get_binds(stage_args):
    '''
    :param stage_args: dict, stage run commands dictionary
    :return binds: list of formatted binds for use in subprocess.check_call
    '''
    binds = []
    to_bind = stage_args['binds']
        
    for bind in to_bind:
        binds.append("-B")
        binds.append(f"{bind['host_path']}:{bind['container_path']}")
        
    return binds

def get_mounts(stage_args):
    '''
    :param stage_args: dict, stage run commands dictionary
    :return mounts: list of formatted mounts for use in subprocess.check_call
    '''
    mounts = []
    to_mount = stage_args['mounts']

    for mount in to_mount:
        mounts.append("--mount")
        cmd = f"type=bind,src={mount['host_path']},dst={mount['container_path']}"
        mounts.append(cmd)

    return mounts

def get_optional_args_in(a_dict):
    """
    :param a_dict: Dictionary with validated parameters,
                   all of which are used by this function
    :return: List of most a_dict optional arguments and their values
    """
    optional_args = []
    for arg in a_dict.keys():
        if a_dict[arg]:
            optional_args.append(arg)
            if isinstance(a_dict[arg], list):
                for el in a_dict[arg]:
                    optional_args.append(str(el))
            elif not isinstance(a_dict[arg], bool):
                optional_args.append(str(a_dict[arg]))
    return optional_args

def log_stage_finished(stage_name, event_time, logger, success):
    """
    Print and return a string showing how much time has passed since the
    current running script reached a certain part of its process
    :param stage_name: String, name of event that just finished
    :param event_time: datetime object representing when {stage_name} started
    :param sub_ses: List with either only the subject ID str or the session too
    :return: String with an easily human-readable message showing how much time
             has passed since {stage_start} when {stage_name} started.
    """
    successful = 'finished' if success else 'failed'
    logger.info("{0} {2}. "
                "Time elapsed since {0} started: {1}"
                .format(stage_name, datetime.now() - event_time, successful))
    

def make_logger():
    """
    Make logger to log status updates, warnings, and other important info
    :return: logging.Logger able to print info to stdout and problems to stderr
    """  # TODO Incorporate pprint to make printed JSONs/dicts more readable
    fmt = "\n%(levelname)s %(asctime)s: %(message)s"
    logging.basicConfig(stream=sys.stdout, format=fmt, level=logging.INFO)  
    logging.basicConfig(stream=sys.stderr, format=fmt, level=logging.ERROR)
    logging.basicConfig(stream=sys.stderr, format=fmt, level=logging.WARNING)
    return logging.getLogger(os.path.basename(sys.argv[0]))


def run_all_stages(j_args, logger):
    """
    Run stages sequentially, starting and ending at stages specified by user
    :param all_stages: List of functions in order where each runs one stage
    :param sub_ses_IDs: List of dicts mapping "age_months", "subject",
                        "session", etc. to unique values per subject session
    :param ubiquitous_j_args: Dictionary of all args needed by each stage
    :param logger: logging.Logger object to show messages and raise warnings
    """
    # ...run all stages that the user said to run
    success = True
    for stage in j_args['cabinet']['stages']:
        stage_start = datetime.now()
        if j_args["cabinet"]["verbose"]:
            logger.info("Now running stage: {}\n"
                        .format(stage))
        stage_success = run_stage(stage, j_args, logger)
        log_stage_finished(stage, stage_start, logger, stage_success)
        if j_args['cabinet']['stop_on_stage_fail'] and not stage_success:
            return False
        success = success and stage_success
    
    return success


def run_stage(stage_name, j_args, logger):
    '''
    Gathers arguments form parameter file, constructs container run command and runs it.
    :param stage: String, name of the stage to run
    :param j_args: Dictionary, copy of j_args
    :param logger: logging.Logger object to show messages and raise warnings
    '''
    stage = j_args['stages'][stage_name]
    action = stage['action']
    flag_stage_args = get_optional_args_in(stage['flags'])
    positional_stage_args = stage['positional_args']
    container_args = get_optional_args_in(stage['container_args'])

    if j_args['cabinet']['container_type'] == 'singularity':
        binds = get_binds(stage)
        container_path = stage['container_filepath']

        cmd = ["singularity", action, *binds, *container_args, container_path, *positional_stage_args, *flag_stage_args]

    elif j_args['cabinet']['container_type'] == 'docker':
        image_name = stage['image_name']
        mounts = get_mounts(stage)

        cmd = ["docker", action, *mounts, *container_args, image_name, *positional_stage_args, *flag_stage_args]

    if j_args["cabinet"]["verbose"]:
        logger.info(f"run command for {stage_name}:\n{' '.join(cmd)}\n")

    try:
        if j_args['cabinet']['log_directory'] != "":
            job_id = j_args['cabinet']['job_id']
            out_file = os.path.join(j_args['cabinet']['log_directory'], f"{job_id}_{stage_name}.log")
            with open(out_file, "w+") as f:
                subprocess.check_call(cmd, stdout=f, stderr=f)
        else:
            subprocess.check_call(cmd)
        return True

    except Exception:
        logger.error(f"Error running {stage_name}")
        return False

def valid_readable_file(path):
    """
    Throw exception unless parameter is a valid readable filepath string. Use
    this, not argparse.FileType("r") which leaves an open file handle.
    :param path: Parameter to check if it represents a valid filepath
    :return: String representing a valid filepath
    """
    return validate(path, lambda x: os.access(x, os.R_OK),
                    os.path.abspath, "Cannot read file at '{}'")


def valid_readable_json(path):
    """
    :param path: Parameter to check if it represents a valid .json file path
    :return: String representing a valid .json file path
    """
    return validate(path, lambda _: os.path.splitext(path)[-1] == ".json",
                    valid_readable_file,
                    "'{}' is not a path to a readable .json file")

def validate(to_validate, is_real, make_valid, err_msg, prepare=None):
    """
    Parent/base function used by different type validation functions. Raises an
    argparse.ArgumentTypeError if the input object is somehow invalid.
    :param to_validate: String to check if it represents a valid object 
    :param is_real: Function which returns true iff to_validate is real
    :param make_valid: Function which returns a fully validated object
    :param err_msg: String to show to user to tell them what is invalid
    :param prepare: Function to run before validation
    :return: to_validate, but fully validated
    """
    try:
        if prepare:
            prepare(to_validate)
        assert is_real(to_validate)
        return make_valid(to_validate)
    except (OSError, TypeError, AssertionError, ValueError,
            argparse.ArgumentTypeError):
        raise argparse.ArgumentTypeError(err_msg.format(to_validate))

def validate_parameter_json(j_args, json_path, logger):
    """
    Validates the parameter JSON to ensure CABINET can run.
    :param j_args: dict, the parsed parameter JSON
    :param json_path: str, filepath of the parameter JSON
    :param logger: logging.Logger object to show messages and raise warnings
    :return: j_args, the parameter j_args dict with empty keys set to defaults
    """
    logger.info("Validating parameter JSON\n")

    is_valid = True

    # validate cabinet key
    if "cabinet" not in j_args.keys():
        logger.error("Missing key in parameter JSON: 'cabinet'")
        is_valid = False
    else:
        j_args, is_valid = validate_cabinet_options(j_args, logger)

    # if cabinet key is valid, validate stages key
    if is_valid:
        if "stages" not in j_args.keys():
            logger.error("Missing key in parameter JSON: 'stages'")
            is_valid = False
        else:
            for requested_stage in j_args["cabinet"]["stages"]:
                if requested_stage not in j_args["stages"].keys():
                    logger.error(f"Parameters for {requested_stage} not found. Please add parameters for {requested_stage} to 'stages'.")
                    is_valid = False
                else:
                    j_args, is_valid = validate_stage(j_args, logger, requested_stage)

    # if stages key is valid, validate binds/mounts
    if is_valid:
        bind_type = "binds"
        if j_args['cabinet']['container_type'] == "docker":
            bind_type = "mounts"
        for stage in j_args['cabinet']['stages']:
            is_valid = is_valid and validate_binds(stage, j_args, bind_type, logger)

    if not is_valid:
        logger.error(f"Parameter JSON {json_path} is invalid. See examples directory for examples.")
        sys.exit()
    elif j_args['cabinet']['verbose']:
        logger.info(f"Parameter JSON {json_path} is valid.\nValidated JSON: {j_args}")

    return j_args

def validate_cabinet_options(j_args, logger):
    """
    Validates the cabinet options from the param json.
    :param j_args: dict, the parsed json.
    :param logger: logging.Logger object to show messages and raise warnings
    :returns j_args: dict, the parsed json with any missing arguments set to default values
    :returns is_valid: bool, if the json is valid
    """
    is_valid = True
    options = {
        "container_type": {
            "required": True,
            "values": ["singularity", "docker"],
            "type": str
        },
        "stages": {
            "required": True,
            "type": list
        },
        "verbose": {
            "required": False,
            "default": False,
            "type": bool
        },
        "log_directory": {
            "required": False,
            "default": "",
            "type": str
        },
        "job_id": {
            "required": False,
            "default": datetime.now().timestamp(),
            "type": str
        },
        "handle_missing_host_paths": {
            "required": False,
            "default": "stop",
            "values": ["stop", "allow", "make_directories"],
            "type": str
        },
        "stop_on_stage_fail": {
            "required": False,
            "default": True,
            "type": bool
        }
    }

    for option, requirements in options.items():
        # enforce required keys
        if option not in j_args['cabinet'].keys():
            if requirements['required']:
                is_valid = False
                logger.error(f"Missing required key in cabinet options: {option}")
                continue
            # set as default if not required and not supplied
            else:
                j_args['cabinet'][option] = requirements["default"]

        # ensure types are correct and values are allowed
        else:
            arg = j_args['cabinet'][option]
            if not isinstance(arg, requirements['type']):
                is_valid = False
                logger.error(f"Invalid cabinet option: {option}. Must be of type {requirements['type']}")
            elif "values" in requirements:
                if arg not in requirements['values']:
                    is_valid = False
                    logger.error(f"Invalid cabinet option: {option}. Must be in {requirements['values']}")

    # create log directory if set and not exists
    if j_args['cabinet']['log_directory'] != "":
        os.makedirs(j_args['cabinet']['log_directory'], exist_ok=True)
    
    return j_args, is_valid

def validate_stage(j_args, logger, stage):
    """
    Validates a stage's options from the param json.
    :param j_args: dict, the parsed json.
    :param logger: logging.Logger object to show messages and raise warnings
    :returns j_args: dict, the parsed json with any missing arguments set to default values
    :returns is_valid: bool, if the json is valid
    """
    is_valid = True
    container_type = j_args['cabinet']['container_type']

    options = {
        "action": {
            "required": False,
            "type": str,
            "values": ['run', 'exec'],
            "default": 'run'
        },
        "positional_args": {
            "required": False,
            "type": list,
            "default": []
        },
        "flags": {
            "required": False,
            "type": dict,
            "default": {}
        },
        "container_args": {
            "required": False,
            "type": dict,
            "default": {}
        }
    }

    if container_type == "singularity":
        options["container_filepath"] = {
            "required": True,
            "type": str
        }
        options["binds"] = {
            "required": False,
            "type": list,
            "default": {}
        }

    elif container_type == "docker":
        options["image_name"] = {
            "required": True,
            "type": str
        }
        options["mounts"] = {
            "required": False,
            "type": list,
            "default": {}
        }

    for option, requirements in options.items():
        # enforce required keys
        if option not in j_args['stages'][stage].keys():
            if requirements['required']:
                is_valid = False
                logger.error(f"Missing required key in stage options: {stage}, {option}.")
                continue
            # set as default if not required and not supplied
            else:
                j_args['stages'][stage][option] = requirements["default"]

        # ensure types are correct and values are allowed
        else:
            arg = j_args['stages'][stage][option]
            if not isinstance(arg, requirements['type']):
                is_valid = False
                logger.error(f"Invalid stage option: {stage}, {option}. Must be of type {requirements['type']}")
            elif "values" in requirements:
                if arg not in requirements['values']:
                    is_valid = False
                    logger.error(f"Invalid stage option: {stage}, {option}. Must be in {requirements['values']}")

    if container_type == "singularity":
        if not os.path.isfile(j_args['stages'][stage]['container_filepath']):
            is_valid = False
            logger.error(f"File does not exist at {j_args['stages'][stage]['container_filepath']}")
    
    return j_args, is_valid

def validate_binds(stage, j_args, type, logger):
    """
    Validate binds or mounts for a specific stage.
    :param stage: str, name of the stage to validate
    :param j_args: dict, the parsed json.
    :param type: str, 'binds' or 'mounts'
    :param logger: logging.Logger object to show messages and raise warnings 
    :return: is_valid, bool. whether the binds for this stage are valid
    """
    is_valid = True
    
    for binds in j_args['stages'][stage][type]:
        if 'host_path' not in binds.keys() or 'container_path' not in binds.keys():
            logger.error(f"Invalid bind in {stage}. 'host_path' and 'container_path' are required for all binds.")
            is_valid = False
        if not os.path.exists(binds['host_path']):
            if j_args["cabinet"]["handle_missing_host_paths"] == 'stop':
                logger.error(f"Host filepath in stage {stage} does not exist: {binds['host_path']}")
                is_valid = False
            elif j_args["cabinet"]["handle_missing_host_paths"] == 'make_directories':
                os.makedirs(binds["host_path"])
                logger.info(f"Made directory {binds['host_path']}")

    return is_valid
