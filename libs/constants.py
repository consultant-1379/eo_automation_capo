"""
Project constants
"""
from enum import Enum, StrEnum


class EnvVariables(StrEnum):
    """
    Environment variables
    """
    ENV = 'ENV'
    NEIGHBOR_ENV = 'NEIGHBOR_ENV'
    CLUSTER_ROLE = 'CLUSTER_ROLE'
    GLOBAL_REGISTRY = 'GLOBAL_REGISTRY'
    CONTROLLER_ENV = 'CONTROLLER_ENV'
    EO_VERSION = 'EO_VERSION'
    INSTALL_EVNFM = 'INSTALL_EVNFM'
    INSTALL_LM = 'INSTALL_LM'
    ENABLE_VM_VNFM_HA = 'ENABLE_VM_VNFM_HA'
    ENABLE_GR = 'ENABLE_GR'
    UPGRADE_EVNFM = 'UPGRADE_EVNFM'
    DOWNLOAD_PACKAGES = 'DOWNLOAD_PACKAGES'
    INSTALL_CM = 'INSTALL_CM'
    UPGRADE_CM = 'UPGRADE_CM'
    INSTALL_CLM = 'INSTALL_CLM'
    HELM_TIMEOUT = 'HELM_TIMEOUT'
    ECCD_LINK = 'ECCD_LINK'
    INSTALL_ECCD = 'INSTALL_ECCD'
    UPGRADE_ECCD = 'UPGRADE_ECCD'
    INSTALL_CAPO = 'INSTALL_CAPO'
    UPGRADE_CAPO = 'UPGRADE_CAPO'
    DIRECTOR_DIMENSIONS = 'DIRECTOR_DIMENSIONS'
    MASTER_DIMENSIONS = 'MASTER_DIMENSIONS'
    WORKER_DIMENSIONS = 'WORKER_DIMENSIONS'
    INSTALL_AAT = 'INSTALL_AAT'
    CLEAN_ECCD = 'CLEAN_ECCD'
    DELETE_NODE_IMAGES = 'DELETE_NODE_IMAGES'
    ASSERT_UPGRADE_TIME = 'ASSERT_UPGRADE_TIME'
    NAMESPACE = 'NAMESPACE'
    SKIP_CHECKSUM = 'SKIP_CHECKSUM'
    DELETE_PACKAGES_AFTER_INSTALL = 'DELETE_PACKAGES_AFTER_INSTALL'


class ECCDConfig(StrEnum):
    PARAMETERS = 'parameters'
    ANSIBLE_VARIABLES = 'ansible_variables'
    OPENSTACK_AUTH_URL = 'openstack_auth_url'
    OPENSTACK_USERNAME = 'openstack_username'
    OPENSTACK_USER_PASSWORD = 'openstack_user_password'
    OPENSTACK_PROJECT_NAME = 'openstack_project_name'


class ProjectFilesLocation:
    """
    Files location in the project
    """
    ECCD_PRIVATE_KEY = 'resources/ssh_keys/{}.pem'.format
    EO_CERTIFICATES = 'resources/ssl_certificates/eo_certs/{}'.format
    CM_CERTIFICATES = 'resources/ssl_certificates/cm_certs/{}'.format
    LM_CERTIFICATES = 'resources/ssl_certificates/lm_certs/{}'.format
    EVNFM_CONFIG = 'config/evnfm/evnfm_{}.yaml'.format
    CM_CONFIG = 'config/cm/cm_{}.yaml'.format
    LM_CONFIG = 'config/lm/lm_{}.yaml'.format
    CONTROLLER = 'config/controller/controller_{}.yaml'.format
    ECCD_CONFIG = 'config/eccd/eccd_{}.yaml'.format
    CAPO_CONFIG = 'config/capo/capo_{}.yaml'.format
    ECCD_FILE = 'config/eccd/eccd_file.yaml'
    CAPO_FILE = 'config/capo/capo_file.yaml'
    EVNFM_COMMON_CONFIG = 'config/evnfm/evnfm_common_config.yaml'
    LM_COMMON_CONFIG = 'config/lm/lm_common_config.yaml'
    CM_COMMON_CONFIG = 'config/cm/cm_common_config.yaml'
    WGETRC_FILE = 'resources/.wgetrc'
    LOCKFILE_INFO = 'lockfile_info.txt'
    REG_CLEAN_SCRIPT = 'resources/support_scripts/cleanregistry.sh'


class DirectorFilesLocation:
    """
    Files location on the ECCD director VM
    """
    KUBE_CONFIG = '{}/.kube/config'.format
    TMP_INTER_CERT = '/tmp/tmp_certs/intermediate-ca.crt'


class OpenstackResponse(list, Enum):
    RESOURCE_NOT_FOUND = ['not find', 'No Image found']


class CertsIssuers(tuple, Enum):
    INTERNAL_TRUST_ISSUERS = ('EGADRootCA', )


class ClusterType(StrEnum):
    PRIMARY = 'PRIMARY'
    SECONDARY = 'SECONDARY'
