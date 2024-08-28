class CleanupCommands:
    CURL = 'curl -s -u {}:{} '.format
    GET_REPOS = '''-X GET {} | jq '.repositories[]' | sort | tr -d '"' '''.format
    GET_TAGS = '''-X GET {} | jq '.tags[]' | tr -d '"' '''.format
    GET_MANIFESTS = '''-v -H "Accept: application/vnd.docker.distribution.manifest.v2+json" -X GET {} 2>&1 | grep docker-content-digest| awk '{{print $3}}' '''.format
    DELETE_MANIFEST = '-X DELETE {}'.format
    KUBECTL = 'kubectl -n kube-system --kubeconfig {} '.format
    GET_REGISTRY = 'get ingress eric-lcm-container-registry-ingress -o jsonpath="{.spec.tls[*].hosts[0]}"'
    GET_REGISTRY_POD = "get po | grep registry | grep -v controller-manager | awk '{print ($1)}'"
    GARBAGE_COLLECT = 'bash -c "{} exec -t {} -- /usr/bin/registry garbage-collect /etc/registry/config.yml" > /dev/null 2>&1'.format
    RM_REPOS = "exec -t {} -c registry -- /bin/bash -c 'rm -rf /var/lib/registry/docker/registry/v2/repositories/*'".format
    RM_SHA256 = "exec -t {} -c registry -- /bin/bash -c 'rm -rf /var/lib/registry/docker/registry/v2/blobs/sha256/*'".format
    DELETE_POD = 'delete po {}'.format
    GET_NODES_IPS = """get no -o json | jq -r '.items[] | .status.addresses[] | select (.type | test("InternalIP")).address ' | grep -v ::"""
    DELETE_IMAGES = "for i in \\$(sudo crictl image ls | sed '1 d' | grep -v 5000 | awk {'print \\$3'}); do sudo crictl rmi \\$i; done"
    CHECK_PODS = '''get pod| grep -Pv '\\s+([1-9]+)\\/\\1\\s+' | grep -v Completed | sed "1 d"'''
