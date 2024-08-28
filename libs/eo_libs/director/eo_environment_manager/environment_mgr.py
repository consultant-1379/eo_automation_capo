"""
Environment manager - prepare cluster for EO installation
"""
import ast
import logging
import os
import shutil
from contextlib import suppress

import yaml
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from libs.constants import ProjectFilesLocation, DirectorFilesLocation, CertsIssuers, ClusterType
from libs.decorators import retry
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.controller.controller_data import ControllerFilesLocation, ControllerCommands
from libs.eo_libs.director.director_vm import DirectorVM
from libs.eo_libs.director.eo_environment_manager.environment_data import EnvironmentManagerCommands as Command, \
    EnvironmentManagerData
from libs.eo_libs.director.eo_kubernetes_manager.kuber_data import KubernetesManagerCommands
from libs.utils.config_manager.config_manager import ControllerConfig
from libs.utils.ssh_client import SSHClient

OPTIONS = '-q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
ssh_cmd = f'ssh {OPTIONS}'
scp_cmd = f'scp {OPTIONS}'


class EnvironmentManager(DirectorVM):
    def __init__(self, env: EoEnv):
        super().__init__(env)
        self.is_ddc = False
        self.net_param = '' if self.is_ipv4 else '--net=host'
        self.nels_host = self.env.common_config.nels_host_ipv4 if self.is_ipv4 else self.env.common_config.nels_host_ipv6

    def prepare_env(self):
        """
        Main method from Environment Manager to run all functions
        """
        self.__configure_env_for_ha()
        self.execute_director_command(Command.SET_DEFAULT_NAMESPACE(self.env.namespace))
        self._add_aliases()
        self._setup_install_vm()
        self._clean_cluster()
        self._deployment_manager_configuration()
        self._transfer_certs_to_director()
        self._prepare_site_values_file()
        self._push_images()

    def prepare_env_for_upgrade(self):
        self._setup_install_vm()
        self._deployment_manager_configuration()
        self._transfer_certs_to_director()
        self._prepare_site_values_file()
        self._push_images()

    def prepare_env_for_aat(self):
        self._setup_install_vm()
        self._deployment_manager_configuration()
        self._clean_cluster(delete_crd=False)
        self._transfer_certs_to_director()
        self._transfer_site_values_for_aat()

    def _setup_install_vm(self):
        self.execute_command(ControllerCommands.CREATE_FOLDER(ControllerFilesLocation.KUBE_CONFIG_DIR(self.env.workdir)))
        self.ssh_client.create_file_with_content(self.kube_config, yaml.dump(self.prepare_kube_config()))
        self.execute_command(Command.COPY_FILE(self.kube_config,
                                               ControllerFilesLocation.EO_KUBE_CONFIG(self.env.workdir)), pty=True)
        self.execute_command(f'chmod 600 {ControllerFilesLocation.EO_KUBE_CONFIG(self.env.workdir)}')
        self.setup_registry_access()

    def sync_controllers(self):
        controllers_list = ['eo_node_ie', 'eo_node_se']
        controllers_list.remove(self.env.controller.controller_name)
        second_controller_config: ControllerConfig = ControllerConfig(controllers_list[0])
        second_ssh_client = SSHClient(host=second_controller_config.controller_host,
                                      user_name=second_controller_config.controller_user,
                                      password=second_controller_config.controller_pass)
        files_to_transfer = ['/kube_config/config', '/config', f'/site_values_{self.env.helmfile_version}.yaml', '/versions']
        second_ssh_client.execute_command(f'mkdir -p {self.env.workdir}')
        second_ssh_client.execute_command(f'rm -rf {self.env.workdir}/site_values_*')
        for file in files_to_transfer:
            path = f'{self.env.workdir}{file}'
            with suppress(FileNotFoundError):
                self.ssh_client.transfer_file(path, path, True, second_ssh_client)

        if self.env.controller.controller_name != 'eo_node_ie':
            check_for_dm_result = second_ssh_client.execute_command(ControllerCommands.CHECK_FOR_DM_ON_ENV(
                self.env.dm_version))
            if not check_for_dm_result:
                second_ssh_client.execute_command(
                    Command.DELETE_FILE(ControllerFilesLocation.DEPLOYMENT_MANAGER(self.env.workdir)), pty=True)
                extract_deployment_manager = second_ssh_client.execute_command(
                    Command.EXTRACT_DEPLOYMENT_MANAGER(self.env.workdir, self.env.dm_version), pty=True)
                assert f'inflating: {self.env.workdir}/deployment-manager.tar' in extract_deployment_manager, \
                    'Error during extracting deployment manager on a second EO node!'
                load_deployment_manager = second_ssh_client.execute_command(Command.LOAD_DEPLOYMENT_MANAGER(
                    self.env.workdir), pty=True, log_output=True)
                assert f'Loaded image: deployment-manager:{self.env.dm_version}' in load_deployment_manager, \
                    'Error during loading deployment manager images on a second EO node!'

    def setup_ddc(self):
        if self.is_ddc:
            logging.info('DDC configuration started...')
            pod_name = self.execute_command(
                f"kubectl get po -n {self.env.namespace} --kubeconfig {self.kube_config} | grep eric-oss-ddc | awk '{{ print $1 }}'")
            self.execute_command(
                f"kubectl -n {self.env.namespace} --kubeconfig {self.kube_config} exec -it {pod_name} -- bash -c '/opt/ericsson/ERICddc/bin/ddc DIRECT TRIGGER'",
                pty=True)
            self.execute_command(
                f"kubectl -n {self.env.namespace} --kubeconfig {self.kube_config} exec -it {pod_name} -- bash -c '/opt/ericsson/ERICddc/bin/ddc DIRECT MAKETAR'",
                pty=True)
            logging.info('DDC configure successfully.')

    def run_installation_script(self):
        """
        Execute EO installation script
        """
        logging.info('EO installation started, please be patient...')
        install_eo = self.execute_command(
            Command.EXECUTE_INSTALL(self.net_param, self.env.workdir, self.env.dm_version, self.env.namespace,
                                    self.env.helm_timeout, self.env.common_config.crd_namespace), pty=True)
        assert 'EO install completed successfully' in install_eo or 'Install completed successfully' in install_eo, 'Error during EO installation!'
        logging.info('EO install finished successfully!')
        self.__check_all_pods_running(self.env.namespace)

    @retry(AssertionError, tries=25, delay=20)
    def __check_all_pods_running(self, namespace):
        logging.info(f'Checking all pods are up and running in the namespace {namespace}...')
        not_running_pods = self.execute_command(
            KubernetesManagerCommands.GET_NOT_RUNNING_PODS(namespace, self.kube_config))
        assert not not_running_pods, f'Not all pods are up and running, check your environment:\n{not_running_pods}'
        logging.info('All pods are up and running!')

    def run_upgrade_script(self):
        logging.info('Upgrade started, please be patient...')
        upgrade_eo = self.execute_command(
            Command.EXECUTE_UPGRADE(self.net_param, self.env.workdir, self.env.dm_version, self.env.namespace,
                                    self.env.helm_timeout, self.env.common_config.crd_namespace), pty=True)
        assert 'Upgrade completed successfully' in upgrade_eo, 'Error during upgrade!'
        logging.info('Upgrade finished successfully!')
        self.__check_all_pods_running(self.env.namespace)

    def apply_workaround_for_internal_certs(self):
        if self.env.install_evnfm:
            self._apply_workaround_for_cvnfm()

    def after_installation_steps(self):
        if not self.env.enable_evnfm_gr:
            self.execute_command(f'rm -rf {self.env.workdir}/logs')
        if self.env.install_evnfm:
            if self.env.enable_vm_vnfm_ha:
                pods = ['eric-vnflcm-service-ha-0', 'eric-vnflcm-service-ha-1']
                for pod in pods:
                    self.execute_director_command(Command.OPENLOG_VMVNFM_ALIAS(pod, self.env.namespace), pty=True)
                    self.execute_director_command(Command.READLOG_VMVNFM_ALIAS(pod, self.env.namespace), pty=True)
            else:
                pod = 'eric-vnflcm-service-0'
                self.execute_director_command(Command.OPENLOG_VMVNFM_ALIAS(pod, self.env.namespace), pty=True)
                self.execute_director_command(Command.READLOG_VMVNFM_ALIAS(pod, self.env.namespace), pty=True)

    def _apply_workaround_for_cvnfm(self):
        with open(f'{ProjectFilesLocation.EO_CERTIFICATES(self.env.env_name)}/intermediate-ca.crt', 'rb') as cert:
            data = cert.read()
            cert = x509.load_pem_x509_certificate(data, default_backend())
            cert_issuer = cert.issuer.rfc4514_string()
            if any(issuer for issuer in CertsIssuers.INTERNAL_TRUST_ISSUERS.value if issuer in cert_issuer):
                logging.info('You are using internal trust certificates, will apply workaround for CVNFM')
                worker_ips = self.execute_director_command(
                    KubernetesManagerCommands.GET_WORKERS_IPS('worker')).split()
                self.execute_director_command(ControllerCommands.CREATE_FOLDER(os.path.dirname(DirectorFilesLocation.TMP_INTER_CERT)))
                self.director_ssh_client.transfer_file(
                    f'{ProjectFilesLocation.EO_CERTIFICATES(self.env.env_name)}/intermediate-ca.crt',
                    DirectorFilesLocation.TMP_INTER_CERT)
                eccd_version = self.director_ssh_client.execute_command(KubernetesManagerCommands.GET_ECCD_VERSION)
                if eccd_version >= '2.18':
                    logging.info('Detected ECCD version 2.18 or later, will apply workaround for containerd')
                    self._containerd_workaround(worker_ips)
                else:
                    logging.info('Detected ECCD version less than 2.18, will apply workaround for docker and helm')
                    self._docker_workaround(worker_ips)
                    self._helm_workaround()
            else:
                logging.info('You are using external trust certificates, no worries :)')

    def _containerd_workaround(self, worker_ips):
        cert_dir = "/etc/pki/trust/anchors"
        for worker_ip in worker_ips:
            self.execute_director_command(
                f'{scp_cmd} {DirectorFilesLocation.TMP_INTER_CERT} {worker_ip}:/tmp/inter.crt')
            self.execute_director_command(
                f'{ssh_cmd} {worker_ip} sudo cp /tmp/inter.crt {cert_dir}/inter.crt')
            self.execute_director_command(f'{ssh_cmd} {worker_ip} sudo update-ca-certificates')
            self.execute_director_command(f'{ssh_cmd} {worker_ip} sudo systemctl restart containerd')

        logging.info('Wait for pods to restart after workaround was applied...')
        self.__check_all_pods_running('kube-system')

    def _docker_workaround(self, worker_ips):
        logging.info('Starting Docker registry workaround applying')
        reg_dir = f'/etc/docker/certs.d/{self.env.config.docker_registry_host}'
        for worker_ip in worker_ips:
            self.execute_command(f'{ssh_cmd} {worker_ip} sudo {ControllerCommands.CREATE_FOLDER(reg_dir)}')
            self.execute_command(f'{scp_cmd} {DirectorFilesLocation.TMP_INTER_CERT} {worker_ip}:/tmp/inter.crt')
            self.execute_command(f'{ssh_cmd} {worker_ip} sudo cp /tmp/inter.crt {reg_dir}/inter.crt')
            self.execute_command(f'{scp_cmd} {DirectorFilesLocation.TMP_INTER_CERT} {worker_ip}:/tmp/ca.crt')
            self.execute_command(f'{ssh_cmd} {worker_ip} sudo cp /tmp/ca.crt {reg_dir}/ca.crt')

    def _helm_workaround(self):
        logging.info('Starting HELM workaround applying.')
        bundle_to_update = '/etc/ssl/ca-bundle.pem'
        wfs_pod = self.execute_director_command(
            f"kubectl get po -n {self.env.namespace} | grep eric-am-common-wfs | grep -v ui | awk '{{print $1}}' ")
        self.execute_director_command(
            f'kubectl cp {DirectorFilesLocation.TMP_INTER_CERT} {self.env.namespace}/{wfs_pod}:/tmp/intermediate-ca.crt')
        self.execute_director_command(
            f"kubectl exec -n {self.env.namespace} {wfs_pod} -- bash -c 'cat /tmp/intermediate-ca.crt >> {bundle_to_update}'")

    def _add_aliases(self):
        check_aliases_in_bashrc = self.execute_director_command(Command.GET_CODEPLOY_ALIASES)
        if not check_aliases_in_bashrc:
            if self.env.enable_vm_vnfm_ha:
                self.execute_director_command(
                    f'{Command.ADD_ALIASES_TO_BASHRC} "{EnvironmentManagerData.ALIASES(self.env.namespace, "eric-vnflcm-service-ha-0")}"')
            else:
                self.execute_director_command(
                    f'{Command.ADD_ALIASES_TO_BASHRC} "{EnvironmentManagerData.ALIASES(self.env.namespace, "eric-vnflcm-service-0")}"')

    def _clean_cluster(self, delete_crd=True):
        """
        Method to clean up kubernetes cluster from previous deployment
        """
        logging.info('Cluster cleanup started...')
        if self.env.install_lm:
            self.execute_command(f'flux uninstall -n {self.env.namespace} --kubeconfig={self.kube_config} -s')
        self.__delete_namespace(self.env.namespace)
        if self.env.is_cm_related:
            self.__delete_namespace(self.env.common_config.capi_wl_ns)
        if self.env.install_cm or self.env.install_evnfm or self.env.install_lm:
            self.__delete_clusterroles(self.env.namespace)
            self.__delete_clusterrolebindings(self.env.namespace)
        if delete_crd and not self.env.config.is_collocated_env:
            self.__delete_namespace(self.env.common_config.crd_namespace)
            self.__delete_crd()
        logging.info('Cluster cleanup finished.')

    def _deployment_manager_configuration(self):
        """
        Method for preparing EO deployment manager or add it to 'eo_node_ie' if needed
        :return:
        """
        logging.info('Deployment manager preparation started...')
        self.execute_command(
            Command.DELETE_FILE(ControllerFilesLocation.DEPLOYMENT_MANAGER(self.env.workdir)), pty=True)
        extract_deployment_manager = self.execute_command(
            Command.EXTRACT_DEPLOYMENT_MANAGER(self.env.workdir, self.env.dm_version), pty=True)
        assert f'inflating: {self.env.workdir}/deployment-manager.tar' in extract_deployment_manager, \
            'Error during extracting deployment manager!'
        load_deployment_manager = self.execute_command(Command.LOAD_DEPLOYMENT_MANAGER(self.env.workdir),
                                                       pty=True, log_output=True)
        assert f'Loaded image: deployment-manager:{self.env.dm_version}' in load_deployment_manager, \
            'Error during loading deployment manager images!'
        initialize_workdir = self.execute_command(
            Command.INITIALIZE_WORKDIR(self.env.workdir, self.env.dm_version), pty=True)
        assert 'init completed successfully' in initialize_workdir, 'Error during workdir initializing!'
        logging.info('Deployment manager preparation finished successfully.')

    def _transfer_certs_to_director(self):
        """
        Method for transferring files from local repo to the director
        """
        logging.info('Certificates are transferring to the director node...')
        if self.env.is_cm_related:
            path_to_cert = ProjectFilesLocation.CM_CERTIFICATES(self.env.env_name)
        elif self.env.is_evnfm_related:
            path_to_cert = ProjectFilesLocation.EO_CERTIFICATES(self.env.env_name)
        else:
            path_to_cert = ProjectFilesLocation.LM_CERTIFICATES(self.env.env_name)
        shutil.make_archive(path_to_cert, 'zip', path_to_cert)
        self.ssh_client.transfer_file(f'{path_to_cert}.zip', ControllerFilesLocation.CERT_ARCHIVE(self.env.workdir))
        self.execute_command(Command.UNZIP_ARCHIVE_TO_DIR(self.env.workdir))
        os.remove(f'{path_to_cert}.zip')
        if self.env.is_cm_related:
            self.execute_command(f'echo "{self.registry_certificate}" >> {self.env.workdir}/certificates/intermediate-ca.crt')
        logging.info('Certificates transferred successfully.')

    def _prepare_site_values_file(self):
        """
        Method for preparing namespaces and site values file
        """
        logging.info(f'Starting namespace {self.env.namespace} and site values preparation...')
        if self.env.install_evnfm or self.env.install_cm or self.env.install_lm:
            self.__create_namespace(self.env.namespace)
            self.__create_namespace(self.env.common_config.crd_namespace)
            if self.env.install_clm:
                self.__create_namespace(self.env.common_config.capi_wl_ns)
        self.execute_command(f'rm -f {self.env.workdir}/site_values_*')
        prepare_site_values = self.execute_command(Command.PREPARE_SITE_VALUES(self.net_param, self.env.workdir, self.env.dm_version, self.env.namespace), pty=True)
        assert 'prepare completed successfully' in prepare_site_values, 'Error during preparing site values file!'
        site_values_file = self.ssh_client.read_file(
            f"{self.env.workdir}/site_values_{self.env.helmfile_version}.yaml").read().decode('utf-8')
        values = yaml.load(site_values_file, Loader=yaml.FullLoader)
        if self.env.is_cm_related:
            updated_values = self.__update_cm_values(values)
        elif self.env.is_evnfm_related:
            updated_values = self.__update_evnfm_values(values)
        elif self.env.is_lm_related:
            updated_values = self.__update_lm_values(values)
        self.ssh_client.create_file_with_content(f"{self.env.workdir}/site_values_{self.env.helmfile_version}.yaml", yaml.dump(updated_values))
        logging.info('Namespace and site values were prepared successfully.')

    def __update_lm_values(self, values: dict):
        values['global']['hosts']['iam'] = self.env.config.iam_host
        values['global']['hosts']['lm'] = self.env.config.lm_host
        values['global']['hosts']['gas'] = self.env.config.gas_host
        values['global']['hosts']['git'] = self.env.config.git_host
        values['global']['registry']['url'] = self.registry_host
        values['global']['registry']['username'] = self.env.config.registry_user
        values['global']['registry']['password'] = self.env.config.registry_pass

        values['global'].update({'exposureApiManagerClient': {'config': {'image': {'repoPath': 'proj-adp-rs-sef-released'}}}})

        values['tags'].update({'eoLm': True})

        values['global']['externalIPv4']['loadBalancerIP'] = self.env.config.load_balancer_ip
        values['eric-oss-common-base']['service-mesh-ingress-gateway']['service']['loadBalancerIP'] = self.env.config.load_balancer_ip
        values['eric-cloud-native-base']['eric-data-object-storage-mn']['persistentVolumeClaim']['size'] = self.env.config.registry_size
        values['eric-oss-common-base']['system-user']['credentials']['username'] = self.env.common_config.system_user
        values['eric-oss-common-base']['system-user']['credentials']['password'] = self.env.common_config.system_pass
        values['eric-oss-common-base']['gas']['defaultUser']['username'] = self.env.common_config.gas_user
        values['eric-oss-common-base']['gas']['defaultUser']['password'] = self.env.common_config.gas_pass

        values['eric-eo-lifecycle-manager']['eric-oss-gitops-gitea']['enabled'] = True
        values['eric-eo-lifecycle-manager']['eric-oss-gitops-gitea-postgres']['enabled'] = True

        values['eric-eo-lifecycle-manager']['eric-lcm-container-registry']['ingress']['hostname'] = self.env.config.docker_registry_host
        values['eric-eo-lifecycle-manager']['eric-oss-gitops-fx-management']['configuration']['createSkeleton'] = True
        values['eric-eo-lifecycle-manager']['eric-oss-gitops-fx-management']['configuration']['bootstrapFlux'] = True
        values['eric-eo-lifecycle-manager']['eric-oss-gitops-fx-management']['configuration']['repoSecret'] = 'container-credentials'
        values['eric-eo-lifecycle-manager']['eric-oss-gitops-fx-management']['configuration']['shardCount'] = 1
        values['global'].update({'ericsson': {'licensing': {'licenseDomains': [{'productType': 'Ericsson_Orchestrator', 'swltId': 'STB-EVNFM-1', 'customerId': '800141'}]}}})
        values['global']['licensing']['sites'][0]['hostname'] = self.nels_host

        values.update({"eric-service-exposure-framework": {"eric-sef-exposure-api-gateway": {"plugins": {"enabled": False}}}})

        try:
            del values['global']['networkPolicy']
        except KeyError:
            pass  # will be removed when LM will deliver fix
        return values

    def __update_common_values(self, values: dict):
        values['global']['registry']['url'] = self.registry_host
        values['global']['registry']['username'] = self.env.config.registry_user
        values['global']['registry']['password'] = self.env.config.registry_pass
        values['global'].update({'ericsson': {'licensing': {'licenseDomains': [{'productType': 'Ericsson_Orchestrator', 'swltId': 'STB-EVNFM-1', 'customerId': '800141'}]}}})
        values['global']['licensing']['sites'][0]['hostname'] = self.nels_host
        values['eric-oss-common-base']['system-user']['credentials']['username'] = self.env.common_config.system_user
        values['eric-oss-common-base']['system-user']['credentials']['password'] = self.env.common_config.system_pass
        values['eric-oss-common-base']['gas']['defaultUser']['username'] = self.env.common_config.gas_user
        values['eric-oss-common-base']['gas']['defaultUser']['password'] = self.env.common_config.gas_pass
        values['eric-oss-common-base']['service-mesh-ingress-gateway']['service']['loadBalancerIP'] = self.env.config.load_balancer_ip
        values['eric-cloud-native-base']['eric-ctrl-bro']['persistence']['persistentVolumeClaim']['size'] = self.env.config.bro_size
        values['eric-cloud-native-base'].update({'eric-fh-snmp-alarm-provider': {'sendAlarm': self.env.config.send_snmp_alarm if self.env.config.send_snmp_alarm else True}})
        if self.env.is_cm_related:
            values['eric-cloud-native-base']['eric-data-object-storage-mn']['persistentVolumeClaim']['size'] = self.env.config.registry_size
        if not self.is_ipv4:
            values['global']['support']['ipv6']['enabled'] = True
        if self.env.config.is_collocated_env:
            node_type = 'ccm' if self.env.is_cm_related else 'eo'
            is_selector = self.execute_director_command(Command.CHECK_NODE_SELECTOR)
            if is_selector:
                values['global'].update({'nodeSelector': {'node': node_type}})
        if self.env.config.syslog_ip and self.env.config.syslog_port:
            values['eric-cloud-native-base']['eric-log-transformer']['egress']['syslog']['enabled'] = True
            values['eric-cloud-native-base']['eric-log-transformer']['egress']['syslog']['tls']['enabled'] = True
            values['eric-cloud-native-base']['eric-log-transformer']['egress']['syslog'].update({'remoteHosts': [{'host': self.env.config.syslog_ip, 'port': self.env.config.syslog_port, 'protocol': 'TCP'}]})
        return values

    def __update_cm_values(self, values):
        values = self.__update_common_values(values)
        values['global']['hosts']['iam'] = f'iam-{self.env.env_name}.{self.env.config.domain_name}'
        values['global']['hosts']['gas'] = f'gas-{self.env.env_name}.{self.env.config.domain_name}'
        values['global']['hosts']['cm'] = f'eo-cm-{self.env.env_name}.{self.env.config.domain_name}'
        if self.is_ipv4:
            values['global']['externalIPv4']['loadBalancerIP'] = self.env.config.esa_lb
        else:
            values['global']['externalIPv6']['loadBalancerIP'] = self.env.config.esa_lb
        values['global']['siteName'] = self.env.env_name
        values['global']['clusterName'] = self.env.common_config.cluster_name
        values['global']['domainName'] = self.env.config.domain_name

        values['tags']['eoCm'] = self.env.install_cm

        values['eric-eo-cm']['defaultUser']['username'] = self.env.common_config.eo_cm_user
        values['eric-eo-cm']['defaultUser']['password'] = self.env.common_config.eo_cm_pass
        values['eric-eo-cm']['eric_eo_cm_broker_credentials']['password'] = self.env.common_config.eric_eo_cm_broker_pass
        values['eric-eo-cm']['eric-eo-cm-db']['password'] = self.env.common_config.eric_eo_cm_dbpass
        values['eric-eo-cm']['eric-eo-cm-db']['superpwd'] = self.env.common_config.eric_eo_cm_superpwd
        values['eric-eo-cm']['eric-eo-cm-db']['db_cmdb_pass'] = self.env.common_config.db_cmdb_pass
        values['eric-eo-cm']['eric-eo-cm-db']['db_ecm_pass'] = self.env.common_config.db_ecm_pass
        values['eric-eo-cm']['eric-eo-cm-db']['db_actprovadapter_pass'] = self.env.common_config.db_actprovadapter_pass
        values['eric-eo-cm']['eric-eo-cm-db']['db_eda_pass'] = self.env.common_config.db_eda_pass
        values['eric-eo-cm']['eric-eo-cm-ns-lcm']['eric-eo-cm-ns-lcm-db']['password'] = self.env.common_config.eric_eo_cm_ns_lcm_db_pass
        values['eric-eo-cm']['eric-eo-cm-ns-lcm']['eric-eo-cm-ns-lcm-db']['superpwd'] = self.env.common_config.eric_eo_cm_ns_lcm_db_superpwd
        values['eric-eo-cm']['eric-eo-cm-cust-wf']['enabled'] = True
        values['eric-eo-cm']['eric-eo-cm-order-mgmt-ca']['eric-eo-cm-order-mgmt-ca-db']['password'] = self.env.common_config.eric_eo_cm_order_mgmt_ca_db_pass
        values['eric-eo-cm']['eric-eo-cm-order-mgmt-ca']['eric-eo-cm-order-mgmt-ca-db']['superpwd'] = self.env.common_config.eric_eo_cm_order_mgmt_ca_db_pass
        domain = self.env.config.domain_name
        values['eric-eo-cm']['eric-eo-cm-idam']['domain'] = domain[domain.find('.'):]
        values['eric-eo-cm']['eric-eo-cm-idam']['cmdbSync_pass'] = self.env.common_config.cmdb_sync_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['configStore']['amConfigPassword'] = self.env.common_config.cs_am_config_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['configStore']['dsPassword'] = self.env.common_config.cs_ds_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['configStore']['monitorPassword'] = self.env.common_config.cs_monitor_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['ctsStore']['dsPassword'] = self.env.common_config.cts_ds_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['ctsStore']['monitorPassword'] = self.env.common_config.cts_monitor_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['ctsStore']['openamCtsPassword'] = self.env.common_config.cts_openam_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['ecmAdmin_pass'] = self.env.common_config.ecm_admin_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['userStore']['dsPassword'] = self.env.common_config.us_ds_pass
        values['eric-eo-cm']['eric-eo-cm-idam']['userStore']['monitorPassword'] = self.env.common_config.us_monitor_pass
        values['eric-eo-cm']['toscaocm']['password'] = self.env.common_config.toscaocm_pass
        values['eric-eo-cm']['toscaocm']['superpwd'] = self.env.common_config.toscaocm_superpwd
        values['eric-eo-cm']['eric-eo-cm-license-consumer-db']['custompwd'] = self.env.common_config.licence_consumer_db_pass
        values['eric-eo-cm']['eric-eo-cm-license-consumer-db']['superpwd'] = self.env.common_config.licence_consumer_db_superpwd
        values['eric-eo-cm']['eric-eo-cm-cust-wf'].update({'eric-eo-cm-cust-wf-db': {'password': self.env.common_config.eric_eo_cm_cust_wf_db_pass,
                                                                                     'superpwd': self.env.common_config.eric_eo_cm_cust_wf_db_superpwd}})
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['onboardPassword'] = self.env.common_config.onboard_pass
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['eoadminPassword'] = self.env.common_config.eoadmin_pass
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['adminPassword'] = self.env.common_config.admin_pass
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['ecmadminPassword'] = self.env.common_config.ecmadmin_pass
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['ecmActPassword'] = self.env.common_config.ecm_act_pass
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['scmClientId'] = self.env.common_config.scm_client_id
        values['eric-eo-cm']['eric-eo-cm-core']['edaConfigJob']['scmClientSecret'] = self.env.common_config.scm_client_secret
        values['eric-eo-cm']['eric-eo-cm-core']['credentials']['am_password'] = self.env.common_config.am_pass
        values['eric-cloud-native-base']['eric-data-object-storage-mn'].update({'global': {'security': {'tls': {'enabled': True}}}})

        values.update({"eric-eo-evnfm": {
            "eric-lcm-container-registry": {"ingress": {"hostname": self.registry_host}},
            "eric-lcm-helm-chart-registry": {"ingress": {"hostname": self.registry_host},
                                             "env": {"secret": {"BASIC_AUTH_USER": self.env.config.registry_user,
                                                                "BASIC_AUTH_PASS": self.env.config.registry_pass}}}}})
        values['eric-oss-function-orchestration-common'].update({'eric-am-onboarding-service': {'userSecret': 'container-credentials',
                                                                                                'enabled': True}})
        if self.env.install_clm:
            values['eric-oss-eo-clm']['enabled'] = self.env.install_clm

        if all([acc := self.env.config.account, ddp_id := self.env.config.ddpid,
                enabled := self.env.config.enable,
                passwd := self.env.config.ddp_pass]):
            values['eric-oss-common-base'].update(
                {'eric-oss-ddc': {
                    'autoUpload': {'account': acc, 'ddpid': ddp_id, 'enabled': enabled, 'password': passwd,
                                   'prefixUpload': 'yes'}}})
            self.is_ddc = True
        return values

    def __update_evnfm_values(self, values: dict):
        values = self.__update_common_values(values)
        values['global']['hosts']['iam'] = self.env.config.iam_host
        values['global']['hosts']['vnfm'] = self.env.config.vnfm_host
        values['global']['hosts']['gas'] = self.env.config.gas_host

        values['tags']['eoEvnfm'] = ast.literal_eval(os.environ.get('INSTALL_C_VNFM', 'True').capitalize())
        values['tags']['eoVmvnfm'] = ast.literal_eval(os.environ.get('INSTALL_VM_VNFM', 'True').capitalize())

        values['eric-eo-evnfm']['eric-lcm-container-registry']['ingress']['hostname'] = self.env.config.docker_registry_host
        values['eric-eo-evnfm']['eric-lcm-container-registry'].update(
            {'persistence': {
                'persistentVolumeClaim': {
                    'size': self.env.config.registry_size}}})
        values['eric-eo-evnfm']['eric-lcm-helm-chart-registry']['ingress']['enabled'] = True
        values['eric-eo-evnfm']['eric-lcm-helm-chart-registry']['ingress']['hostname'] = self.env.config.helm_registry_host
        values['eric-eo-evnfm']['eric-lcm-helm-chart-registry']['env']['secret']['BASIC_AUTH_USER'] = self.env.common_config.helm_auth_user
        values['eric-eo-evnfm']['eric-lcm-helm-chart-registry']['env']['secret']['BASIC_AUTH_PASS'] = self.env.common_config.helm_auth_pass
        values['eric-eo-evnfm']['eric-vnfm-orchestrator-service']['smallstack']['application'] = self.env.config.enable_smallstack
        values['eric-eo-evnfm']['eric-vnfm-orchestrator-service']['oss']['topology']['secretName'] = 'enm-secret'
        values['eric-eo-evnfm'].update({'eric-am-common-wfs': {'userSecret': 'container-credentials'}})

        if self.env.config.enm_load_balancer_ip:
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['service']['loadBalancerIP'] = self.env.config.enm_load_balancer_ip
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['service']['enabled'] = True
        else:
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['service']['loadBalancerIP'] = self.env.config.load_balancer_ip

        values['eric-eo-evnfm-vm']['eric-vnflcm-service']['oss']['secretName'] = 'oss-secret'

        values['eric-oss-function-orchestration-common'].update({'eric-am-onboarding-service': {'container': {'registry': {'enabled': True}},
                                                                                                'userSecret': 'container-credentials',
                                                                                                'onboarding': {'skipCertificateValidation': False}},
                                                                 'eric-eo-evnfm-nbi': {'eric-evnfm-rbac': {
                                                                     'defaultUser': {'username': self.env.config._vnfm_user if self.env.config._vnfm_user else self.env.common_config.vnfm_user,
                                                                                     'password': self.env.common_config.vnfm_pass}}}})
        if is_enabled := self.env.enable_vm_vnfm_ha:
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['ha']['enabled'] = is_enabled
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['ha']['persistentVolumeClaim']['storageClassName'] = self.env.config.storage_class
        else:
            values['eric-eo-evnfm-vm']['eric-vnflcm-service']['ha']['enabled'] = is_enabled
        if not self.is_ipv4:
            values['eric-eo-evnfm'].update({'application-manager-postgres': {'global': {'internalIPFamily': 'IPv6'}}})
        if enable_gr := self.env.enable_evnfm_gr:
            values['geo-redundancy']['enabled'] = enable_gr
            values['global']['hosts']['gr'] = self.env.config.gr_host
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['credentials']['password'] = self.env.common_config.gr_pass
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['credentials']['username'] = self.env.common_config.gr_user
            cluster_role = self.env.cluster_role
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['cluster']['role'] = cluster_role
            match cluster_role:
                case ClusterType.PRIMARY:
                    values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['cluster']['secondary_hostnames'][0] = self.env.config.secondary_host
                case ClusterType.SECONDARY:
                    with suppress(KeyError):
                        del values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['cluster']['secondary_hostnames']
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['registry'] = {'secondarySiteContainerRegistryHostname': self.env.config.secondary_host,
                                                                                            'userSecretName': 'container-credentials',
                                                                                            'usernameKey': 'userid',
                                                                                            'passwordKey': 'userpasswd'}

            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['sftp']['url'] = self.env.config.sftp_url
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['sftp']['username'] = self.env.config.sftp_name
            values['eric-oss-common-base']['eric-gr-bur-orchestrator']['gr']['sftp']['password'] = self.env.config.sftp_pass
            values['eric-eo-evnfm']['eric-global-lcm-container-registry']['hostname'] = self.env.global_registry
            values['eric-eo-evnfm']['eric-global-lcm-container-registry']['username'] = self.env.common_config.eo_reg_user
            values['eric-eo-evnfm']['eric-global-lcm-container-registry']['password'] = self.env.common_config.eo_reg_pass
            values['eric-eo-evnfm'].update({'eric-am-common-wfs': {'dockerRegistry': {'secret': 'container-credentials'}}})
        return values

    def __configure_env_for_ha(self):
        is_nfs_installed = self.execute_director_command('helm ls -A | grep nfs-fs3')
        if self.env.env_name in ['c13a3', 'c15a2', 'c15a3', 'c16a024'] and not is_nfs_installed:
            self.execute_director_command(Command.ADD_NFS_PROVISIONER_REPO)
            self.execute_director_command(Command.INSTALL_NFS_PROVISIONER(self.env.env_name.upper()))

    def __delete_namespace(self, ns_name: str):
        logging.info(f'Deletion of namespace {ns_name} started...')
        delete_namespace = self.execute_command(Command.DELETE_NAMESPACE(ns_name, self.kube_config), pty=True)
        if 'NotFound' not in delete_namespace:
            assert f'namespace "{ns_name}" deleted' in delete_namespace, f'Error during namespace {ns_name} deleting!'
        logging.info(f'Namespace {ns_name} was deleted.')

    def __delete_clusterroles(self, ns_name):
        self.execute_command(Command.DELETE_CLUSTERROLES(ns_name, self.kube_config))

    def __delete_clusterrolebindings(self, ns_name):
        self.execute_command(Command.DELETE_CLUSTERROLEBINDINGS(ns_name, self.kube_config))

    def __delete_crd(self):
        crds_to_delete = ('projectcontour', 'sec.tls', 'siptls.sec', 'cassandraclusters.wcdbcd.data.ericsson.com', 'istio')
        for crd in crds_to_delete:
            self.execute_command(Command.DELETE_CRD(self.env.common_config.crd_namespace, crd, self.kube_config))

    def __create_namespace(self, ns_name: str):
        create_namespace = self.execute_command(Command.CREATE_NAMESPACE(ns_name, self.kube_config), pty=True)
        try:
            assert f'namespace/{ns_name} created' in create_namespace
        except AssertionError:
            assert 'already exists' in create_namespace, f'Error during namespace {ns_name} creation!'

    @retry(AssertionError, tries=3, delay=30)
    def _push_images(self):
        logging.info('Image push started, please be patient...')
        image_push = self.execute_command(Command.EXECUTE_IMAGE_PUSH(self.env.workdir, self.env.dm_version), pty=True)
        assert 'Image push completed successfully' in image_push, logging.error('Error during image push process!')
        logging.info('Image push finished successfully!')

    def _transfer_site_values_for_aat(self):
        logging.info(f'Starting namespace {self.env.namespace} creation and site values preparation...')
        self.__create_namespace(self.env.namespace)
        with open('resources/aat_resources/site_values.yaml', 'r', encoding='utf-8') as yaml_file:
            site_values = yaml.load(yaml_file, Loader=yaml.FullLoader)
            site_values['global']['hosts']['agatAatAdapter'] = self.env.config.aat_host
            site_values['global']['registry']['url'] = self.registry_host
            site_values['global']['registry']['username'] = self.env.config.registry_user
            site_values['global']['registry']['password'] = self.env.config.registry_pass
            site_values['aat']['adapter']['host']['ip'] = self.env.config.aat_host
            self.ssh_client.create_file_with_content(
                f'{self.env.workdir}/site_values_{self.env.helmfile_version}.yaml', yaml.dump(site_values))
        logging.info('Namespace was created and site values were prepared successfully.')

    def install_aat_test_service(self):
        logging.info('EO installation started, please be patient...')
        install_eo = self.execute_command(
            Command.EXECUTE_AAT_INSTALL(self.env.workdir, self.env.dm_version,
                                        self.env.namespace, self.env.helm_timeout), pty=True)
        assert 'EO install completed successfully' in install_eo or 'Install completed successfully' in install_eo, 'Error during EO installation!'
        logging.info('EO installation finished successfully!')
