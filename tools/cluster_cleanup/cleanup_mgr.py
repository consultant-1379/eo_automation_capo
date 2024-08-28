import logging

from libs import get_bool_environ
from libs.constants import EnvVariables
from libs.decorators import retry
from libs.environment_init.eo_init import EoEnv
from libs.eo_libs.controller.controller_vm import ControllerVm
from libs.eo_libs.director.director_vm import DirectorVM
from libs.utils.config_manager.config_manager import EvnfmConfig
from tools.cluster_cleanup.cleanup_data import CleanupCommands

ssh_cmd = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'


class ClusterCleanup:
    def __init__(self):
        try:
            EvnfmConfig()
            self.env = EoEnv(is_evnfm=True)
        except FileNotFoundError:
            self.env = EoEnv(is_cm=True)
        controller_vm = ControllerVm(self.env)
        self.registry_user = controller_vm.env.config.registry_user
        self.registry_pass = controller_vm.env.config.registry_pass
        self.exec_comm = controller_vm.execute_command
        self.kube_config = f'{controller_vm.env.workdir}/kube_config/config'
        self.need_to_delete_images: bool = get_bool_environ(EnvVariables.DELETE_NODE_IMAGES, 'false')
        self.kubectl_cmd = CleanupCommands.KUBECTL(self.kube_config)

    def execute_cleanup(self):
        logging.info('Starting cleanup, please wait...')
        self.__clean_manifests()
        self.__clean_registry()
        if self.need_to_delete_images:
            self.__delete_images()
        logging.info('Checking all pods are up and running in the namespace "kube-system"...')
        self.__check_all_pods_running()
        logging.info('All pods are up and running!')
        logging.info('Cleanup finished successfully!')

    def __clean_manifests(self):
        logging.info('Manifests cleanup started...')
        registry = self.exec_comm(CleanupCommands.KUBECTL(self.kube_config) + CleanupCommands.GET_REGISTRY)
        curl_cmd = CleanupCommands.CURL(self.registry_user, self.registry_pass)
        repos = self.exec_comm(curl_cmd + CleanupCommands.GET_REPOS(f'https://{registry}/v2/_catalog')).split()
        for repo in repos:
            tags = self.exec_comm(curl_cmd + CleanupCommands.GET_TAGS(f'https://{registry}/v2/{repo}/tags/list'))
            if 'error' in tags:
                continue
            for tag in tags.split():
                manifests = self.exec_comm(
                    curl_cmd + CleanupCommands.GET_MANIFESTS(f'https://{registry}/v2/{repo}/manifests/{tag}')).split()
                for manifest in manifests:
                    logging.debug(f"Delete {repo} tag {tag} manifest {manifest}")
                    output = self.exec_comm(curl_cmd + CleanupCommands.DELETE_MANIFEST(
                        f"https://{registry}/v2/{repo}/manifests/{manifest}"))
                    assert not output, output
        logging.info('Manifests cleanup finished successfully!')

    def __clean_registry(self):
        logging.info('Registry cleanup started...')
        registry_pods = self.exec_comm(self.kubectl_cmd + CleanupCommands.GET_REGISTRY_POD).split()
        for registry_pod in registry_pods:
            self.exec_comm(CleanupCommands.GARBAGE_COLLECT(self.kubectl_cmd, registry_pod))
            output = self.exec_comm(self.kubectl_cmd + CleanupCommands.RM_REPOS(registry_pod))
            assert not output, output
            output = self.exec_comm(self.kubectl_cmd + CleanupCommands.RM_SHA256(registry_pod))
            assert not output, output
            logging.debug(f"Restarting {registry_pod}...")
            self.exec_comm(self.kubectl_cmd + CleanupCommands.DELETE_POD(registry_pod))
        logging.info('Registry cleanup finished successfully!')

    def __delete_images(self):
        logging.info('Removing docker images tagged to k8s-registry from all nodes...')
        nodes_ips = self.exec_comm(self.kubectl_cmd + CleanupCommands.GET_NODES_IPS).split()
        director_vm = DirectorVM(self.env)
        for node_ip in nodes_ips:
            output = director_vm.execute_director_command(f'{ssh_cmd} {node_ip} "{CleanupCommands.DELETE_IMAGES}"')
            if "Permission denied" in output:
                logging.info(f"There is no access to node {node_ip}. Skipping its images cleanup")
        logging.info('Nodes cleanup finished successfully!')

    @retry(AssertionError, tries=20, delay=10)
    def __check_all_pods_running(self):
        not_running_pods = self.exec_comm(self.kubectl_cmd + CleanupCommands.CHECK_PODS)
        assert not not_running_pods, f'Not all pods are up and running, check your environment:\n{not_running_pods}'


if __name__ == '__main__':
    ClusterCleanup().execute_cleanup()
