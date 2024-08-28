import logging

from libs.environment_init.eccd_init import EccdEnv
from libs.eo_libs.eccd.eccd_manager import ECCDManager


class ECCDRunner:
    def __init__(self):
        self.env_var: EccdEnv = EccdEnv()
        self.eccd_manager = ECCDManager(self.env_var)

    def install(self):
        logging.info('Starting ECCD installation.')
        try:
            self.__common_prep_steps()
            self.eccd_manager.delete_previous_stack()
            self.eccd_manager.run_installation_script()
        finally:
            self.__common_after_steps()

    def upgrade(self):
        try:
            self.__common_prep_steps()
            self.eccd_manager.run_upgrade_script()
        finally:
            self.__common_after_steps()

    def __common_prep_steps(self):
        self.eccd_manager.check_controller_free_space(self.eccd_manager)
        self.eccd_manager.wait_for_unlock(self.eccd_manager.package_folder)
        self.eccd_manager.download_package(self.eccd_manager)
        self.eccd_manager.untar_package()
        self.eccd_manager.prepare_images()
        self.eccd_manager.prepare_flavors(self.eccd_manager)
        self.eccd_manager.update_env_file()

    def __common_after_steps(self):
        self.eccd_manager.ssh_client.download_file_from_remote(self.eccd_manager.env_file_path, 'env_file.yaml')
        self.eccd_manager.clean_up_working_directory()
