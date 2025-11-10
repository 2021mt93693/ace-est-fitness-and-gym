# ACE Fitness Infrastructure - Terraform

This directory contains Terraform configuration for deploying the ACE Fitness application infrastructure on Google Cloud Platform.

## 🏗️ What Gets Created

- **GKE Cluster**: 3-node Kubernetes cluster with autoscaling
- **Static IP Addresses**: Permanent IPs for Jenkins and application
- **Artifact Registry**: Docker image repository
- **Jenkins**: CI/CD server with persistent storage
- **Kubernetes Namespaces**: Separate environments for Jenkins and application
- **RBAC**: Proper service accounts and permissions
- **LoadBalancer Services**: External access to services

## 📋 Prerequisites

1. **Terraform**: Install from [terraform.io](https://terraform.io)
2. **Google Cloud CLI**: Install `gcloud` and authenticate
3. **GCP Project**: Ensure billing is enabled

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project itd-2021mt93693
```

## 🚀 Quick Start

```bash
# Navigate to terraform directory
cd infrastructure/terraform

# Deploy everything
./deploy.sh apply

# Get access information
./deploy.sh access
```

## 📝 Detailed Usage

### 1. Initialize Terraform
```bash
./deploy.sh init
```

### 2. Review planned changes
```bash
./deploy.sh plan
```

### 3. Deploy infrastructure
```bash
./deploy.sh apply
```

### 4. Configure kubectl
```bash
./deploy.sh kubectl
```

### 5. Get access URLs
```bash
./deploy.sh access
```

### 6. View current state
```bash
./deploy.sh show
```

### 7. Cleanup (when done)
```bash
./deploy.sh destroy
```

## 📁 File Structure

```
terraform/
├── providers.tf          # Provider configurations
├── variables.tf          # Input variables
├── main.tf               # Core infrastructure (GKE, IPs, Artifact Registry)
├── kubernetes.tf         # Kubernetes resources (namespaces, Jenkins)
├── outputs.tf            # Output values
├── terraform.tfvars.example  # Example configuration
├── deploy.sh             # Convenient wrapper script
└── README.md            # This file
```

## ⚙️ Configuration

Copy the example configuration file and customize:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your preferences
```

### Key Variables

- `project_id`: Your GCP project ID
- `region`: GCP region (default: us-central1)
- `zone`: GCP zone (default: us-central1-a)
- `cluster_name`: Name for your GKE cluster
- `node_count`: Number of nodes (default: 3)
- `machine_type`: Node machine type (default: e2-medium)

## 🔗 Outputs

After deployment, you'll get:

- **Jenkins URL**: `http://<static-ip>` (permanent)
- **Application URL**: `http://<static-ip>` (after Jenkins deployment)
- **Kubectl Command**: Ready-to-run cluster access command
- **Admin Password Command**: Get Jenkins initial password

## 💰 Cost Estimation

Approximate monthly costs (us-central1):

| Resource | Cost/Month |
|----------|------------|
| GKE Cluster (3 x e2-medium) | ~$72 |
| LoadBalancers (2) | ~$36 |
| Static IPs (2) | ~$6 |
| Artifact Registry | ~$1 |
| **Total** | **~$115** |

## 🔒 Security Features

- **Service Accounts**: Dedicated accounts with minimal permissions
- **RBAC**: Kubernetes role-based access control
- **Network Policies**: Pod-to-pod communication control
- **Private Clusters**: Optional (can be enabled)
- **Secure Defaults**: No legacy endpoints or ABAC

## 🚨 Important Commands

```bash
# Get Jenkins admin password
kubectl exec --namespace jenkins -it deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword

# Check deployment status
kubectl get pods -n jenkins
kubectl get pods -n ace-fitness

# View services and IPs
kubectl get services -A

# Access Jenkins (if LoadBalancer pending)
kubectl port-forward svc/jenkins-service 8080:80 -n jenkins
```

## 🔄 Terraform State

Terraform state is stored locally by default. For team collaboration, consider:

1. **Remote Backend**: Use Google Cloud Storage
2. **State Locking**: Enable state locking
3. **Workspace Management**: Use separate workspaces for environments

Example backend configuration:
```hcl
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "ace-fitness/terraform/state"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Error**
   ```bash
   gcloud auth application-default login
   ```

2. **API Not Enabled**
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

3. **Insufficient Quotas**
   - Check GCP quotas in Console
   - Request quota increases if needed

4. **LoadBalancer Pending**
   - Wait 5-10 minutes for IP assignment
   - Check service events: `kubectl describe service -n jenkins`

### Getting Help

```bash
# Terraform help
./deploy.sh help

# View infrastructure state
./deploy.sh show

# Check Terraform logs
terraform apply -var-file=terraform.tfvars -auto-approve
```

## 🔄 Next Steps

After infrastructure deployment:

1. **Access Jenkins** at the provided URL
2. **Install Required Plugins**:
   - Google Kubernetes Engine
   - Docker Pipeline
   - Pipeline
3. **Configure Credentials**: Add GCP service account key
4. **Create Pipeline Job**: Point to your Jenkinsfile
5. **Deploy Application**: Run the pipeline

## 📚 Additional Resources

- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Jenkins on Kubernetes](https://www.jenkins.io/doc/book/installing/kubernetes/)

---

**Note**: This Terraform configuration replaces the shell scripts and provides better infrastructure management, state tracking, and idempotent operations.