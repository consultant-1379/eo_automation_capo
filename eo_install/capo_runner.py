import logging

from libs.environment_init.eccd_init import EccdEnv
from libs.eo_libs.capo.capo_manager import CAPOManager


class CAPORunner:
    def __init__(self):
        self.env_var: EccdEnv = EccdEnv()
        self.capo_manager = CAPOManager(self.env_var)

    def install_capo(self):
        logging.info('Starting CAPO installation.')
        try:
            self.__common_prep_steps()
            self.capo_manager.cleanup_previous_installation()
            self.capo_manager.execute_installation_script()
        finally:
            self.__common_after_steps()

    def upgrade_capo(self):
        try:
            self.__common_prep_steps()
            self.capo_manager.execute_upgrade_script()
        finally:
            self.__common_after_steps()

    def __common_prep_steps(self):
        self.capo_manager.check_controller_free_space(self.capo_manager)
        self.capo_manager.wait_for_unlock(self.capo_manager.package_folder)
        self.capo_manager.download_package(self.capo_manager)
        self.capo_manager.prepare_capo_config()
        sw_dir = self.capo_manager.prepare_capo_package()
        self.capo_manager.sw_package_path = f'{self.capo_manager.workdir}/{sw_dir}'
        self.capo_manager.prepare_capo_images()
        self.capo_manager.prepare_flavors(self.capo_manager)

    def __common_after_steps(self):
        self.capo_manager.execute_command(f'rm -rf {self.capo_manager.workdir}')
        archive = f'{self.env_var.env_name}.tar.gz'
        self.capo_manager.execute_command(f'tar -czvf {archive} .ccdadm/{self.env_var.env_name}/')
        self.capo_manager.ssh_client.download_file_from_remote(archive, 'cluster_artifacts.tar.gz')
        self.capo_manager.execute_command(f'rm -rf {archive}')
