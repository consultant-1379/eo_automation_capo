from enum import StrEnum


class ControllerCommands:
    AUTH = ' --os-auth-url {} --os-username {} --os-password {} --os-default-domain-id default --os-project-name {}'.format
    GET_DATA = "openstack {} show {} -f json".format
    CREATE_IMAGE = "openstack image create --container-format bare --disk-format raw --min-disk 10 --file {} {}".format
    DELETE_ENTITY = "openstack {} delete {}".format
    CREATE_FLAVOR = 'openstack flavor create --vcpus {} --ram {} --disk {} {}'.format
    CREATE_STACK = 'openstack stack create --timeout 180 -t {} -e {} --wait {}'.format
    UPDATE_STACK = 'openstack stack update --timeout 240 -t {} -e {} --wait {}'.format
    DELETE_STACK = 'openstack stack delete --yes --wait {}'.format
    GET_STACK_STATUS = "openstack stack show {} {} | grep stack_status_reason | awk -F '|' '{{print $3}}'".format
    GET_SERVER_LIST = "openstack server list -f json {}".format
    STACK_EVENTS = 'openstack stack event list {} {}'.format
    DELETE_VOLUMES = """volumes=$(openstack volume list -f json {1} | jq '. | .[] | select(.Status=="available") | select(."{2}" | startswith("{0}"))') && openstack volume delete {1} $(echo ${{volumes}} | jq '.ID' -r)""".format
    DOWNLOAD_FILE = 'wget --inet4-only -P {} {}'.format
    CHECK_SHA1 = "sha1sum {} | awk '{{print $1}}'".format
    CHECK_SHA256 = "openssl dgst -sha256 {} | awk '{{print $2}}'".format
    CREATE_FOLDER = 'mkdir -p {}'.format
    CHECK_FOR_DM_ON_ENV = 'docker image list | grep deployment-manager | grep {}'.format


class OpenstackEntity(StrEnum):
    IMAGE = 'image'
    FLAVOR = 'flavor'
    STACK = 'stack'


class OpenStackConstants:
    NAME = 'Name'
    DISPLAY_NAME = 'Display Name'


class ControllerFilesLocation:
    EO_PACKAGES_DIR = '/eo/packages'
    DEPLOYMENT_MANAGER = '{}/deployment-manager.tar'.format
    CERT_ARCHIVE = '{}/certificates/certs.zip'.format
    EO_KUBE_CONFIG = '{}/kube_config/config'.format
    KUBE_CONFIG_DIR = '{}/kube_config'.format
    ECCD_ROOT = '/openstack/ECCD'
    ECCD_FOLDER = '/openstack/ECCD/eccd_{}'.format
    CAPO_FOLDER = '/openstack/capo/capo_{}'.format
    HOME = '/root'
