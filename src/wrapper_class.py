from datetime import datetime
from src.logger import LOGGER

class Wrapper:

    def __init__(self) -> None:
        self.start_time = datetime.now()
        #get args
        #validate json
        LOGGER.info(f"Identified stages to be run: {self.json_args['cabinet']['stages']}")

    def run_all_stages(self) -> bool:

        return success
    #exit_with_time_info
    
    