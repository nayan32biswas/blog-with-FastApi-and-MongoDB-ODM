# Monitoring

This document explains how to set up monitoring for our blog application using Prometheus and Grafana.

## Setup Using Helm (Recommended)

```sh
# Install helm if not already installed
sudo snap install helm --classic

# Add the Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install the Prometheus stack (includes Prometheus, Grafana, and Alertmanager)
helm install prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

# Get the Grafana admin password
kubectl --namespace monitoring get secrets prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

# Verify all pods are running
kubectl get pods -n monitoring

# Access Grafana dashboard (default username: admin)
kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3000:80
```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the Grafana dashboard.

## Accessing Logs

To view the Nginx ingress controller logs:

```sh
# Get the ingress controller pod name
kubectl get pods -n ingress-nginx

# View the logs
kubectl logs -f <ingress-controller-pod-name> -n ingress-nginx
```

## Dashboard Configuration

By default you will find several predefined dashboards. Here's how to create custom dashboards:

1. **Create Dashboard**

   - Go to Dashboards → New dashboard → Add visualization → Select "Prometheus"

2. **Add CPU Usage Panel**
   - Use the query: `sum(rate(container_cpu_usage_seconds_total{namespace="blog-app-ns"}[5m])) by (pod) * 100`
   - Set unit to "Percent"
3. **Add Memory Usage Panel**

   - Use the query: `sum(container_memory_working_set_bytes{namespace="blog-app-ns"}) by (pod)`
   - Set unit to "Bytes"

4. **Add Network Traffic Panel**

   - Use the query: `sum(rate(container_network_receive_bytes_total{namespace="blog-app-ns"}[5m])) by (pod)`
   - Set unit to "Bytes/sec"

5. **Add Ingress Controller Metrics**
   - Use the query: `sum(nginx_ingress_controller_requests) by (status)`
   - Create a graph or gauge visualization
