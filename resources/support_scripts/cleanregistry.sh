#!/bin/bash
#To cleanup cluster registry
#Run from client with registry and cluster access

#Set registry credenstials
reguser=$1
regpwd=$2
kubeconfig=$3

#variable
registry=$(kubectl get ingress eric-lcm-container-registry-ingress -n kube-system --kubeconfig $kubeconfig -o jsonpath="{.spec.tls[*].hosts[0]}")
registrypod=$(kubectl get po -n kube-system --kubeconfig $kubeconfig | grep registry | awk '{print ($1)}')
registryurl=https://$registry/v2/_catalog

#get repo
for i in $(curl -s -u $reguser:$regpwd -X GET $registryurl | jq '.repositories[]' | sort | tr -d '"')
  do
    url=https://$registry/v2/$i/tags/list
#get tags
    for z in $( curl -s -u $reguser:$regpwd -X GET $url | jq '.tags[]' | tr -d '"')
      do
        url2=https://$registry/v2/$i/manifests/$z
#get manifest
        for p in $(curl -u $reguser:$regpwd -v --silent -H "Accept: application/vnd.docker.distribution.manifest.v2+json" -X GET $url2 2>&1 | grep docker-content-digest| awk '{print ($3)}')
         do
#mark manifests
           echo  "Delete $i tag $z manifest $p"
            delurl="https://$registry/v2/$i/manifests/$p"
            delurl=${delurl%$'\r'}
            curl -u $reguser:$regpwd -X DELETE $delurl
         done
      done
  done
#clean registry
kubectl exec -t -n kube-system $registrypod --kubeconfig $kubeconfig -- /usr/bin/registry garbage-collect /etc/registry/config.yml
kubectl exec -t -n kube-system $registrypod --kubeconfig $kubeconfig -c registry -- /bin/bash -c 'rm -rf /var/lib/registry/docker/registry/v2/repositories/*'
echo LIST /var/lib/registry/docker/registry/v2/repositories/
kubectl exec -t -n kube-system $registrypod --kubeconfig $kubeconfig -c registry -- ls -l /var/lib/registry/docker/registry/v2/repositories/
kubectl exec -t -n kube-system $registrypod --kubeconfig $kubeconfig -c registry -- /bin/bash -c 'rm -rf /var/lib/registry/docker/registry/v2/blobs/sha256/*'
echo LIST /var/lib/registry/docker/registry/v2/blobs/sha256/
kubectl exec -t -n kube-system $registrypod --kubeconfig $kubeconfig -c registry -- ls -l /var/lib/registry/docker/registry/v2/blobs/sha256/
#restart pod
echo "Restarting $registrypod"
kubectl delete po -n kube-system $registrypod --kubeconfig $kubeconfig
