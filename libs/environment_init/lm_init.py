from libs import get_environ
from libs.constants import EnvVariables
from libs.environment_init.env_initializer import InitEnv
from libs.utils.config_manager.config_manager import LmConfig, LmCommonConfig


class LmEnv(InitEnv):
    def __init__(self):
        super().__init__()
        self.config: LmConfig = LmConfig()
        self.common_config: LmCommonConfig = LmCommonConfig()
        self.helmfile_version, self.dm_version = get_environ(EnvVariables.EO_VERSION, '#').strip().split('#')
        self.helm_timeout: str = get_environ(EnvVariables.HELM_TIMEOUT, '').strip()
        self.namespace: str = get_environ(EnvVariables.NAMESPACE, f'lm-{self.env_name}')
        self.workdir: str = f'/eo/workdir/workdir_lm_{self.env_name}'
