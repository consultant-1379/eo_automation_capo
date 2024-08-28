"""
Data for Download Manager
"""
from enum import Enum

BASE_LINK = 'https://arm.seli.gic.ericsson.se/artifactory/proj-eric-oss-drop-generic-local/csars'
AAT_LINK = 'https://arm1s11-eiffel052.eiffel.gic.ericsson.se:8443/nexus/content/repositories/eo-releases/com/ericsson/oss/orchestration/eo/eric-aat-eo-test-service'


class EoPackageLinks(Enum):
    HELMFILE = (BASE_LINK + '/eric-eo-helmfile/{0}/eric-eo-helmfile-{0}.csar').format
    CM_HELMFILE = (BASE_LINK + '/eric-eo-cm-helmfile/{0}/eric-eo-cm-helmfile-{0}.csar').format
    DM_FILE = 'https://arm.seli.gic.ericsson.se/artifactory/proj-eric-oss-drop-generic-local/csars/dm/deployment-manager-{}.zip'.format
    ERIC_EO_EVNFM_VM = (BASE_LINK + '/eric-eo-evnfm-vm/{0}/eric-eo-evnfm-vm-{0}.csar').format
    ERIC_EO_EVNFM = (BASE_LINK + '/eric-eo-evnfm/{0}/eric-eo-evnfm-{0}.csar').format
    ERIC_EO_CM = (BASE_LINK + '/eric-eo-cm/{0}/eric-eo-cm-{0}.csar').format
    ERIC_EO_ACT_CNA = (BASE_LINK + '/eric-eo-act-cna/{0}/eric-eo-act-cna-{0}.csar').format
    ERIC_OSS_EO_CLM = (BASE_LINK + '/eric-oss-eo-clm/{0}/eric-oss-eo-clm-{0}.csar').format
    ERIC_EO_LIFECYCLE_MANAGER = (BASE_LINK + '/eric-eo-lifecycle-manager/{0}/eric-eo-lifecycle-manager-{0}.csar').format
    ERIC_SERVICE_EXPOSURE_FRAMEWORK = (BASE_LINK + '/eric-service-exposure-framework/{0}/eric-service-exposure-framework-{0}.csar').format


class AatPackageLinks(Enum):
    AAT = (AAT_LINK + '/{0}/eric-aat-eo-test-service-{0}.csar').format


class EoBasePackageLinks(Enum):
    ERIC_CLOUD_NATIVE_BASE = (BASE_LINK + '/eric-cloud-native-base/{0}/eric-cloud-native-base-{0}.csar').format
    ERIC_CNCS_OSS_CONFIG = (BASE_LINK + '/eric-cncs-oss-config/{0}/eric-cncs-oss-config-{0}.csar').format
    ERIC_OSS_COMMON_BASE = (BASE_LINK + '/eric-oss-common-base/{0}/eric-oss-common-base-{0}.csar').format
    ERIC_CNBASE_OSS_CONFIG = (BASE_LINK + '/eric-cnbase-oss-config/{0}/eric-cnbase-oss-config-{0}.csar').format
    ERIC_CLOUD_NATIVE_SERVICE_MESH = (BASE_LINK + '/eric-cloud-native-service-mesh/{0}/eric-cloud-native-service-mesh-{0}.csar').format
    ERIC_OSS_FUNCTION_ORCHESTRATION_COMMON = (BASE_LINK + '/eric-oss-function-orchestration-common/{0}/eric-oss-function-orchestration-common-{0}.csar').format
