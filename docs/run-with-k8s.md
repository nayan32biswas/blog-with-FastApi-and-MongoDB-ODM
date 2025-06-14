# Run the application with Kubernetes

We added a simple example configuration to run the app with Kubernetes. For simplicity, we are using a single Docker image for the dev and prod environments.

We are using Minikube to run the Kubernetes cluster on a local device, and it's not being tested in production.

Make sure the `minikube` is installed locally. And start the minikube service with the command `minikube start`.

## Install and configure the necessary tools

- `minikube start`
- `minikube addons enable ingress` Enable the ingress
  - `kubectl get pods -n ingress-nginx` Verify the **ingress-nginx-controller** is running.
- `minikube ip` Get the minikube ip address to access the server.
- `sudo vi /etc/hosts` Update the host file with `<minikube-ip> local.blog-app.com`.
  - It will be accessible within the local device, not from the internet.

## Basic commands to run the app

- Navigate to the project in the terminal.
- `docker build -t fastapi_blog_prod:latest -f Dockerfile.prod .` Build the Docker image.
- `minikube image load fastapi_blog_prod:latest` Load the new image into the minikube. It will be used by the k8s locally.
- `cp k8s/example.env.secrets ./k8s/overlays/dev/.env.secrets && cp k8s/example.env.properties ./k8s/overlays/dev/.env.properties` Copy the example config and secrets to the targeted folder. Modify the file content if required.
- `kubectl apply -k k8s/dev` Run the application including the database.
- `kubectl config set-context --current --namespace=blog-app-ns` Set the namespace as default.
- To restart the change after changing the code in the application you might need to remove the image from the minikube.
