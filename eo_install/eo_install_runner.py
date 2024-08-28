"""
Function to execute co-deploy installation
"""
import json
import logging
import os
import time
from contextlib import suppress

from libs import get_bool_environ
from libs.constants import EnvVariables
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.director.eo_download_manager.download_mgr import DownloadManager
from libs.eo_libs.director.eo_environment_manager.environment_mgr import EnvironmentManager
from libs.eo_libs.director.eo_kubernetes_manager.kuber_mgr import KubernetesManager


class EoInstall:
    def __init__(self):
        self.env: EoEnv = EoEnv()
        self.eo_download_manager = DownloadManager(self.env)
        self.eo_kuber_manager = KubernetesManager(self.env)
        self.eo_env_manager = EnvironmentManager(self.env)

    def install_eo(self):
        try:
            logging.info('Starting EO install.')
            if get_bool_environ(EnvVariables.DOWNLOAD_PACKAGES, 'True'):
                self.__before_steps()
                self.eo_download_manager.download_packages()
            self.eo_env_manager.prepare_env()
            self.eo_kuber_manager.create_kuber_assets()
            self.eo_env_manager.apply_workaround_for_internal_certs()
            self.eo_env_manager.run_installation_script()
            self.eo_env_manager.after_installation_steps()
            self.eo_env_manager.setup_ddc()
        finally:
            self.__after_steps()

    def upgrade_eo(self):
        try:
            logging.info('Starting EO upgrade.')
            self.__before_steps()
            self.eo_download_manager.download_packages()
            self.eo_env_manager.prepare_env_for_upgrade()
            if self.env.upgrade_evnfm:
                self.eo_kuber_manager.recreate_oss_secret()
            start_upgrade = time.time()
            self.eo_env_manager.run_upgrade_script()
            end_upgrade = time.time()
            if get_bool_environ(EnvVariables.ASSERT_UPGRADE_TIME):
                total_time = (end_upgrade - start_upgrade) / 60
                assert total_time <= 90, 'Upgrade did not completed within 90 minutes, but was successful.'
        finally:
            self.__after_steps()

    def __before_steps(self):
        logging.info('Cleaning workdir from orphan files...')
        self.eo_env_manager.execute_command(f'rm -rf {self.env.workdir}/*csar {self.env.workdir}/*zip {self.env.workdir}/*tar {self.env.workdir}/*tgz')
        logging.info('Cleaning done, proceeding.')
        with suppress(FileNotFoundError):
            if self.env.upgrade_evnfm or self.env.upgrade_cm:
                old_sv_file = self.eo_env_manager.execute_command(f'find {self.env.workdir}/site_values_*')
                self.eo_env_manager.ssh_client.download_file_from_remote(old_sv_file, os.path.basename(old_sv_file))

    def __after_steps(self):
        self.eo_env_manager.ssh_client.download_file_from_remote(f"{self.env.workdir}/site_values_{self.env.helmfile_version}.yaml", f'site_values_{self.env.helmfile_version}.yaml')
        if self.env.is_evnfm_related:
            self.eo_env_manager.execute_command(f'unzip -jo {self.env.workdir}/eric-eo-evnfm-*.csar Scripts/eo-evnfm/certificate_management.py -d {self.env.workdir}')
        if not self.env.enable_evnfm_gr or get_bool_environ(EnvVariables.DELETE_PACKAGES_AFTER_INSTALL, 'True'):
            self.eo_env_manager.execute_command(f'rm -rf {self.env.workdir}/*csar {self.env.workdir}/*zip {self.env.workdir}/*tar {self.env.workdir}/*tgz')
        versions = {'helmfile': self.env.helmfile_version, 'dm': self.env.dm_version}
        self.eo_env_manager.ssh_client.create_file_with_content(f'{self.env.workdir}/versions', json.dumps(versions))
        self.eo_env_manager.sync_controllers()
