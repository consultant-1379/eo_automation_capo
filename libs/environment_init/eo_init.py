"""
Class to initialize all environment variables
"""
from libs import get_environ
from libs.constants import EnvVariables, ClusterType
from libs.environment_init.env_initializer import InitEnv

from libs.utils.config_manager.config_manager import CmConfig, EvnfmConfig, CmCommonConfig, EvnfmCommonConfig, LmConfig, \
    LmCommonConfig


class EoEnv(InitEnv):
    def __init__(self, is_cm=False, is_evnfm=False):
        super().__init__()
        self.is_cm_related: bool = self.install_cm or self.upgrade_cm
        self.is_evnfm_related: bool = self.install_evnfm or self.upgrade_evnfm
        self.is_lm_related: bool = self.install_lm
        self.namespace, self.config, self.common_config = self.__get_parameters(is_cm, is_evnfm)
        if self.enable_evnfm_gr:
            self.neighbor_config = EvnfmConfig(env_name=get_environ(EnvVariables.NEIGHBOR_ENV).strip())
            self.cluster_role = get_environ(EnvVariables.CLUSTER_ROLE)
            self.global_registry = get_environ(EnvVariables.GLOBAL_REGISTRY)
            self.config = self.get_gr_config()
        self.helmfile_version, self.dm_version = get_environ(EnvVariables.EO_VERSION, '#').strip().split('#')
        self.helm_timeout: str = get_environ(EnvVariables.HELM_TIMEOUT, '').strip()

        if self.install_aat:
            workdir = 'aat'
        elif self.is_lm_related:
            workdir = 'workdir_lm'
        else:
            workdir = 'workdir'
        self.workdir: str = f'/eo/workdir/{workdir}_{self.env_name}'

    def __get_parameters(self, is_cm, is_evnfm):
        if self.is_cm_related or is_cm:
            namespace = get_environ(EnvVariables.NAMESPACE, f'eric-eo-cm-{self.env_name}')
            config: CmConfig = CmConfig()
            common_config: CmCommonConfig = CmCommonConfig()
        elif self.is_evnfm_related or is_evnfm:
            namespace: str = get_environ(EnvVariables.NAMESPACE, f'evnfm-{self.env_name}')
            config: EvnfmConfig = EvnfmConfig()
            common_config: EvnfmCommonConfig = EvnfmCommonConfig()
        else:
            namespace: str = get_environ(EnvVariables.NAMESPACE, f'lm-{self.env_name}')
            config: LmConfig = LmConfig()
            common_config: LmCommonConfig = LmCommonConfig()
        return namespace, config, common_config

    def get_gr_config(self):
        match self.cluster_role:
            case ClusterType.PRIMARY:
                return self.config
            case ClusterType.SECONDARY:
                new_config: EvnfmConfig = self.neighbor_config
                params = ('iam_host', 'load_balancer_ip', 'gr_host', 'secondary_host', 'openstack_auth_url', 'openstack_user',
                          'openstack_pass', 'openstack_project_name', 'director_ip', 'registry_user', 'registry_pass')
                for param in params:
                    setattr(new_config, param, getattr(self.config, param))
                return new_config
