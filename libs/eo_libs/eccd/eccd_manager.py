import logging
from urllib.parse import urlparse

import yaml

from libs.environment_init.eccd_init import EccdEnv
from libs.eo_libs.controller.controller_data import ControllerCommands, OpenstackEntity, \
    ControllerFilesLocation
from libs.eo_libs.controller.controller_vm import ControllerVm


class ECCDManager(ControllerVm):
    def __init__(self, env: EccdEnv):
        self.env = env
        super().__init__(env)
        self.package_link = self.env.eccd_link
        self.eccd_version, self.eccd_package_name = self.__get_package_version_and_name_from_link()
        self.package_folder = ControllerFilesLocation.ECCD_FOLDER(self.eccd_version)
        self.package_path = f'{self.package_folder}/{self.eccd_package_name}'
        self.workdir = f'{ControllerFilesLocation.ECCD_ROOT}/tmp_{self.env.env_name}'
        self.env_file_path = f'{self.workdir}/eccd_env_{self.env.env_name}_{self.eccd_version}.yaml'
        self.director_image_name = f'eorv_director_{self.eccd_version}'
        self.node_image_name = f'eorv_node_{self.eccd_version}'
        self.director_flavor_name = f'eorv_director_{self.eccd_version}_{self.env.env_name}'
        self.master_flavor_name = f'eorv_master_{self.eccd_version}_{self.env.env_name}'
        self.worker_flavor_name = f'eorv_worker_{self.eccd_version}_{self.env.env_name}'

    def delete_previous_stack(self) -> None:
        logging.info(f'Going to delete stack {self.env.stack_name}.')
        self.execute_command(f'{ControllerCommands.DELETE_STACK(self.env.stack_name)} {self.auth}', pty=True)
        self.delete_volumes_connected_to_cluster(self.env.stack_name)
        stack_data = self.execute_command(f'{ControllerCommands.GET_DATA(OpenstackEntity.STACK, self.env.stack_name)} {self.auth}')
        assert 'not found' in stack_data, 'Error during stack deletion!'
        logging.info(f'Stack {self.env.stack_name} deleted successfully!')

    def update_env_file(self) -> None:
        eccd_file, config = self.env.eccd_file, self.env.config
        eccd_file['parameters']['ansible_variables']['openstack_auth_url'] = config.openstack_auth_url
        eccd_file['parameters']['ansible_variables']['kube_api_ingress_host'] = config.api_host
        eccd_file['parameters']['ansible_variables']['openstack_username'] = config.openstack_user
        eccd_file['parameters']['ansible_variables']['openstack_user_password'] = config.openstack_pass
        eccd_file['parameters']['ansible_variables']['openstack_project_name'] = config.openstack_project_name
        eccd_file['parameters']['ansible_variables']['container_registry_storage_size'] = config.reg_size
        eccd_file['parameters']['ansible_variables']['container_registry_hostname'] = config.reg_host
        for peer_address in config.peer_address:
            eccd_file['parameters']['ansible_variables']['ecfe_config_map_peers'].append({'peer_address': peer_address,
                                                                                          'peer_asn': config.peer_asn})
        eccd_file['parameters']['ansible_variables']['ecfe_my_asn'] = config.my_asn
        for pool in config.address_pools:
            eccd_file['parameters']['ansible_variables']['ecfe_pool_cidrs'].append(pool)
        eccd_file['parameters']['os_endpoint_ips'].append(self.__get_os_ip())
        eccd_file['parameters']['director_external_network'] = config.director_network
        eccd_file['parameters']['director_external_subnet'] = config.director_subnet

        eccd_file['parameters']['master_image'] = self.node_image_name
        eccd_file['parameters']['master_flavor'] = self.master_flavor_name
        eccd_file['parameters']['masters_count'] = int(self.env.master_dimensions[0])
        eccd_file['parameters']['master_root_volume_size'] = int(self.env.master_dimensions[3])
        eccd_file['parameters']['master_config_volume_size'] = int(self.env.master_dimensions[4])

        eccd_file['parameters']['director_image'] = self.director_image_name
        eccd_file['parameters']['director_flavor'] = self.director_flavor_name
        eccd_file['parameters']['directors_count'] = int(self.env.director_dimensions[0])
        eccd_file['parameters']['director_root_volume_size'] = int(self.env.director_dimensions[3])
        eccd_file['parameters']['director_config_volume_size'] = int(self.env.director_dimensions[4])
        eccd_file['parameters']['director_virtual_router_id'] = self.env.config.director_vr_id

        eccd_file['parameters']['node_pools'][0]['image'] = self.node_image_name
        eccd_file['parameters']['node_pools'][0]['flavor'] = self.worker_flavor_name
        eccd_file['parameters']['node_pools'][0]['count'] = int(self.env.worker_dimensions[0])
        eccd_file['parameters']['node_pools'][0]['root_volume_size'] = int(self.env.worker_dimensions[3])
        eccd_file['parameters']['node_pools'][0]['external_networks'][0]['network'] = config.worker_network
        eccd_file['parameters']['node_pools'][0]['external_networks'][0]['subnet'] = config.worker_subnet

        eccd_file['parameters']['public_key'] = config.public_key

        self.ssh_client.create_file_with_content(self.env_file_path, yaml.dump(eccd_file, default_style='|'))

    def run_installation_script(self) -> None:
        logging.info('ECCD installation started, please be patient...')
        eccd_yaml_file_path = self.execute_command(f'find {self.workdir} -name eccd.yaml')
        install_log = self.execute_command(f'{ControllerCommands.CREATE_STACK(eccd_yaml_file_path, self.env_file_path, self.env.stack_name)} {self.auth}', pty=True)
        assert 'Stack CREATE completed successfully' in install_log, 'ECCD installation failed!'
        logging.info('ECCD installed successfully!')

    def untar_package(self) -> None:
        logging.info('Package preparation started...')
        self.execute_command(ControllerCommands.CREATE_FOLDER(self.workdir))
        self.execute_command(f'tar xvzf {self.package_path} -C {self.workdir} --strip-components=1')
        logging.info('Package prepared successfully!')

    def prepare_images(self) -> None:
        logging.info('Director image preparation started...')
        is_director_image_exists = self.check_image_already_exists(self.director_image_name)
        logging.info('Node image preparation started...')
        is_node_image_exists = self.check_image_already_exists(self.node_image_name)

        def work_with_image(image_type, image_name, package_folder):
            image_path = self.execute_command(f'find {package_folder} -name *{image_type}*.qcow2')
            self.__convert_image_to_raw_format(image_path, f'{package_folder}/{image_type}.raw')
            created_image = self.create_image(f'{package_folder}/{image_type}.raw', image_name)
            assert image_name in created_image, "Error during image creation on Openstack!"
            logging.info(f'{image_type.capitalize()} image prepared successfully!')

        if is_director_image_exists:
            logging.info('Needed director image already present on OpenStack.')
        else:
            work_with_image('director', self.director_image_name, self.workdir)

        if is_node_image_exists:
            logging.info('Needed node image already present on OpenStack.')
        else:
            work_with_image('node', self.node_image_name, self.workdir)

    def __convert_image_to_raw_format(self, image_path, destination_path) -> None:
        self.execute_command(f'qemu-img convert -f qcow2 -O raw {image_path} {destination_path}')

    def run_upgrade_script(self) -> None:
        logging.info('ECCD upgrade started, please be patient...')
        eccd_yaml_file_path = self.execute_command(f'find {self.workdir} -name eccd.yaml')
        self.execute_command(f'{ControllerCommands.UPDATE_STACK(eccd_yaml_file_path, self.env_file_path, self.env.stack_name)} {self.auth}', pty=True)
        logging.info('ECCD upgrade finished successfully!')

    def clean_up_working_directory(self) -> None:
        self.execute_command(f'rm -rf {self.workdir}')

    def __get_package_version_and_name_from_link(self) -> tuple:
        link_list = self.package_link.split('/')
        package_version = link_list[-3].strip()
        package_name = link_list[-1].strip()
        return package_version, package_name

    def __get_os_ip(self):
        return self.execute_command(f"nslookup {urlparse(self.env.config.openstack_auth_url).hostname} | awk -F': ' 'NR==6 {{ print $2 }} '")
