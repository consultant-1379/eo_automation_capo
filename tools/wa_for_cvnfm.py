import logging
import os
import textwrap

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from libs import get_environ
from libs.constants import ProjectFilesLocation, CertsIssuers, DirectorFilesLocation, EnvVariables
from libs.decorators import retry
from libs.eo_libs.controller.controller_data import ControllerCommands
from libs.eo_libs.director.eo_environment_manager.environment_mgr import scp_cmd, ssh_cmd
from libs.eo_libs.director.eo_kubernetes_manager.kuber_data import KubernetesManagerCommands
from libs.utils.ssh_client import SSHClient


class CvnfmWaForEccd:
    def __init__(self):
        director_ip = get_environ('CLUSTER_CRED').split('@')[1]
        user_name = get_environ('CLUSTER_CRED').split('@')[0]
        private_key = get_environ('PRIVATE_KEY')
        wrapped_key = textwrap.fill(private_key, width=64)
        self.filename = 'temp_key.pem'
        self.pem = open(self.filename, 'a+')
        self.pem.write(wrapped_key)
        self.pem.seek(0)
        self.pem.read()
        self.director_ssh_client = SSHClient(host=director_ip,
                                             user_name=user_name,
                                             private_key_file=self.filename)
        self.execute_director_command = self.director_ssh_client.execute_command
        self.env_name = get_environ(EnvVariables.ENV).strip()

    def apply_workaround_for_cvnfm(self):
        logging.info('Starting apply WA for CVNFM...')
        with open(f'{ProjectFilesLocation.EO_CERTIFICATES(self.env_name)}/intermediate-ca.crt', 'rb') as cert:
            data = cert.read()
            cert = x509.load_pem_x509_certificate(data, default_backend())
            cert_issuer = cert.issuer.rfc4514_string()
            if any(issuer for issuer in CertsIssuers.INTERNAL_TRUST_ISSUERS.value if issuer in cert_issuer):
                logging.info('You are using internal trust certificates, will apply workaround for CVNFM')
                worker_ips = self.execute_director_command(
                    KubernetesManagerCommands.GET_WORKERS_IPS('worker')).split()
                self.execute_director_command(ControllerCommands.CREATE_FOLDER(os.path.dirname(DirectorFilesLocation.TMP_INTER_CERT)))
                self.director_ssh_client.transfer_file(
                    f'{ProjectFilesLocation.EO_CERTIFICATES(self.env_name)}/intermediate-ca.crt',
                    DirectorFilesLocation.TMP_INTER_CERT)
                self._containerd_workaround(worker_ips)
            else:
                logging.info('You are using external trust certificates, no worries :)')
        self.pem.close()
        os.remove(self.filename)
        logging.info('WA applied successfully!')

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

    @retry(AssertionError, tries=20, delay=10)
    def __check_all_pods_running(self, namespace):
        logging.info(f'Checking all pods are up and running in the namespace {namespace}...')
        not_running_pods = self.execute_director_command(
            KubernetesManagerCommands.GET_NOT_RUNNING_PODS(namespace, '~/.kube/config'))
        assert not not_running_pods, f'Not all pods are up and running, check your environment:\n{not_running_pods}'
        logging.info('All pods are up and running!')


if __name__ == '__main__':
    CvnfmWaForEccd().apply_workaround_for_cvnfm()
