from datetime import datetime
import sys
import subprocess
import os

from src.logger import LOGGER
from src.valid_jargs_class import ValidJargs

class Wrapper():

    def __init__(self, Jargs: ValidJargs) -> None:
        self.start_time = datetime.now()
        self.j_args = Jargs.j_args

    def run_wrapper(self) -> None:
        LOGGER.info(f"Identified stages to be run: {self.j_args['cabinet']['stages']}")
        success = self.run_all_stages()
        self.exit_with_time_info(success)
    
    def exit_with_time_info(self, success):
        """
        Terminate the pipeline after displaying a message showing how long it ran
        :param success: bool, whether all stages were successful
        """
        print("CABINET {}: {}"
            .format("took this long to run all stages successfully" if success else "ran for this long but some stages were not successful",
                    datetime.now() - self.start_time))
        sys.exit(0 if success else 1)

    def get_binds(self, stage_args):
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

    def get_mounts(self, stage_args):
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

    def get_optional_args_in(self, a_dict):
        """
        :param a_dict: Dictionary with validated parameters,
                    all of which are used by this function
        :return: List of most a_dict optional arguments and their values
        """
        LOGGER.info("get_opt_args")
        optional_args = []
        for arg in a_dict.keys():
            if isinstance(a_dict[arg], list):
                LOGGER.info(f"list: {arg}")
                optional_args.append(arg)
                for el in a_dict[arg]:
                    optional_args.append(str(el))
            elif isinstance(a_dict[arg], bool):
                LOGGER.info(f"bool: {arg}")
                if a_dict[arg]:
                    optional_args.append(arg)
            else:
                optional_args.append(arg)
                optional_args.append(str(a_dict[arg]))
                LOGGER.info(arg)
        return optional_args

    def log_stage_finished(self, stage_name, event_time, success):
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

    def run_all_stages(self):
        """
        Run stages sequentially as specified by user
        """
        # ...run all stages that the user said to run
        success = True
        for stage in self.j_args['cabinet']['stages']:
            stage_start = datetime.now()
            if self.j_args["cabinet"]["verbose"]:
                LOGGER.info("Now running stage: {}\n"
                            .format(stage))
            stage_success = self.run_stage(stage)
            self.log_stage_finished(stage, stage_start, stage_success)
            if self.j_args['cabinet']['stop_on_stage_fail'] and not stage_success:
                return False
            success = success and stage_success
        
        return success

    def run_stage(self, stage_name):
        '''
        Gathers arguments form parameter file, constructs container run command and runs it.
        :param stage: String, name of the stage to run
        '''
        stage = self.j_args['stages'][stage_name]
        action = stage['action']
        flag_stage_args = self.get_optional_args_in(stage['flags'])
        positional_stage_args = stage['positional_args']
        container_args = self.get_optional_args_in(stage['container_args'])

        if self.j_args['cabinet']['container_type'] == 'singularity':
            binds = self.get_binds(stage)
            container_path = stage['container_filepath']

            cmd = ["singularity", action, *binds, *container_args, container_path, *positional_stage_args, *flag_stage_args]

        elif self.j_args['cabinet']['container_type'] == 'docker':
            image_name = stage['image_name']
            mounts = self.get_mounts(stage)

            cmd = ["docker", action, *mounts, *container_args, image_name, *positional_stage_args, *flag_stage_args]

        if self.j_args["cabinet"]["verbose"]:
            LOGGER.info(f"run command for {stage_name}:\n{' '.join(cmd)}\n")

        try:
            if self.j_args['cabinet']['log_directory'] != "":
                job_id = self.j_args['cabinet']['job_id']
                out_file = os.path.join(self.j_args['cabinet']['log_directory'], f"{job_id}_{stage_name}.log")
                with open(out_file, "w+") as f:
                    subprocess.check_call(cmd, stdout=f, stderr=f)
            else:
                subprocess.check_call(cmd)
            return True

        except Exception:
            LOGGER.error(f"Error running {stage_name}")
            return False

    