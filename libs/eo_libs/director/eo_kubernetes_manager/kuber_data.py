"""
Kubernetes data for Kubernetes Manager
"""


class KubernetesManagerCommands:
    CREATE_ERIC_SEC_ACCESS_MGMT_CREDS_SECRET = "kubectl create secret generic eric-sec-access-mgmt-creds --from-literal=kcadminid='{}' --from-literal=kcpasswd='{}' --from-literal=pguserid={} --from-literal=pgpasswd='{}' --namespace {}  --kubeconfig {}".format
    CREATE_ERIC_EO_DATABASE_PG_SECRET = "kubectl create secret generic eric-eo-database-pg-secret --from-literal=custom-user='{}' --from-literal=custom-pwd='{}' --from-literal=super-user='{}' --from-literal=super-pwd='{}' --from-literal=metrics-user='{}' --from-literal=metrics-pwd='{}' --from-literal=replica-user='{}' --from-literal=replica-pwd='{}' --namespace {}  --kubeconfig {}".format

    CREATE_SEC_ACCESS_MGMT_AAPXY_CREDS_SECRET = "kubectl create secret generic eric-sec-access-mgmt-aapxy-creds --from-literal=aapxysecret={} --namespace {} --kubeconfig {}".format
    CREATE_HTPASSWD = 'htpasswd -cBb {}/htpasswd {} {}'.format
    CREATE_CONTAINER_REGISTRY_USERS_SECRET = 'kubectl create secret generic container-registry-users-secret --from-file=htpasswd={}/htpasswd --namespace {} --kubeconfig {}'.format
    CONTAINER_CREDENTIALS_SECRET = 'kubectl create secret generic container-credentials --from-literal=url={} --from-literal=userid={} --from-literal=userpasswd={} --namespace {} --kubeconfig {}'.format
    SNMP_ALARM_SECRET = 'kubectl create secret generic snmp-alarm-provider-config --namespace {} --from-file={} --kubeconfig {}'.format

    CREATE_ENM_SECRET = "kubectl create secret generic enm-secret --from-literal=enm-scripting-ip={} --from-literal=enm-scripting-username='{}' --from-literal=enm-scripting-password='{}' --from-literal=enm-scripting-connection-timeout={} --from-literal=enm-scripting-ssh-port={} --namespace {} --kubeconfig {}".format

    DELETE_OSS_SECRET = 'kubectl delete secret oss-secret --namespace {} --kubeconfig {}'.format

    CREATE_OSS_SECRET_OLD = "kubectl create secret generic oss-secret --from-literal=oss-masterserver-hostname=masterservice --from-literal=oss-notification-hostname=notificationservice --from-literal=oss-masterservice-ip={} --from-literal=oss-notificationservice-ip={} --namespace {} --kubeconfig {}".format
    CREATE_OSS_SECRET = "kubectl create secret generic oss-secret --from-literal=oss-primaryserver-hostname=masterservice --from-literal=oss-notification-hostname=notificationservice --from-literal=oss-primaryservice-ip={} --from-literal=oss-notificationservice-ip={} --namespace {} --kubeconfig {}".format
    CREATE_SERVICE_ACCOUNT = 'kubectl create -f {}/ServiceAccount.yaml --namespace {} --kubeconfig {}'.format

    DELETE_CLUSTER_ROLE_BINDING = 'kubectl delete clusterrolebindings.rbac.authorization.k8s.io evnfm-{} --kubeconfig {}'.format
    CREATE_CLUSTER_ROLE_BINDING = 'kubectl create -f {}/ClusterRoleBinding.yaml --kubeconfig {}'.format

    GET_WORKERS_IPS = """kubectl get no -o json | jq -r '.items[] | select (.metadata.name| test("{}")).status.addresses[] | select (.type | test("InternalIP")).address '""".format

    GET_ECCD_VERSION = """less /usr/local/lib/erikube_setup/image-list.json | grep erikube_version |tr -d '",'| awk '{{print $2}}'"""

    GET_NOT_RUNNING_PODS = '''kubectl get pod -n {} --kubeconfig {} | grep -Pv '\\s+([1-9]+)\\/\\1\\s+' | grep -v Completed | sed "1 d"'''.format


class DeploymentData:
    @staticmethod
    def get_alarm_config(address, community):
        return {
            "agentEngineId": "12abc1b804c162d0",
            "trapTargets": [{"address": address, "community": community}]}
