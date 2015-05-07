########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import logging
import random
import shlex
import string
import subprocess
import tempfile
import sys
import os

from cloudify.exceptions import LocalCommandExecutionException
from cloudify import env


def setup_logger(logger_name,
                 logger_level=logging.INFO,
                 handlers=None,
                 remove_existing_handlers=True,
                 logger_format=None):
    """
    :param logger_name: Name of the logger.
    :param logger_level: Level for the logger (not for specific handler).
    :param handlers: An optional list of handlers (formatter will be
                     overridden); If None, only a StreamHandler for
                     sys.stdout will be used.
    :param remove_existing_handlers: Determines whether to remove existing
                                     handlers before adding new ones
    :return: A logger instance.
    :rtype: `logging.Logger`
    """

    if logger_format is None:
        logger_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    logger = logging.getLogger(logger_name)

    if remove_existing_handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    if not handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handlers = [handler]

    formatter = logging.Formatter(fmt=logger_format,
                                  datefmt='%H:%M:%S')
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logger_level)
    return logger


def get_manager_ip():
    """
    Returns the IP address of manager inside the management network.
    """
    return os.environ[env.MANAGER_IP_KEY]


def get_agent_name():

    """
    Returns the name of the agent running the operation
    """
    return os.environ[env.AGENT_NAME_KEY]


def get_manager_file_server_blueprints_root_url():
    """
    Returns the blueprints root url in the file server.
    """
    return os.environ[env.MANAGER_FILE_SERVER_BLUEPRINTS_ROOT_URL_KEY]


def get_manager_file_server_url():
    """
    Returns the manager file server base url.
    """
    return os.environ[env.MANAGER_FILE_SERVER_URL_KEY]


def get_manager_rest_service_port():
    """
    Returns the port the manager REST service is running on.
    """
    return int(os.environ[env.MANAGER_REST_PORT_KEY])


def get_agent_process_management():
    return os.environ[env.AGENT_PROCESS_MANAGEMENT_KEY]


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    Generate and return a random string using upper case letters and digits.
    """
    return ''.join(random.choice(chars) for x in range(size))


def create_temp_folder():
    """
    Create a temporary folder.
    """
    path_join = os.path.join(tempfile.gettempdir(), id_generator(5))
    os.makedirs(path_join)
    return path_join


class LocalCommandRunner(object):

    def __init__(self, logger=None):

        """
        :param logger: This logger will be used for
                       printing the output and the command.
        :rtype: cloudify.utils.LocalCommandRunner
        """

        logger = logger or setup_logger('cloudify.local')
        self.logger = logger

    def sudo(self, command,
             exit_on_failure=True,
             stdout_pipe=True,
             stderr_pipe=True,
             cwd=None,
             quiet=False):
        return self.run('sudo {0}'.format(command),
                        exit_on_failure=exit_on_failure,
                        stderr_pipe=stderr_pipe,
                        stdout_pipe=stdout_pipe,
                        cwd=cwd,
                        quiet=quiet)

    def run(self, command,
            exit_on_failure=True,
            stdout_pipe=True,
            stderr_pipe=True,
            cwd=None,
            quiet=True,
            execution_env=None):

        """
        Runs local commands.

        :param command: The command to execute.
        :param exit_on_failure: False to ignore failures.
        :param stdout_pipe: False to not pipe the standard output.
        :param stderr_pipe: False to not pipe the standard error.

        :return: A wrapper object for all valuable info from the execution.
        :rtype: CommandExecutionResponse
        """

        shlex_split = shlex.split(command)
        stdout = subprocess.PIPE if stdout_pipe else None
        stderr = subprocess.PIPE if stderr_pipe else None
        env = os.environ.copy()
        env.update(execution_env or {})
        if not quiet:
            self.logger.info('run: {0}'.format(command))

        p = subprocess.Popen(shlex_split, stdout=stdout,
                             stderr=stderr, cwd=cwd, env=env)
        out, err = p.communicate()
        if out:
            out = out.rstrip()
        if err:
            err = err.rstrip()

        if p.returncode != 0:
            error = LocalCommandExecutionException(
                command=command,
                error=err,
                output=out,
                code=p.returncode)
            if exit_on_failure:
                raise error
            else:
                self.logger.error(error)

        return LocalCommandExecutionResponse(
            command=command,
            output=out,
            code=p.returncode)


class CommandExecutionResponse(object):

    """
    Wrapper object for info returned when running commands.

    :param command: The command that was executed.
    :param output: The output from the execution.
    :param code: The return code from the execution.
    """

    def __init__(self, command, output, code):
        self.command = command
        self.output = output
        self.code = code


class LocalCommandExecutionResponse(CommandExecutionResponse):
    pass
