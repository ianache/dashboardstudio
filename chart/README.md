```
export USERNAME=
export PASSWORD=
kubectl create secret generic git-creds --from-literal=username='${USERNAME}' --from-literal=password='${PASSWORD}' -n bi
```

```
kubectl create secret generic git-creds --from-literal=username='${USERNAME}' --from-literal=password='${PASSWORD}' -n bi
```