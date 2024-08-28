"""
Class to initialize all environment variables
"""
import logging
import sys

from libs import get_environ, get_bool_environ
from libs.constants import EnvVariables
from libs.utils.config_manager.config_manager import ControllerConfig


class InitEnv:
    def __init__(self):
        self.install_evnfm: bool = get_bool_environ(EnvVariables.INSTALL_EVNFM)
        self.install_lm: bool = get_bool_environ(EnvVariables.INSTALL_LM)
        self.enable_vm_vnfm_ha: bool = get_bool_environ(EnvVariables.ENABLE_VM_VNFM_HA, 'true')
        self.enable_evnfm_gr: bool = get_bool_environ(EnvVariables.ENABLE_GR)
        self.install_cm: bool = get_bool_environ(EnvVariables.INSTALL_CM)
        self.install_eccd: bool = get_bool_environ(EnvVariables.INSTALL_ECCD)
        self.install_capo: bool = get_bool_environ(EnvVariables.INSTALL_CAPO)
        self.install_aat: bool = get_bool_environ(EnvVariables.INSTALL_AAT)
        self.upgrade_evnfm: bool = get_bool_environ(EnvVariables.UPGRADE_EVNFM)
        self.upgrade_cm: bool = get_bool_environ(EnvVariables.UPGRADE_CM)
        self.upgrade_eccd: bool = get_bool_environ(EnvVariables.UPGRADE_ECCD)
        self.upgrade_capo: bool = get_bool_environ(EnvVariables.UPGRADE_CAPO)
        self.execute_eccd_cleanup: bool = get_bool_environ(EnvVariables.CLEAN_ECCD)
        self.install_clm: bool = get_bool_environ(EnvVariables.INSTALL_CLM)
        self.skip_checksum: bool = get_bool_environ(EnvVariables.SKIP_CHECKSUM)
        if not any(list(self.__dict__.values())):
            self.exit('No option selected, exiting...')
        self.env_name: str = get_environ(EnvVariables.ENV).strip()
        self.controller = ControllerConfig()

    @staticmethod
    def exit(message: str):
        logging.error(message)
        sys.exit(-1)
