import os
import subprocess
from shutil import which

import jsonschema

UMOUNT_TOOLS = ['fusermount', 'fusermount3']
HTTPDIRFS_EXECUTABLES = ['httpdirfs']

httpdirfs_access_schema = {
    'type': 'object',
    'properties': {
        'url': {'type': 'string'},
        'auth': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string'},
            },
            'additionalProperties': False,
            'required': ['username', 'password']
        },
    },
    'additionalProperties': False,
    'required': ['url']
}


def _get_httpdirfs_tool():
    for executable in HTTPDIRFS_EXECUTABLES:
        if which(executable):
            return executable
    raise Exception('One of the following executables must be present in PATH: {}'.format(HTTPDIRFS_EXECUTABLES))


def _get_umount_tool():
    for executable in UMOUNT_TOOLS:
        if which(executable):
            return executable
    raise Exception('One of the following executables must be present in PATH: {}'.format(UMOUNT_TOOLS))


class HttpDirFs:
    @staticmethod
    def receive_directory(access, internal, listing):
        url = access['url']
        path = internal['path']

        mount_tool = _get_httpdirfs_tool()

        command = [mount_tool]

        # add authentication
        auth = access.get('auth')
        if auth:
            command.extend([
                '--username',
                '\'{}\''.format(auth['username']),
                '--password',
                '\'{}\''.format(auth['password']),
            ])

        command.extend([
            url,
            path
        ])

        command = ' '.join(command)

        os.mkdir(path)

        process_result = subprocess.run(command,
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.DEVNULL,
                                        shell=True)

        if process_result.returncode != 0:
            if os.path.isdir(path):
                os.rmdir(path)
            if auth:
                raise Exception('Could not mount from "{}" for user "{}" using "{}":\n{}'
                                .format(url, auth['username'], mount_tool, process_result.stderr.decode('utf-8')))
            else:
                raise Exception('Could not mount from "{}" using "{}" without authentication:\n{}'
                                .format(url, mount_tool, process_result.stderr.decode('utf-8')))

    @staticmethod
    def receive_directory_validate(access):
        try:
            jsonschema.validate(access, httpdirfs_access_schema)
        except jsonschema.ValidationError as e:
            if e.context:
                raise Exception(e.context)
            else:
                raise Exception(str(e))

        _get_httpdirfs_tool()
        _get_umount_tool()

    @staticmethod
    def receive_directory_cleanup(internal):
        umount_tool = _get_umount_tool()

        path = internal['path']

        process_result = subprocess.run([umount_tool, '-u', path], stderr=subprocess.PIPE)
        if process_result.returncode == 0:
            os.rmdir(path)
        else:
            raise Exception('Cleanup failed. Could not unmount "{}" with "{} -u":\n{}'.format(
                path, umount_tool, process_result.stderr
            ))
