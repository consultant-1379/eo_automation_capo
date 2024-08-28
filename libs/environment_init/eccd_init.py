"""
Class to initialize all environment variables
"""
from typing import Union

from libs import get_environ
from libs.constants import EnvVariables, ProjectFilesLocation
from libs.environment_init.env_initializer import InitEnv
from libs.utils.config_manager.config_manager import EccdConfig, CapoConfig
from libs.utils.config_manager.config_reader import ConfigReader

get_config = ConfigReader.get_config


class EccdEnv(InitEnv):
    def __init__(self):
        super().__init__()
        self.eccd_link: str = get_environ(EnvVariables.ECCD_LINK, '').strip()
        self.director_dimensions: list = get_environ(EnvVariables.DIRECTOR_DIMENSIONS, '1, 2, 4, 50').split(',')
        self.master_dimensions: list = get_environ(EnvVariables.MASTER_DIMENSIONS).split(',')
        self.worker_dimensions: list = get_environ(EnvVariables.WORKER_DIMENSIONS).split(',')
        self.stack_name: str = f'ccd-{self.env_name}'
        self.config: Union[EccdConfig | CapoConfig] = EccdConfig() if self.install_eccd or self.upgrade_eccd else CapoConfig()
        self.eccd_file = get_config(ProjectFilesLocation.ECCD_FILE) if self.install_eccd or self.upgrade_eccd else get_config(ProjectFilesLocation.CAPO_FILE)
