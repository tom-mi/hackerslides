import os
import shutil
import subprocess
from typing import List

from hackerslides.formatter import Command, ExecCommand, RmDirCommand, MkDirCommand


class Executor:

    def execute(self, commands: List[Command]):
        raise NotImplementedError


class DefaultExecutor(Executor):

    def execute(self, commands: List[Command]):
        for command in commands:
            if isinstance(command, ExecCommand):
                subprocess.check_output(command.command)
            elif isinstance(command, RmDirCommand):
                if os.path.exists(command.path):
                    shutil.rmtree(command.path)
            elif isinstance(command, MkDirCommand):
                os.makedirs(command.path)
            else:
                raise ValueError(f'Unknow command {commands}')
