"""
Data for Environment Manager
"""


class EnvironmentManagerCommands:
    DELETE_NAMESPACE = 'kubectl delete namespace {0} --kubeconfig {1}'.format
    DELETE_CRD = "kubectl delete crd --namespace {0} --kubeconfig {2} $(kubectl get crd --namespace {0} --kubeconfig {2} | grep {1} | cut -f1 -d ' ')".format
    DELETE_CLUSTERROLES = '''kubectl delete clusterroles --kubeconfig {1} $(kubectl get clusterroles --kubeconfig {1} -o=jsonpath='{{.items[?(@.metadata.annotations.meta\\.helm\\.sh\\/release-namespace=="{0}")].metadata.name}}')'''.format
    DELETE_CLUSTERROLEBINDINGS = '''kubectl delete clusterrolebindings --kubeconfig {1} $(kubectl get clusterrolebindings --kubeconfig {1} -o=jsonpath='{{.items[?(@.metadata.annotations.meta\\.helm\\.sh\\/release-namespace=="{0}")].metadata.name}}') --kubeconfig {1}'''.format
    EXTRACT_DEPLOYMENT_MANAGER = "unzip -oj {0}/deployment-manager-{1}.zip -d {0}".format
    LOAD_DEPLOYMENT_MANAGER = 'sudo docker load --input {}/deployment-manager.tar'.format
    INITIALIZE_WORKDIR = 'sudo docker run --rm -u $(id -u):$(id -g) -v {}:/workdir deployment-manager:{} init'.format

    CREATE_NAMESPACE = 'kubectl create namespace {0} --kubeconfig {1}'.format
    PREPARE_SITE_VALUES = 'sudo docker run {} --rm -u $(id -u):$(id -g) -v {}:/workdir -v /etc/hosts:/etc/hosts deployment-manager:{} prepare --namespace {}'.format

    GET_REGISTRY_URL = 'kubectl get ingress eric-lcm-container-registry-ingress -n kube-system -o jsonpath="{.spec.tls[*].hosts[0]}"; echo'
    GET_API_URL = 'kubectl get ingress kubernetes-api -n kube-system -o jsonpath="{.spec.tls[*].hosts}"; echo'

    GET_REG_SECRET = """kubectl get secrets -n kube-system cr-registry-tls -o jsonpath="{.data.tls\\.crt}" | base64 --decode"""

    EXECUTE_INSTALL = 'sudo docker run {0} --rm -v /var/run/docker.sock:/var/run/docker.sock -v {1}:/workdir -v /etc/hosts:/etc/hosts deployment-manager:{2} install --namespace {3} --helm-timeout {4} --crd-namespace {5} --skip-image-check-push'.format
    EXECUTE_UPGRADE = 'sudo docker run {0} --rm -v /var/run/docker.sock:/var/run/docker.sock -v {1}:/workdir -v /etc/hosts:/etc/hosts deployment-manager:{2} upgrade --namespace {3} --helm-timeout {4} --crd-namespace {5} --skip-image-check-push'.format
    EXECUTE_AAT_INSTALL = 'sudo docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v {0}:/workdir -v /etc/hosts:/etc/hosts deployment-manager:{1} install --namespace {2} --helm-timeout {3} --skip-crds'.format

    EXECUTE_IMAGE_PUSH = 'sudo docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v {0}:/workdir -v /etc/hosts:/etc/hosts deployment-manager:{1} image push --docker-timeout 600'.format
    UNZIP_ARCHIVE_TO_DIR = 'unzip -d {0}/certificates -jo {0}/certificates/certs.zip'.format
    DELETE_FILE = 'sudo rm -f {}'.format
    COPY_FILE = 'cp {} {}'.format

    CHECK_NODE_SELECTOR = 'kubectl describe no | grep node='

    SET_DEFAULT_NAMESPACE = 'kubectl config set-context --current --namespace {0}'.format
    GET_CODEPLOY_ALIASES = 'grep -F "codeploy aliases" ./.bashrc'
    ADD_ALIASES_TO_BASHRC = 'echo >> ./.bashrc'

    READLOG_VMVNFM_ALIAS = '''kubectl exec -it {0} -n {1} -- /bin/bash -c "echo alias readlog=\\'tail -f /ericsson/3pp/jboss/standalone/log/server.log\\' >> /home/eric-vnflcm-service/.bashrc"'''.format
    OPENLOG_VMVNFM_ALIAS = '''kubectl exec -it {0} -n {1} -- /bin/bash -c "echo alias openlog=\\'vi /ericsson/3pp/jboss/standalone/log/server.log\\' >> /home/eric-vnflcm-service/.bashrc"'''.format

    LIST_CAPI_MANAGER = 'kubectl get all -A | grep deployment.apps/capi-controller-manager'

    ADD_NFS_PROVISIONER_REPO = 'helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/'
    INSTALL_NFS_PROVISIONER = 'helm install nfs-fs3 nfs-subdir-external-provisioner/nfs-subdir-external-provisioner --set storageClass.name=network-file --set nfs.server=10.232.14.23 --set nfs.path=/nfs/{} --set storageClass.archiveOnDelete=false --namespace kube-system'.format


class EnvironmentManagerData:
    ALIASES = """
# codeploy aliases
source <(kubectl completion bash|sed s/kubectl/k/g)
alias c=clear
alias k=kubectl
alias po='kubectl get po -n {0}'
alias ns='kubectl get ns'
alias no='kubectl get no -o wide'
alias pvc='kubectl get pvc -n {0}'
alias ingress='kubectl get ingress --all-namespaces'
alias wpo='watch -n 1 \\"kubectl get po -n {0} | column\\"'
alias svc='kubectl exec -it {1} -n {0} -- /bin/bash'""".format


class CmEnvData:
    @staticmethod
    def get_helm_registry(reg_user, reg_pass, reg_host, reg_cert):
        return {'docker': {
            'registry': {
                'credentials': {
                    'user': reg_user,
                    'password': reg_pass
                },
                'url': {
                    'host': reg_host
                },
                'cert': reg_cert
            }}}

    @staticmethod
    def get_docker_registry(reg_user, reg_pass, reg_host, reg_cert):
        return {'helm': {
            'repo': {
                'credentials': {
                    'user': reg_user,
                    'password': reg_pass
                },
                'url': {
                    'host': reg_host
                },
                'cert': reg_cert
            }}}
