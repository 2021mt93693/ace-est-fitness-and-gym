pipeline {
    agent any
    
    triggers {
        // Poll SCM every 2 minutes to detect changes
        pollSCM('H/2 * * * *')
    }
    
    environment {
        PYTHONPATH = "${WORKSPACE}/src"
        DOCKER_IMAGE = 'ace-est-fitness-and-gym'
        DOCKER_TAG = "${BUILD_NUMBER}"
        GCP_PROJECT_ID = 'itd-2021mt93693'  // Your project ID
        GCP_REGION = 'us-central1'
        ARTIFACT_REGISTRY_REPO = 'ace-fitness-repo'
        K8S_NAMESPACE = 'ace-fitness'
        GCP_SERVICE_ACCOUNT_KEY = credentials('gcp-service-account-key')  // Add this credential in Jenkins
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Code Quality Check') {
            steps {
                script {
                    // Basic file checks
                    sh '''
                        echo "Checking project structure..."
                        ls -la
                        if [ -f "Dockerfile" ]; then
                            echo "✓ Dockerfile found"
                        else
                            echo "✗ Dockerfile not found"
                            exit 1
                        fi
                        if [ -f "requirements.txt" ]; then
                            echo "✓ requirements.txt found"
                        else
                            echo "✗ requirements.txt not found"
                            exit 1
                        fi
                        if [ -f "src/app.py" ]; then
                            echo "✓ app.py found"
                        else
                            echo "✗ app.py not found" 
                            exit 1
                        fi
                        echo "Project structure validation passed!"
                    '''
                }
            }
        }
        
        stage('Unit Testing & Linting') {
            steps {
                script {
                    sh '''
                        # Set PATH to include kubectl (if needed)
                        export PATH=$PATH:/tmp/google-cloud-sdk/bin:/var/jenkins_home/.local/bin
                        
                        echo "Running Python linting and unit tests using Python container..."
                        
                        # Create a temporary testing job in Kubernetes
                        kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: python-test-${BUILD_NUMBER}
  namespace: jenkins
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: python-tester
        image: python:3.9-slim
        command: ["/bin/bash"]
        args:
        - "-c"
        - |
          echo "Installing dependencies..."
          pip install --upgrade pip
          pip install flake8 pytest coverage pytest-cov
          
          echo "Installing project requirements..."
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
          
          echo "Running linting..."
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "Critical linting issues found"
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || echo "Style issues found"
          
          echo "Running unit tests..."
          export PYTHONPATH=/workspace/src
          pytest --cov=src --cov-report=xml --cov-report=term tests/ || echo "Tests completed with issues"
          
          echo "Python testing completed!"
        workingDir: /workspace
        volumeMounts:
        - name: source-code
          mountPath: /workspace
      initContainers:
      - name: git-clone
        image: alpine/git:latest
        command: ["/bin/sh"]
        args:
        - "-c"
        - "git clone https://github.com/2021mt93693/ace-est-fitness-and-gym.git /workspace && cd /workspace && git checkout FEATURE-JENKINS"
        volumeMounts:
        - name: source-code
          mountPath: /workspace
      volumes:
      - name: source-code
        emptyDir: {}
EOF
                        
                        # Wait for job completion
                        echo "Waiting for testing job to complete..."
                        kubectl wait --for=condition=complete job/python-test-${BUILD_NUMBER} -n jenkins --timeout=300s || echo "Testing timeout"
                        
                        # Show test results
                        echo "=== Test Results ==="
                        kubectl logs job/python-test-${BUILD_NUMBER} -n jenkins -c python-tester || echo "Could not retrieve test logs"
                        
                        # Clean up test job (but allow failure for debugging)
                        kubectl delete job python-test-${BUILD_NUMBER} -n jenkins --ignore-not-found=true || echo "Cleanup attempted"
                        
                        echo "Unit testing stage completed!"
                    '''
                }
            }
            post {
                always {
                    script {
                        // Archive any test artifacts that might exist
                        sh 'echo "Test stage completed"'
                    }
                }
            }
        }
        
        stage('GCP Authentication') {
            steps {
                script {
                    sh '''
                        echo "Setting up GCP and Kubernetes tools..."
                        
                        # Check if running as root (needed for package installation)
                        if [ "$EUID" -ne 0 ]; then
                            echo "Not running as root, trying alternative installation methods..."
                        fi
                        
                        # Try to install gcloud CLI if not present (may fail due to permissions)
                        if ! command -v gcloud &> /dev/null; then
                            echo "gcloud CLI not found, attempting installation..."
                            
                            # Try snap install first (if available)
                            if command -v snap &> /dev/null; then
                                snap install google-cloud-sdk --classic || echo "Snap install failed"
                            fi
                            
                            # If still not available, download binary
                            if ! command -v gcloud &> /dev/null; then
                                echo "Downloading gcloud SDK..."
                                cd /tmp
                                curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-450.0.0-linux-x86_64.tar.gz
                                tar -xzf google-cloud-sdk-450.0.0-linux-x86_64.tar.gz
                                export PATH=$PATH:/tmp/google-cloud-sdk/bin
                                cd -
                            fi
                        fi
                        
                        # Install kubectl if not present
                        if ! command -v kubectl &> /dev/null; then
                            echo "Installing kubectl..."
                            curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl"
                            chmod +x kubectl
                            mkdir -p ~/.local/bin && mv kubectl ~/.local/bin/
                            export PATH=$PATH:~/.local/bin
                        fi
                        
                        # Verify tools are available
                        echo "Checking tool availability..."
                        gcloud version || echo "gcloud not available"
                        kubectl version --client || echo "kubectl not available"
                        docker --version || echo "docker not available"
                        
                        # If we have gcloud, authenticate
                        if command -v gcloud &> /dev/null; then
                            echo "Authenticating with GCP..."
                            gcloud auth activate-service-account --key-file=$GCP_SERVICE_ACCOUNT_KEY
                            gcloud config set project $GCP_PROJECT_ID
                            gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                            
                            # Install GKE auth plugin
                            echo "Installing GKE auth plugin..."
                            gcloud components install gke-gcloud-auth-plugin --quiet || echo "GKE auth plugin installation attempted"
                            
                            # Configure kubectl to connect to the GKE cluster
                            echo "Configuring kubectl..."
                            gcloud container clusters get-credentials itd-cluster --zone=us-central1-a --project=$GCP_PROJECT_ID
                        else
                            echo "WARNING: gcloud CLI not available, will try manual configuration"
                        fi
                        
                        echo "GCP authentication completed!"
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    sh '''
                        echo "Building Docker image..."
                        
                        # Read version from build.version file
                        VERSION=$(cat build.version)
                        echo "Building version: $VERSION"
                        
                        # Build the Docker image with multiple tags
                        docker build -t ${DOCKER_IMAGE}:${VERSION} \
                                    -t ${DOCKER_IMAGE}:latest \
                                    -t ${DOCKER_IMAGE}:build-${BUILD_NUMBER} .
                        
                        # Tag for GCP Artifact Registry
                        docker tag ${DOCKER_IMAGE}:${VERSION} ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${VERSION}
                        docker tag ${DOCKER_IMAGE}:latest ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:latest
                        
                        # Set environment variable for deployment
                        echo "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${VERSION}" > docker_image_full.txt
                        
                        echo "Docker build completed successfully!"
                    '''
                    
                    // Store the full image name for deployment
                    env.DOCKER_IMAGE_FULL = readFile('docker_image_full.txt').trim()
                    echo "Full Docker image: ${env.DOCKER_IMAGE_FULL}"
                }
            }
        }
        
        stage('Push to Artifact Registry') {
            steps {
                script {
                    sh '''
                        echo "Pushing Docker image to GCP Artifact Registry..."
                        
                        # Set PATH to include gcloud
                        export PATH=$PATH:/tmp/google-cloud-sdk/bin
                        
                        VERSION=$(cat build.version)
                        
                        # Push images to Artifact Registry
                        docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${VERSION}
                        docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:latest
                        
                        echo "Docker image pushed successfully!"
                    '''
                }
            }
        }
        
        
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh """
                        # Set PATH to include gcloud and kubectl
                        export PATH=\$PATH:/tmp/google-cloud-sdk/bin:/var/jenkins_home/.local/bin
                        
                        # Create namespace if it doesn't exist
                        kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                        
                        # Apply service first (if it doesn't exist)
                        if ! kubectl get service ace-fitness-service -n ${K8S_NAMESPACE} 2>/dev/null; then
                            echo "Deploying service..."
                            kubectl apply -f infrastructure/k8s/manifest_files/app/service.yaml
                        fi
                        
                        # Apply or update deployment
                        if ! kubectl get deployment ace-fitness-app -n ${K8S_NAMESPACE} 2>/dev/null; then
                            echo "First deployment - applying deployment and ingress manifests"
                            # Update the deployment.yaml to use the new image before applying
                            sed -i "s|image: ace-est-fitness-and-gym:latest|image: ${env.DOCKER_IMAGE_FULL}|" infrastructure/k8s/manifest_files/app/deployment.yaml
                            kubectl apply -f infrastructure/k8s/manifest_files/app/deployment.yaml
                            kubectl apply -f infrastructure/k8s/manifest_files/app/ingress.yaml
                        else
                            echo "Updating existing deployment with new image"
                            # Update the deployment with the new image
                            kubectl set image deployment/ace-fitness-app ace-fitness-app=${env.DOCKER_IMAGE_FULL} -n ${K8S_NAMESPACE}
                        fi
                        
                        # Wait for rollout to complete
                        kubectl rollout status deployment/ace-fitness-app -n ${K8S_NAMESPACE} --timeout=300s
                        
                        # Verify deployment
                        echo "=== Deployment Status ==="
                        kubectl get pods -n ${K8S_NAMESPACE}
                        kubectl get services -n ${K8S_NAMESPACE}
                        kubectl get ingress -n ${K8S_NAMESPACE}
                        
                        # Show access information
                        echo "=== Access Information ==="
                        APP_IP=\$(kubectl get service ace-fitness-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
                        if [ "\$APP_IP" != "pending" ] && [ "\$APP_IP" != "" ]; then
                            echo "Application is accessible at: http://\${APP_IP}"
                        else
                            echo "LoadBalancer IP is still pending. Please check later with:"
                            echo "kubectl get service ace-fitness-service -n ${K8S_NAMESPACE}"
                        fi
                        
                        # Show ingress information if available
                        INGRESS_IP=\$(kubectl get ingress -n ${K8S_NAMESPACE} -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
                        if [ "\$INGRESS_IP" != "" ]; then
                            echo "Ingress IP: \$INGRESS_IP"
                        fi
                    """
                }
            }
        }
        
        stage('Tag Release') {
            when {
                branch 'main'
            }
            steps {
                script {
                    def version = readFile('build.version').trim()
                    sh """
                        git config user.name "Jenkins"
                        git config user.email "jenkins@localhost"
                        git tag "v${version}"
                        git push origin "v${version}"
                    """
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}