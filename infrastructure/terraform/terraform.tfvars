# Terraform configuration file for environment-specific values
# Copy this file to terraform.tfvars and customize as needed

# GCP Project Configuration
project_id = "itd-2021mt93693"
region     = "us-central1"
zone       = "us-central1-a"

# Cluster Configuration
cluster_name = "itd-cluster"
environment  = "dev"

# Node Configuration
node_count   = 3
machine_type = "e2-medium"
disk_size_gb = 30

# Autoscaling Configuration
min_nodes = 1
max_nodes = 5

# Jenkins Configuration
jenkins_disk_size = 20