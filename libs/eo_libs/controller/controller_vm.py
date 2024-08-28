"""
OpenStack controller VM
"""
import ast
import logging

from libs.constants import OpenstackResponse
from libs.decorators import retry
from libs.eo_libs.controller.controller_data import ControllerCommands, OpenstackEntity, \
    OpenStackConstants
from libs.utils.ssh_client import SSHClient


class ControllerVm:
    def __init__(self, env):
        self.ssh_client = SSHClient(host=env.controller.controller_host,
                                    user_name=env.controller.controller_user,
                                    password=env.controller.controller_pass)
        self.execute_command = self.ssh_client.execute_command
        self.env = env

    @property
    def auth(self) -> str:
        return ControllerCommands.AUTH(self.env.config.openstack_auth_url,
                                       self.env.config.openstack_user,
                                       self.env.config.openstack_pass,
                                       self.env.config.openstack_project_name)

    @retry(AssertionError, tries=180, delay=30)
    def wait_for_unlock(self, package_folder):
        is_locked = ast.literal_eval(
            self.execute_command(f'test -f {package_folder}/lock && echo "True" || echo "False"'))
        assert not is_locked, logging.info('Downloading process locked, might be due to concurrent job.')

    def create_image(self, image_path, name):
        return self.execute_command(f'{ControllerCommands.CREATE_IMAGE(image_path, name)} {self.auth}')

    def delete_volumes_connected_to_cluster(self, stack_name):
        result = self.execute_command(
            f'{ControllerCommands.DELETE_VOLUMES(stack_name, self.auth, OpenStackConstants.NAME)}', pty=True)
        if 'jq: error' in result:
            result = self.execute_command(
                f'{ControllerCommands.DELETE_VOLUMES(stack_name, self.auth, OpenStackConstants.DISPLAY_NAME)}',
                pty=True)
        return result

    def download_package(self, eccd_manager):
        link, package_folder, eccd_package_path = eccd_manager.package_link, eccd_manager.package_folder, eccd_manager.package_path
        lock_file = f'{package_folder}/lock'
        try:
            logging.info('Going to download package...')
            is_package_exists = self.__check_package_already_exists(link, package_folder, eccd_package_path)
            if is_package_exists:
                logging.info('ECCD package present and checked.')
                return
            self.execute_command(f'rm -rf {package_folder} && {ControllerCommands.CREATE_FOLDER(package_folder)}')
            self.ssh_client.create_file_with_content(lock_file, '')
            self.__download_to_folder(package_folder, link)
            assert self.__check_sha256_sum(link, package_folder,
                                           eccd_package_path), 'Downloaded package has wrong sha256 checksum!'
            logging.info('Package downloaded successfully!')
        finally:
            self.execute_command(f'rm -f {lock_file}')

    def __check_package_already_exists(self, link, package_folder, eccd_package_path):
        is_file_exists_not_empty = self.execute_command(f'test -f {eccd_package_path} && echo "True" || echo "False"')
        if ast.literal_eval(is_file_exists_not_empty):
            return self.__check_sha256_sum(link, package_folder, eccd_package_path)
        return False

    def __check_sha256_sum(self, link, package_folder, eccd_package_path):
        self.execute_command(f'rm -f {eccd_package_path + ".sha256"}')
        self.__download_to_folder(package_folder, link + '.sha256')
        sha256_package = self.execute_command(ControllerCommands.CHECK_SHA256(eccd_package_path))
        sha256_from_file = self.execute_command(f'cat {eccd_package_path + ".sha256"}')
        return sha256_package == sha256_from_file

    def check_controller_free_space(self, eccd_manager):
        logging.info('Checking controller has enough memory, please wait...')
        required_space = 0
        package_size = self.execute_command(
            f"curl -sI {eccd_manager.package_link}  2>&1 | grep -i Content-Length | awk '{{print $2}}'")
        required_space += int(package_size) * 3
        self.__is_free_space_available(required_space)

    def __is_free_space_available(self, required: int):
        available = self.execute_command("df -B1 | awk '/openstack/ {{print $4}}'")
        if not available:
            available = self.execute_command("df /openstack -B1 | tail -n +2 | awk '{{print $4}}'")
        available = int(available)
        info = f'\nAvailable: {round(available / 1048576, 2)} MiB \nRequired not less: {round(required / 1048576)} MiB'
        logging.info(f'Check is over:{info}')
        assert available > required, \
            f'Free space is not enough.{info}\nPlease clean up disk space on the controller and try again!'

    def check_image_already_exists(self, name):
        image_data = self.execute_command(
            f'{ControllerCommands.GET_DATA(OpenstackEntity.IMAGE, name)} {self.auth}')
        if_image_exists = True
        if any(response for response in OpenstackResponse.RESOURCE_NOT_FOUND.value if response in image_data):
            if_image_exists = False
        return if_image_exists

    def prepare_flavors(self, eccd):
        nodes_dimensions: tuple = ({eccd.director_flavor_name: self.env.director_dimensions},
                                   {eccd.master_flavor_name: self.env.master_dimensions},
                                   {eccd.worker_flavor_name: self.env.worker_dimensions})
        [self.__prepare_single_flavor(next(iter(dimension.items()))) for dimension in nodes_dimensions]

    def __prepare_single_flavor(self, dimension: tuple):
        self.__delete_flavor_by_name(dimension[0])
        created_flavor = self.__create_flavor(dimension[0], dimension[1][1], int(dimension[1][2]) * 1024,
                                              dimension[1][3])
        assert dimension[0] in created_flavor, f'Error during flavor {dimension[0]} creation!'
        logging.info(f'Flavor {dimension[0]} created successfully!')

    def __delete_flavor_by_name(self, name):
        return self.execute_command(
            f'{ControllerCommands.DELETE_ENTITY(OpenstackEntity.FLAVOR, name)} {self.auth}')

    def __create_flavor(self, name, vcpus, ram, disk):
        host = ''
        return self.execute_command(
            f"{ControllerCommands.CREATE_FLAVOR(vcpus, ram, disk, name)} {host} {self.auth}")

    def __download_to_folder(self, folder, link):
        return self.execute_command(ControllerCommands.DOWNLOAD_FILE(folder, link), pty=True, log_output=False)
