# Create Kubernetes namespaces
resource "kubernetes_namespace" "jenkins" {
  metadata {
    name = "jenkins"
    labels = {
      name        = "jenkins"
      environment = var.environment
    }
  }

  depends_on = [google_container_cluster.gke_cluster]
}

resource "kubernetes_namespace" "ace_fitness" {
  metadata {
    name = "ace-fitness"
    labels = {
      name        = "ace-fitness"
      environment = var.environment
    }
  }

  depends_on = [google_container_cluster.gke_cluster]
}

# Create service account for Jenkins
resource "kubernetes_service_account" "jenkins" {
  metadata {
    name      = "jenkins"
    namespace = kubernetes_namespace.jenkins.metadata[0].name
  }
}

# Create cluster role for Jenkins
resource "kubernetes_cluster_role" "jenkins" {
  metadata {
    name = "jenkins"
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services", "endpoints", "persistentvolumeclaims"]
    verbs      = ["create", "delete", "get", "list", "patch", "update", "watch"]
  }

  rule {
    api_groups = [""]
    resources  = ["nodes"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "replicasets"]
    verbs      = ["create", "delete", "get", "list", "patch", "update", "watch"]
  }

  rule {
    api_groups = ["extensions"]
    resources  = ["deployments", "replicasets"]
    verbs      = ["create", "delete", "get", "list", "patch", "update", "watch"]
  }
}

# Bind cluster role to service account
resource "kubernetes_cluster_role_binding" "jenkins" {
  metadata {
    name = "jenkins"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.jenkins.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.jenkins.metadata[0].name
    namespace = kubernetes_namespace.jenkins.metadata[0].name
  }
}

# Create persistent volume claim for Jenkins
resource "kubernetes_persistent_volume_claim" "jenkins" {
  metadata {
    name      = "jenkins-pv-claim"
    namespace = kubernetes_namespace.jenkins.metadata[0].name
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    
    resources {
      requests = {
        storage = "${var.jenkins_disk_size}Gi"
      }
    }

    storage_class_name = "standard"
  }
}

# Deploy Jenkins
resource "kubernetes_deployment" "jenkins" {
  metadata {
    name      = "jenkins"
    namespace = kubernetes_namespace.jenkins.metadata[0].name
    labels = {
      app = "jenkins-server"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "jenkins-server"
      }
    }

    template {
      metadata {
        labels = {
          app = "jenkins-server"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.jenkins.metadata[0].name

        security_context {
          fs_group    = 1000
          run_as_user = 1000
        }

        container {
          name  = "jenkins"
          image = "jenkins/jenkins:lts"

          port {
            name           = "httpport"
            container_port = 8080
          }

          port {
            name           = "jnlpport"
            container_port = 50000
          }

          liveness_probe {
            http_get {
              path = "/login"
              port = 8080
            }
            initial_delay_seconds = 90
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 5
          }

          readiness_probe {
            http_get {
              path = "/login"
              port = 8080
            }
            initial_delay_seconds = 60
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          volume_mount {
            name       = "jenkins-data"
            mount_path = "/var/jenkins_home"
          }

          env {
            name  = "JAVA_OPTS"
            value = "-Djenkins.install.runSetupWizard=false"
          }

          env {
            name  = "JENKINS_OPTS"
            value = "--httpPort=8080"
          }

          resources {
            limits = {
              memory = "2Gi"
              cpu    = "1000m"
            }
            requests = {
              memory = "500Mi"
              cpu    = "500m"
            }
          }
        }

        volume {
          name = "jenkins-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.jenkins.metadata[0].name
          }
        }
      }
    }
  }
}

# Create Jenkins LoadBalancer service with static IP
resource "kubernetes_service" "jenkins" {
  metadata {
    name      = "jenkins-service"
    namespace = kubernetes_namespace.jenkins.metadata[0].name
    annotations = {
      "prometheus.io/scrape"                 = "true"
      "prometheus.io/path"                   = "/"
      "prometheus.io/port"                   = "8080"
      "cloud.google.com/load-balancer-type" = "External"
    }
  }

  spec {
    selector = {
      app = "jenkins-server"
    }

    type                = "LoadBalancer"
    load_balancer_ip    = google_compute_address.jenkins_static_ip.address
    
    port {
      name        = "httpport"
      port        = 80
      target_port = 8080
      protocol    = "TCP"
    }

    port {
      name        = "jnlpport"
      port        = 50000
      target_port = 50000
      protocol    = "TCP"
    }
  }
}

# Create ACE Fitness app service (without deployment - managed by Jenkins)
resource "kubernetes_service" "ace_fitness" {
  metadata {
    name      = "ace-fitness-service"
    namespace = kubernetes_namespace.ace_fitness.metadata[0].name
    labels = {
      app = "ace-fitness-app"
    }
    annotations = {
      "cloud.google.com/load-balancer-type" = "External"
    }
  }

  spec {
    selector = {
      app = "ace-fitness-app"
    }

    type             = "LoadBalancer"
    load_balancer_ip = google_compute_address.app_static_ip.address

    port {
      name        = "http"
      port        = 80
      target_port = 5000
      protocol    = "TCP"
    }
  }
}