import logging
import os
import requests
import subprocess
import sys

from analysis import get_setting

logger = logging.getLogger('LoomDaemon')

TASK_RUNNER_EXECUTABLE = os.path.abspath(
    os.path.join(
        get_setting('BASE_DIR'),
        '../../worker/task_runner.py',
        ))


class LocalTaskManager:

    @classmethod
    def run(cls, task_run):
        from analysis.models.task_runs import LocalTaskRunExecution
        task_run_execution = LocalTaskRunExecution.create({'task_run': task_run})
        
        cmd = [
            sys.executable,
            TASK_RUNNER_EXECUTABLE,
            '--execution_id',
            task_run_execution.get_id(),
            '--master_url',
            get_setting('MASTER_URL_FOR_WORKER')
        ]
        logger.debug(cmd)
        proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT)
