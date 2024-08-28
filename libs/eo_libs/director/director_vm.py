"""
Director VM
"""
import json
import logging
from functools import cached_property
from ipaddress import ip_address

import yaml

from libs.constants import ProjectFilesLocation, DirectorFilesLocation
from libs.decorators import singleton
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.controller.controller_data import ControllerCommands
from libs.eo_libs.controller.controller_vm import ControllerVm
from libs.eo_libs.director.eo_environment_manager.environment_data import EnvironmentManagerCommands
from libs.utils.ssh_client import SSHClient

CA_CERT = '/etc/pki/trust/anchors/ca.crt'


class DirectorVM(ControllerVm):
    def __init__(self, env: EoEnv):
        super().__init__(env)
        self.director_ssh_client = SSHClient(host=self.__get_director_ip(),
                                             user_name=env.config.director_user,
                                             private_key_file=ProjectFilesLocation.ECCD_PRIVATE_KEY(env.env_name))
        self.execute_director_command = self.director_ssh_client.execute_command
        self.kube_config = f'{self.env.workdir}/config'
        self.env = env
        self.is_ipv4 = ip_address(self.env.config.load_balancer_ip).version == 4

    def prepare_kube_config(self):
        kube_config = self.director_kube_config
        api_host = self.api_host
        try:
            kube_config['clusters'][0]['cluster']['server'] = f'https://{api_host}'
            return kube_config
        except KeyError as exception:
            logging.error('Cluster has unexpected kube config format!')
            raise exception

    def setup_registry_access(self):
        cert_directory = f'/etc/docker/certs.d/{self.registry_host}'
        self.execute_command(ControllerCommands.CREATE_FOLDER(cert_directory))
        self.ssh_client.create_file_with_content(f'{cert_directory}/ca.crt', self.registry_certificate)

    @cached_property
    def director_kube_config(self):
        director_homedir = f'/home/{self.env.config.director_user}'
        kube_data = self.director_ssh_client.read_file(
            DirectorFilesLocation.KUBE_CONFIG(director_homedir)).read().decode('utf-8')
        return yaml.load(kube_data, Loader=yaml.FullLoader)

    @cached_property
    def api_host(self):
        apis = json.loads(self.execute_director_command(EnvironmentManagerCommands.GET_API_URL))
        return [api for api in apis if 'local' not in api][0]

    @cached_property
    def registry_host(self):
        return self.execute_director_command(EnvironmentManagerCommands.GET_REGISTRY_URL)

    @cached_property
    def registry_certificate(self):
        secret_cert = self.execute_director_command(EnvironmentManagerCommands.GET_REG_SECRET)
        ca_cluster_cert = self.execute_director_command(f'sudo cat {CA_CERT}')
        cert = f'{secret_cert}\n{ca_cluster_cert}' if 'BEGIN CERTIFICATE' in ca_cluster_cert else secret_cert
        return cert

    @singleton
    def __get_director_ip(self):
        is_in_config = bool(self.env.config.director_ip)
        director_ip = self.__get_director_ip_from_config() if is_in_config else self.__get_director_ip_from_the_stack()
        logging.info(f"Found director IP: '{director_ip}', will use it.")
        return director_ip

    def __get_director_ip_from_config(self):
        director_ip = self.env.config.director_ip
        if not director_ip:
            self.env.exit('No director IP found in the config file. Exiting.')
        return director_ip

    def __get_director_ip_from_the_stack(self):
        output: str = self.execute_command(ControllerCommands.GET_SERVER_LIST(self.auth))
        director_ip = None
        if vms_list := json.loads(output.replace('\'', '"')):
            for machine in vms_list:
                networks_list = machine.get('Networks')
                if 'director-0' in machine.get('Name'):
                    director_ip = \
                        networks_list.get([network for network in networks_list if 'internal' not in network][0])[0]
                    break
                if 'cp' in machine.get('Name'):
                    director_ip = networks_list.get([network for network in networks_list if
                                                     'internal' not in network and 'election' not in network][0])[0]
                    break
            return director_ip
        return self.env.exit('No director IP found!')
