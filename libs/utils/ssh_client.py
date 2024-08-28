"""
SSH client
"""

import logging
import ntpath
import os

import paramiko
from paramiko import SFTPFile

logging.getLogger('paramiko').setLevel(logging.WARNING)


class SSHClient:

    def __init__(self, **kwargs):
        """
        Init SSH Client class

        :param host: client host (or IP address)
        :param user_name: username
        :param password: password
        :param port: ssh port (by default - 22)
        :param private_key_file: path to private key file (usually stored in resources/ssh_keys)
        :param jump_data: information about jump host (if needed)
        """
        self.user_name = kwargs.get('user_name', None)
        self.password = kwargs.get('password', None)
        self.host = kwargs.get('host', None)
        self.port = kwargs.get('port', 22)
        self.private_key_file = kwargs.get('private_key_file', None)
        self.jump_channel = None
        self.client = None

    def _open_session(self):
        """
        Service method to open main SSH connection
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, port=self.port, username=self.user_name, password=self.password,
                            allow_agent=False, key_filename=self.private_key_file, look_for_keys=False,
                            sock=self.jump_channel)

    def execute_command(self, command, log_output=True, pty=False, wait_for_response=True):
        """
        Method to execute SSH command

        :param command: command to be executed
        :param log_output: print command output to console
        :param pty: request a pseudo-terminal from the server
        :param wait_for_response: wait while command to be executed
        :return: stdout of the SSH command
        """
        self._open_session()
        _, stdout, stderr = self.client.exec_command(command, get_pty=pty)
        logging.debug(f"SSH -->> [{self.user_name}@{self.host}]#{command}")
        if wait_for_response:
            output = stdout.read().decode('UTF-8').strip("\n ")
            if output == '':
                output = stderr.read().decode('UTF-8').strip("\n ")
            if log_output:
                logging.debug(f"SSH <<-- [{self.user_name}@{self.host}]#{output}")
        else:
            return None

        self.client.close()
        return output

    def download_file_from_remote(self, remote_path, local_path):
        """
        Download file from remote server to local folder.

        :param remote_path: folder on the remote host.
        :param local_path: destination folder
        """
        self._open_session()
        with self.client.open_sftp() as sftp:
            sftp.get(remote_path, local_path)

    def read_file(self, remote_filename) -> SFTPFile:
        """
        Read file on the remote server

        :param remote_filename: path to remote file
        :return: content
        """
        self._open_session()
        ftp_client = self.client.open_sftp()
        remote_file = ftp_client.open(remote_filename)
        return remote_file

    def create_file_with_content(self, file_path, content):
        """
        Create file on the remote server

        :param file_path: path to file
        :param content: content
        """
        self._open_session()
        ftp_client = self.client.open_sftp()
        remote_file = ftp_client.file(file_path, 'w', bufsize=-1)
        remote_file.write(content)
        ftp_client.close()
        self.client.close()

    def transfer_file(self, path_to_file_from, path_to_file_to, remote_flag=False, ssh_client_to=None):
        """
        Universal method for file transferring

        :param path_to_file_from: path to the file that should be moved to remote host
        :param path_to_file_to: destination for the file on remote host
        :param remote_flag: if True - file will be transferred from remote host to remote host
        :param ssh_client_to: (required if remote_flag is True) ssh_client for receiving remote host
        """
        self._open_session()
        ftp_client = self.client.open_sftp()
        if not remote_flag:
            ftp_client.put(path_to_file_from, path_to_file_to)
            ftp_client.close()
            self.client.close()
            logging.debug(
                f'File transfer was completed successful from local path "{path_to_file_from}" to "{self.host}:{path_to_file_to}"')
        if remote_flag:
            tmp_file = os.path.realpath(f'resources/{ntpath.basename(path_to_file_to)}')
            try:
                ftp_client.get(path_to_file_from, tmp_file)
                client_to = paramiko.SSHClient()
                client_to.load_system_host_keys()
                client_to.set_missing_host_key_policy(paramiko.WarningPolicy)
                client_to.connect(hostname=ssh_client_to.host,
                                  port=ssh_client_to.port,
                                  username=ssh_client_to.user_name,
                                  password=ssh_client_to.password)
                ftp_client_to = client_to.open_sftp()
                ftp_client_to.put(tmp_file, path_to_file_to)
                ftp_client.close()
                ftp_client_to.close()
                client_to.close()
            finally:
                os.remove(tmp_file)
