from enum import StrEnum


class ControllerConfigName(StrEnum):
    """
    Controller files configuration variables
    """
    HOST = 'host'
    USER = 'user'
    PASS = 'password'


class EoSharedConfigName(StrEnum):
    IS_COLLOCATED_ENV = 'is_collocated_env'
    OPENSTACK_AUTH_URL = 'openstack_auth_url'
    OPENSTACK_USER = 'openstack_user'
    OPENSTACK_PASS = 'openstack_password'
    OPENSTACK_PROJECT_NAME = 'openstack_project_name'
    DIRECTOR_IP = 'director_ip'
    DIRECTOR_USER = 'director_user'
    REGISTRY_USER = 'container_registry_custom_user_id'
    REGISTRY_PASS = 'container_registry_custom_pw'
    BRO_SIZE = 'bro_size'
    LOAD_BALANCER_IP = 'load_balancer_ip'
    SYSLOG_IP = 'syslog_ip'
    SYSLOG_PORT = 'syslog_port'
    REGISTRY_SIZE = 'registry_size'
    SEND_SNMP_ALARM = 'send_snmp_alarm'


class LmConfigName(StrEnum):
    IAM_HOST = 'iam_hostname'
    LM_HOST = 'lm_hostname'
    GAS_HOST = 'gas_hostname'
    GIT_HOST = 'git_hostname'
    IS_COLLOCATED_ENV = 'is_collocated_env'


class EvnfmConfigName(StrEnum):
    ENMS = 'ENMs'
    IAM_HOST = 'iam_hostname'
    VNFM_HOST = 'vnfm_hostname'
    GAS_HOST = 'gas_hostname'
    DOCKER_REGISTRY_HOST = 'docker_registry_hostname'
    HELM_REGISTRY_HOST = 'helm_registry_hostname'
    ENABLE_SMALLSTACK = 'enable_smallstack'
    ENM_SCRIPTING_CLUSTER_IP = 'enm_scripting_cluster_ip'
    ENM_NOTIFICATION_IP = 'enm_notification_ip'
    ENM_USER = 'enm_username'
    ENM_PASS = 'enm_password'
    ENM_CONNECTION_TIMEOUT_IN_MILLISECONDS = 'enm_connection_timeout_in_milliseconds'
    ENM_SCRIPTING_SSH_PORT = 'enm_scripting_ssh_port'
    AAT_HOST = 'aat_hostname'
    GR_HOST = 'gr_hostname'
    CLUSTER_ROLE = 'cluster_role'
    SECONDARY_HOST = 'secondary_hostname'
    SFTP_URL = 'sftp_url'
    SFTP_NAME = 'sftp_name'
    SFTP_PASS = 'sftp_password'
    STORAGE_CLASS = 'storage_class'
    ENM_LOAD_BALANCER_IP = 'enm_load_balancer_ip'


class CmConfigName(StrEnum):
    DOMAIN_NAME = 'domain_name'
    ESA_LB = 'esa_lb'
    ACCOUNT = 'account'
    DDPID = 'ddpid'
    ENABLE = 'enabled'
    DDP_PASS = 'password'


class SharedCommonConfigName(StrEnum):
    GAS_USER = 'gas_user'
    GAS_PASS = 'gas_password'
    SYSTEM_USER = 'system_user'
    SYSTEM_PASS = 'system_password'
    CRD_NAMESPACE = 'crd_namespace'
    KC_ADMIN_ID = 'kc_admin_id'
    KC_PASS = 'kc_password'
    PG_USER_ID = 'pg_user_id'
    PG_PASS = 'pg_password'
    CUSTOM_USER_ID = 'custom_user_id'
    CUSTOM_PASS = 'custom_password'
    SUPER_USER_ID = 'super_user_id'
    SUPER_PASS = 'super_password'
    METRICS_USER_ID = 'metrics_user_id'
    METRICS_PASS = 'metrics_password'
    REPLICA_USER_ID = 'replica_user_id'
    REPLICA_PASS = 'replica_password'
    NELS_HOST_IPV4 = 'nels_host_ipv4'
    NELS_HOST_IPV6 = 'nels_host_ipv6'
    SNMP_SERVER_IP = 'snmp_server_ip'
    SNMP_COMMUNITY = 'snmp_community'


class LmCommonConfigName(StrEnum):
    LM_USER = 'lm_user'
    LM_PASS = 'lm_password'
    LM_REG_USER = 'lm_reg_user'
    LM_REG_PASS = 'lm_reg_password'


class EvnfmCommonConfigName(StrEnum):
    VNFM_USER = 'vnfm_user'
    VNFM_PASS = 'vnfm_password'
    VNFM_REG_USER = 'vnfm_reg_user'
    VNFM_REG_PASS = 'vnfm_reg_password'
    HELM_AUTH_USER = 'helm_auth_user'
    HELM_AUTH_PASS = 'helm_auth_pass'
    GR_USER = 'gr_user'
    GR_PASS = 'gr_password'


class CmCommonConfigName(StrEnum):
    EXTERNAL_TRAFFIC_POLICY = 'external_traffic_policy'
    SYSTEM_USER = 'system_user'
    SYSTEM_PASS = 'system_password'
    EO_CM_USER = 'eo_cm_user'
    EO_CM_PASS = 'eo_cm_password'
    CLUSTER_NAME = 'cluster_name'
    ERIC_EO_CM_BROKER_PASS = 'eric_eo_cm_broker_password'
    ERIC_EO_CM_DBPASS = 'eric_eo_cm_dbpassword'
    ERIC_EO_CM_SUPERPWD = 'eric_eo_cm_superpwd'
    DB_CMDB_PASS = 'db_cmdb_pass'
    DB_ECM_PASS = 'db_ecm_pass'
    DB_ACTPROVADAPTER_PASS = 'db_actprovadapter_pass'
    DB_EDA_PASS = 'db_eda_pass'
    ERIC_EO_CM_NS_LCM_DB_PASS = 'eric_eo_cm_ns_lcm_db_password'
    ERIC_EO_CM_NS_LCM_DB_SUPERPWD = 'eric_eo_cm_ns_lcm_db_superpwd'
    ERIC_EO_CM_CUST_WF_DB_PASS = 'eric_eo_cm_cust_wf_db_password'
    ERIC_EO_CM_CUST_WF_DB_SUPERPWD = 'eric_eo_cm_cust_wf_db_superpwd'
    ERIC_EO_CM_ORDER_MGMT_CA_DB_PASS = 'eric_eo_cm_order_mgmt_ca_db_password'
    ERIC_EO_CM_ORDER_MGMT_CA_DB_SUPERPWD = 'eric_eo_cm_order_mgmt_ca_db_superpwd'
    ONBOARD_PASS = 'onboard_password'
    EOADMIN_PASS = 'eoadmin_password'
    ADMIN_PASS = 'admin_password'
    ECMADMIN_PASS = 'ecmadmin_password'
    ECM_ACT_PASS = 'ecm_act_password'
    SCM_CLIENT_ID = 'scm_client_id'
    SCM_CLIENT_SECRET = 'scm_client_secret'
    TOSCAOCM_PASS = 'toscaocm_password'
    TOSCAOCM_SUPERPWD = 'toscaocm_superpwd'
    LICENCE_CONSUMER_DB_PASS = 'license_consumer_db_password'
    LICENCE_CONSUMER_DB_SUPERPWD = 'license_consumer_db_superpwd'
    CMDB_SYNC_PASS = 'cmdb_sync_pass'
    CS_AM_CONFIG_PASS = 'cs_am_config_pass'
    CS_DS_PASS = 'cs_ds_pass'
    CS_MONITOR_PASS = 'cs_monitor_pass'
    CTS_DS_PASS = 'cts_ds_pass'
    CTS_MONITOR_PASS = 'cts_monitor_pass'
    CTS_OPENAM_PASS = 'cts_openam_pass'
    ECM_ADMIN_PASS = 'ecm_admin_pass'
    US_DS_PASS = 'us_ds_pass'
    US_MONITOR_PASS = 'us_monitor_pass'
    AM_PASS = 'am_password'
    CAPI_WL_NS = 'capi_wl_namespace'


class EccdSharedConfigName(StrEnum):
    API_HOST = 'api_hostname'
    REG_HOST = 'registry_hostname'
    REGISTRY_STORAGE_SIZE = 'registry_storage_size'
    WORKER_NETWORK = 'worker_network'
    WORKER_SUBNET = 'worker_subnet'
    PEER_ADDRESS = 'peer_address'
    PEER_ASN = 'peer-asn'
    MY_ASN = 'my-asn'
    ADDRESS_POOLS = 'address-pools'
    PUBLIC_KEY = 'public_key'


class CapoConfigName(StrEnum):
    OPENSTACK_PROJECT_ID = 'openstack_project_id'
    CP_NETWORK = 'cp_network'
    CP_SUBNET = 'cp_subnet'


class EccdConfigName(StrEnum):
    DIRECTOR_NETWORK = 'director_network'
    DIRECTOR_SUBNET = 'director_subnet'
    DIRECTOR_VR_ID = 'director_virtual_router_id'
