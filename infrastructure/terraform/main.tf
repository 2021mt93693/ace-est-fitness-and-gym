# Enable required APIs
resource "google_project_service" "cloudresourcemanager_api" {
  service = "cloudresourcemanager.googleapis.com"
}

resource "google_project_service" "container_api" {
  service = "container.googleapis.com"
}

resource "google_project_service" "artifactregistry_api" {
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "cloudbuild_api" {
  service = "cloudbuild.googleapis.com"
}

# Reserve static external IP for Jenkins
resource "google_compute_address" "jenkins_static_ip" {
  name         = "jenkins-static-ip"
  region       = var.region
  address_type = "EXTERNAL"
  description  = "Static IP for Jenkins LoadBalancer"

  depends_on = [google_project_service.container_api]
}

# Reserve static external IP for Application
resource "google_compute_address" "app_static_ip" {
  name         = "ace-fitness-static-ip"
  region       = var.region
  address_type = "EXTERNAL"
  description  = "Static IP for ACE Fitness application LoadBalancer"

  depends_on = [google_project_service.container_api]
}

# Create GKE cluster
resource "google_container_cluster" "gke_cluster" {
  name     = var.cluster_name
  location = var.zone

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Enable autoscaling
  cluster_autoscaling {
    enabled = true
    resource_limits {
      resource_type = "cpu"
      minimum       = 1
      maximum       = 10
    }
    resource_limits {
      resource_type = "memory"
      minimum       = 1
      maximum       = 20
    }
  }

  # Network configuration
  network    = "default"
  subnetwork = "default"

  # Enable basic authentication and issue client certificates
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Enable IP aliasing
  ip_allocation_policy {}

  # Enable legacy ABAC until RBAC is enabled
  enable_legacy_abac = false

  # Configure addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  depends_on = [
    google_project_service.container_api,
  ]
}

# Create node pool
resource "google_container_node_pool" "primary_nodes" {
  name     = "${var.cluster_name}-node-pool"
  location = var.zone
  cluster  = google_container_cluster.gke_cluster.name

  node_count = var.node_count

  # Enable autoscaling
  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  # Node configuration
  node_config {
    preemptible  = false
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-standard"

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = var.environment
    }

    tags = ["gke-node", "${var.cluster_name}-node"]

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }

  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Create service account for GKE nodes
resource "google_service_account" "gke_service_account" {
  account_id   = "${var.cluster_name}-sa"
  display_name = "Service Account for ${var.cluster_name} GKE nodes"
}

# Bind necessary roles to the service account
resource "google_project_iam_member" "gke_service_account_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/artifactregistry.reader"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"

  depends_on = [google_project_service.cloudresourcemanager_api]
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "ace_fitness_repo" {
  location      = var.region
  repository_id = "ace-fitness-repo"
  description   = "Docker repository for ACE Fitness application"
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry_api]
}