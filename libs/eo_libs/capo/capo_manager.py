import logging
from urllib.parse import urlparse

import yaml

from libs.eo_libs.controller.controller_data import ControllerFilesLocation
from libs.environment_init.eccd_init import EccdEnv
from libs.eo_libs.controller.controller_vm import ControllerVm


class CAPOManager(ControllerVm):
    def __init__(self, env: EccdEnv):
        self.env = env
        super().__init__(env)
        self.package_link = self.env.eccd_link
        self.capo_version, self.capo_package_name = self.__get_package_version_and_name_from_link()
        self.package_folder = ControllerFilesLocation.CAPO_FOLDER(self.capo_version)
        self.workdir = f'{self.package_folder}/capo_{self.env.env_name}'
        self.package_path = f'{self.package_folder}/{self.capo_package_name}'
        self.sw_package_path = None
        self.env_file_path = f'{self.workdir}/capo_env_{self.env.env_name}_{self.capo_version}.yaml'
        self.ephemeral_image = f'ephemeral-{self.capo_version}'
        self.node_image_name = f'node-{self.capo_version}'
        self.director_flavor_name = f'eorv_ephemeral_{self.capo_version}_{self.env.env_name}'  # ephemeral flavor here
        self.master_flavor_name = f'eorv_master_{self.capo_version}_{self.env.env_name}'
        self.worker_flavor_name = f'eorv_worker_{self.capo_version}_{self.env.env_name}'

    def __get_package_version_and_name_from_link(self) -> tuple:
        link_list = self.package_link.split('/')
        package_version = link_list[-3].strip()
        if 'swPackage' in package_version:
            package_version = link_list[-2].strip()
        package_name = link_list[-1].strip()
        return package_version, package_name

    def prepare_capo_config(self):
        logging.info('Workdir and config file preparation started...')
        self.execute_command(f'rm -rf {self.workdir}')
        self.execute_command(f'mkdir {self.workdir}')
        eccd_file, config = self.env.eccd_file, self.env.config
        eccd_file['infra']['iaas']['capo']['clouds']['cloud']['auth']['auth_url'] = config.openstack_auth_url
        eccd_file['infra']['iaas']['capo']['clouds']['cloud']['auth']['username'] = config.openstack_user
        eccd_file['infra']['iaas']['capo']['clouds']['cloud']['auth']['password'] = config.openstack_pass
        eccd_file['infra']['iaas']['capo']['clouds']['cloud']['auth']['project_id'] = config.openstack_project_id
        eccd_file['infra']['iaas']['capo']['target_cloud_cacert'] = self.__get_cloud_cert()
        eccd_file['infra']['iaas']['capo']['oam_network']['name'] = config.cp_network
        eccd_file['infra']['iaas']['capo']['oam_network']['subnets'][0] = config.cp_subnet

        eccd_file['infra']['bootstrap']['capo']['ephemeral_image']['name'] = self.ephemeral_image
        eccd_file['infra']['bootstrap']['capo']['ephemeral_flavor'] = self.director_flavor_name
        eccd_file['infra']['bootstrap']['authorized_keys'][0] = config.public_key
        eccd_file['infra']['iaas']['capo']['node_image']['name'] = self.node_image_name

        eccd_file['infra']['controlplane']['pool_cfg']['capo']['flavor'] = self.master_flavor_name
        eccd_file['infra']['controlplane']['pool_cfg']['capo']['root_volume']['size'] = int(self.env.master_dimensions[3])
        eccd_file['infra']['controlplane']['pool_cfg']['count'] = int(self.env.master_dimensions[0])
        eccd_file['infra']['controlplane']['pool_cfg']['authorized_keys'][0] = config.public_key

        eccd_file['infra']['worker_pools'][0]['pool_cfg']['capo']['flavor'] = self.worker_flavor_name
        eccd_file['infra']['worker_pools'][0]['pool_cfg']['capo']['root_volume']['size'] = int(self.env.worker_dimensions[3])
        eccd_file['infra']['worker_pools'][0]['pool_cfg']['capo']['traffic_networks'][0]['network'] = config.worker_network
        eccd_file['infra']['worker_pools'][0]['pool_cfg']['count'] = int(self.env.worker_dimensions[0])

        eccd_file['kubernetes']['apiserver_extra_sans'][0] = config.api_host

        for addon in eccd_file.get('addons'):
            match addon.get('name'):
                case 'cr-registry':
                    addon['spec']['hostname'] = config.reg_host
                    addon['spec']['storage_size'] = config.reg_size
                case 'ecfe':
                    addon['spec']['config'] = self.__get_ecfe_config()
        self.ssh_client.create_file_with_content(self.env_file_path, yaml.dump(eccd_file))
        self.execute_command(f'echo "Ready config is:" && cat {self.env_file_path}')
        logging.info('Workdir and config file prepared successfully!')

    @property
    def ccdadm_bin(self):
        return self.execute_command(f'find {self.workdir} -name ccdadm')

    def cleanup_previous_installation(self):
        logging.info('Cleanup previous CAPO instance started...')
        env_name = self.env.env_name
        result = self.execute_command(f'{self.ccdadm_bin} cluster undefine -n {env_name} && {self.ccdadm_bin} cluster define -n {env_name} -c {self.env_file_path} && {self.ccdadm_bin} context set -n {env_name} && {self.ccdadm_bin} cluster undeploy --debug')
        assert 'OpenStack resources undeployed successfully' in result, 'Errors during CAPO undeploy!'
        self.delete_volumes_connected_to_cluster('')
        logging.info('CAPO cleanup finished successfully!')

    def execute_installation_script(self):
        logging.info('CAPO installation started...')
        env_name = self.env.env_name
        result = self.execute_command(f'{self.ccdadm_bin} cluster undefine -n {env_name} && {self.ccdadm_bin} cluster define -n {env_name} -c {self.env_file_path} && {self.ccdadm_bin} context set -n {env_name} && {self.ccdadm_bin} cluster deploy -s {self.sw_package_path} --debug', pty=True)
        assert 'deployment completed' in result, 'CAPO installation failed!'
        logging.info('CAPO installation finished successfully!')

    def execute_upgrade_script(self):
        logging.info('CAPO upgrade started...')
        env_name = self.env.env_name
        result = self.execute_command(f'{self.ccdadm_bin} context set -n {env_name} && {self.ccdadm_bin} cluster upgrade all -c {self.env_file_path} -s {self.sw_package_path} --debug', pty=True)
        assert 'Cluster upgrade completed' in result, 'CAPO upgrade failed!'
        logging.info('CAPO upgrade finished successfully!')

    def prepare_capo_package(self):
        logging.info('Package preparation started...')
        unpack_result = self.execute_command(f'tar xvzf {self.package_path} -C {self.workdir}')
        logging.info('Package prepared successfully!')
        return unpack_result.split('\n')[0]

    def prepare_capo_images(self):
        logging.info('CAPO images preparation started...')
        images = [{'type': 'ephemeral', 'name': self.ephemeral_image}, {'type': 'node', 'name': self.node_image_name}]
        for image in images:
            image_type, image_name = image.get('type'), image.get('name')
            is_exist = self.check_image_already_exists(image_name)
            if not is_exist:
                image_path = self.execute_command(f'find {self.workdir} -name {image_type}*.img')
                created_image = self.create_image(image_path, image_name)
                assert image_name in created_image, "Error during image creation on Openstack!"
        logging.info('CAPO images prepared successfully!')

    def __get_ecfe_config(self):
        return """bgp-peers:
- peer-address: {peer1}
  peer-asn: {peer_asn}
  my-asn: {my_asn}
- peer-address: {peer2}
  peer-asn: {peer_asn}
  my-asn: {my_asn}
  hold-time: 3s
  my-address-pools:
  - metallb-config
address-pools:
- name: metallb-config
  protocol: bgp
  addresses:
{addresses}
""".format(peer1=self.env.config.peer_address[0],
           peer2=self.env.config.peer_address[1],
           peer_asn=self.env.config.peer_asn,
           my_asn=self.env.config.my_asn,
           addresses=''.join([f'  - {pool}\n' for pool in self.env.config.address_pools]))

    def __get_cloud_cert(self):
        return self.execute_command(f'openssl s_client -connect {urlparse(self.env.config.openstack_auth_url).hostname}:443 < /dev/null 2>/dev/null | openssl x509 -outform PEM')
