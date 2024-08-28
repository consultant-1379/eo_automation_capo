"""
Kubernetes assets management
"""
import json
import logging

from libs.eo_libs.director.director_vm import DirectorVM
from libs.eo_libs.director.eo_kubernetes_manager.kuber_data import KubernetesManagerCommands as Command, DeploymentData


class KubernetesManager(DirectorVM):

    def create_kuber_assets(self):
        """
        Main method from Kubernetes Manager to run all functions
        """
        self._create_sec_access_mgmt_creds_secret()
        self._create_eo_database_pg_secret()
        self._create_container_credentials_secret()
        if self.env.is_cm_related or self.env.is_evnfm_related:
            self._create_snmp_alarm_secret()
        if self.env.install_evnfm:
            self._create_enm_secret()
            self._create_oss_secret()
        if self.env.install_evnfm or self.env.install_lm:
            self._create_container_registry_users_secret()
        if self.env.install_lm:
            self._create_sec_access_mgmt_aapxy_cred_secret()

    def recreate_oss_secret(self):
        self.execute_command(Command.DELETE_OSS_SECRET(self.env.namespace, self.kube_config), pty=True)
        self._create_oss_secret()

    def _create_sec_access_mgmt_creds_secret(self):
        eric_sec_access_mgmt_creds_secret = self.execute_command(
            Command.CREATE_ERIC_SEC_ACCESS_MGMT_CREDS_SECRET(self.env.common_config.kc_admin_id,
                                                             self.env.common_config.kc_pass,
                                                             self.env.common_config.pg_user_id,
                                                             self.env.common_config.pg_pass,
                                                             self.env.namespace, self.kube_config), pty=True)
        assert 'secret/eric-sec-access-mgmt-creds created' in eric_sec_access_mgmt_creds_secret, \
            'Error during creating eric-sec-access-mgmt-creds secret!'
        logging.info('Secret eric-sec-access-mgmt-creds created.')

    def _create_eo_database_pg_secret(self):
        eric_eo_database_pg_secret = self.execute_command(
            Command.CREATE_ERIC_EO_DATABASE_PG_SECRET(self.env.common_config.custom_user_id,
                                                      self.env.common_config.custom_pass,
                                                      self.env.common_config.super_user_id,
                                                      self.env.common_config.super_pass,
                                                      self.env.common_config.metrics_user_id,
                                                      self.env.common_config.metrics_pass,
                                                      self.env.common_config.replica_user_id,
                                                      self.env.common_config.replica_pass,
                                                      self.env.namespace, self.kube_config), pty=True)
        assert 'secret/eric-eo-database-pg-secret created' in eric_eo_database_pg_secret, \
            'Error during creating eric-eo-database-pg-secret secret!'
        logging.info('Secret eric-eo-database-pg-secret created.')

    def _create_enm_secret(self):
        enm_secret = self.execute_command(
            Command.CREATE_ENM_SECRET(self.env.config.enm_scripting_cluster_ip,
                                      self.env.config.enm_user,
                                      self.env.config.enm_pass,
                                      self.env.config.enm_connection_timeout_in_milliseconds,
                                      self.env.config.enm_scripting_ssh_port,
                                      self.env.namespace,
                                      self.kube_config), pty=True)
        assert 'secret/enm-secret created' in enm_secret, 'Error during creating enm-secret!'
        logging.info('Secret enm-secret created.')

    def _create_oss_secret(self):
        oss_secret = self.execute_command(
            Command.CREATE_OSS_SECRET(self.env.config.enm_scripting_cluster_ip,
                                      self.env.config.enm_notification_ip,
                                      self.env.namespace, self.kube_config), pty=True)
        assert 'secret/oss-secret created' in oss_secret, 'Error during creating oss-secret!'
        logging.info('Secret oss-secret created.')

    def _create_container_registry_users_secret(self):
        htpasswd = self.execute_command(
            Command.CREATE_HTPASSWD(self.env.workdir,
                                    self.env.common_config.eo_reg_user,
                                    self.env.common_config.eo_reg_pass,
                                    self.kube_config), pty=True)
        assert f'Adding password for user {self.env.common_config.eo_reg_user}' in htpasswd, \
            'Error during generating htpasswd!'
        container_registry_users_secret = self.execute_command(
            Command.CREATE_CONTAINER_REGISTRY_USERS_SECRET(self.env.workdir, self.env.namespace,
                                                           self.kube_config), pty=True)
        assert 'secret/container-registry-users-secret created' in container_registry_users_secret, \
            'Error during creating container-registry-users-secret secret!'
        logging.info('Secret container-registry-users-secret created.')

    def _create_container_credentials_secret(self):
        registry_host = self.env.config.docker_registry_host if self.env.install_evnfm or self.env.install_lm else self.registry_host
        registry_user = self.env.common_config.eo_reg_user if self.env.install_evnfm or self.env.install_lm else self.env.config.registry_user
        registry_pass = self.env.common_config.eo_reg_pass if self.env.install_evnfm or self.env.install_lm else self.env.config.registry_pass
        secret = self.execute_command(
            Command.CONTAINER_CREDENTIALS_SECRET(registry_host, registry_user, registry_pass,
                                                 self.env.namespace, self.kube_config), pty=True)
        assert 'secret/container-credentials created' in secret, 'Error during creating container-credentials secret!'
        logging.info('Secret container-credentials created.')

    def _create_snmp_alarm_secret(self):
        secret_file_path = f'{self.env.workdir}/config.json'
        secret_file_content = json.dumps(DeploymentData.get_alarm_config(self.env.common_config.snmp_server_ip,
                                                                         self.env.common_config.snmp_community))
        self.ssh_client.create_file_with_content(secret_file_path, secret_file_content)
        secret = self.execute_command(Command.SNMP_ALARM_SECRET(self.env.namespace, secret_file_path, self.kube_config))
        assert 'secret/snmp-alarm-provider-config created' in secret, 'Error during creating snmp-alarm-provider-config secret!'
        logging.info('Secret snmp-alarm-provider-config created.')
        self.execute_command(f'rm -f {secret_file_path}')

    def _create_sec_access_mgmt_aapxy_cred_secret(self):
        secret = self.execute_command(Command.CREATE_SEC_ACCESS_MGMT_AAPXY_CREDS_SECRET(self.env.common_config.lm_pass,
                                                                                        self.env.namespace,
                                                                                        self.kube_config))
        assert 'secret/eric-sec-access-mgmt-aapxy-cred' in secret, 'Error during creating eric-sec-access-mgmt-aapxy-cred secret!'
