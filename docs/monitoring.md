# Monitoring

```sh
# Install helm
sudo snap install helm --classic

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update


# Default username will be `admin`.
helm install prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

# Get password of the dashboard
kubectl --namespace monitoring get secrets prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

# Check if all pods are running
kubectl get pods -n monitoring

# Run the command an open Forwarding host "127.0.0.1:3000" in the browser.
kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3000:80
```
