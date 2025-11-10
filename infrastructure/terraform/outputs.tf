# Output values for use in other systems

output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.gke_cluster.name
}

output "cluster_endpoint" {
  description = "Endpoint for the GKE cluster"
  value       = google_container_cluster.gke_cluster.endpoint
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.gke_cluster.location
}

output "jenkins_static_ip" {
  description = "Static IP address for Jenkins"
  value       = google_compute_address.jenkins_static_ip.address
}

output "app_static_ip" {
  description = "Static IP address for the application"
  value       = google_compute_address.app_static_ip.address
}

output "jenkins_url" {
  description = "URL to access Jenkins"
  value       = "http://${google_compute_address.jenkins_static_ip.address}"
}

output "app_url" {
  description = "URL to access the application (after deployment)"
  value       = "http://${google_compute_address.app_static_ip.address}"
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ace_fitness_repo.repository_id}"
}

output "kubectl_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.gke_cluster.name} --zone ${var.zone} --project ${var.project_id}"
}

output "jenkins_admin_password_command" {
  description = "Command to get Jenkins admin password"
  value       = "kubectl exec --namespace jenkins -it deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword"
}

output "resource_summary" {
  description = "Summary of created resources"
  value = {
    cluster_name           = google_container_cluster.gke_cluster.name
    jenkins_ip            = google_compute_address.jenkins_static_ip.address
    app_ip               = google_compute_address.app_static_ip.address
    artifact_registry    = google_artifact_registry_repository.ace_fitness_repo.repository_id
    namespaces           = [kubernetes_namespace.jenkins.metadata[0].name, kubernetes_namespace.ace_fitness.metadata[0].name]
  }
}