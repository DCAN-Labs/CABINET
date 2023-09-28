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

from src.logger import LOGGER

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

def log_stage_finished(stage_name, event_time, success):
    """
    Print and return a string showing how much time has passed since the
    current running script reached a certain part of its process
    :param stage_name: String, name of event that just finished
    :param event_time: datetime object representing when {stage_name} started
    :param success: bool, whether the stage was successful
    :return: String with an easily human-readable message showing how much time
             has passed since {stage_start} when {stage_name} started.
    """
    successful = 'finished' if success else 'failed'
    LOGGER.info("{0} {2}. "
                "Time elapsed since {0} started: {1}"
                .format(stage_name, datetime.now() - event_time, successful))

def run_all_stages(j_args):
    """
    Run stages sequentially as specified by user
    :param j_args: Dictionary of all args needed by each stage
    """
    # ...run all stages that the user said to run
    success = True
    for stage in j_args['cabinet']['stages']:
        stage_start = datetime.now()
        if j_args["cabinet"]["verbose"]:
            LOGGER.info("Now running stage: {}\n"
                        .format(stage))
        stage_success = run_stage(stage, j_args)
        log_stage_finished(stage, stage_start, stage_success)
        if j_args['cabinet']['stop_on_stage_fail'] and not stage_success:
            return False
        success = success and stage_success
    
    return success

def run_stage(stage_name, j_args):
    '''
    Gathers arguments form parameter file, constructs container run command and runs it.
    :param stage: String, name of the stage to run
    :param j_args: Dictionary, copy of j_args
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
        LOGGER.info(f"run command for {stage_name}:\n{' '.join(cmd)}\n")

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
        LOGGER.error(f"Error running {stage_name}")
        return False

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
