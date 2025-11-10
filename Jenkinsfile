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
                    // Since we can't install Python in Jenkins container,
                    // we'll skip linting and testing for now
                    // The Docker image build will validate the code works
                    echo "Skipping Python linting/testing - will be handled in Docker build"
                    echo "Code checkout successful, proceeding to Docker build..."
                    
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
                            
                                                    # Configure kubectl to connect to the GKE cluster
                        echo "Configuring kubectl..."
                        gcloud container clusters get-credentials itd-cluster --zone=us-central1-a --project=$GCP_PROJECT_ID
                        else
                            echo "WARNING: gcloud CLI not available, will try manual configuration"
                        fi
                    '''
                }
            }
        }
        
        stage('Docker Build') {
            steps {
                script {
                    def imageTag = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${DOCKER_TAG}"
                    
                    sh """
                        echo "Building and pushing Docker image..."
                        
                        # Check if Docker is available
                        if command -v docker &> /dev/null; then
                            echo "Docker found, proceeding with build..."
                            
                            # Build Docker image
                            echo "Building image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                            
                            # Tag for Artifact Registry
                            echo "Tagging image: ${imageTag}"
                            docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${imageTag}
                            
                            # Push to Artifact Registry
                            echo "Pushing image to Artifact Registry..."
                            docker push ${imageTag}
                            
                            echo "Image pushed successfully: ${imageTag}"
                        else
                            echo "Docker not available in Jenkins container."
                            echo "Using kubectl to create a build pod..."
                            
                            # Create a temporary build pod with Docker-in-Docker
                            kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: docker-build-${BUILD_NUMBER}
  namespace: jenkins
spec:
  restartPolicy: Never
  containers:
  - name: docker
    image: docker:dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: workspace
      mountPath: /workspace
  - name: builder
    image: google/cloud-sdk:latest
    command: ["/bin/bash"]
    args: ["-c", "sleep 3600"]
    env:
    - name: DOCKER_HOST
      value: tcp://localhost:2375
    - name: GCP_PROJECT_ID
      value: "${GCP_PROJECT_ID}"
    - name: GCP_REGION
      value: "${GCP_REGION}"
    - name: ARTIFACT_REGISTRY_REPO
      value: "${ARTIFACT_REGISTRY_REPO}"
    - name: DOCKER_IMAGE
      value: "${DOCKER_IMAGE}"
    - name: DOCKER_TAG
      value: "${DOCKER_TAG}"
    volumeMounts:
    - name: workspace
      mountPath: /workspace
    - name: gcp-key
      mountPath: /tmp/gcp-key.json
      subPath: gcp-key.json
  volumes:
  - name: workspace
    emptyDir: {}
  - name: gcp-key
    secret:
      secretName: gcp-service-account-key
EOF
                            
                            # Wait for pod to be ready
                            echo "Waiting for build pod to be ready..."
                            kubectl wait --for=condition=Ready pod/docker-build-${BUILD_NUMBER} -n jenkins --timeout=300s
                            
                            # Copy source code to the pod
                            echo "Copying source code to build pod..."
                            kubectl cp . jenkins/docker-build-${BUILD_NUMBER}:/workspace -c builder
                            
                            # Execute build commands in the pod
                            echo "Building Docker image in pod..."
                            kubectl exec docker-build-${BUILD_NUMBER} -n jenkins -c builder -- bash -c "
                                cd /workspace
                                gcloud auth activate-service-account --key-file=/tmp/gcp-key.json
                                gcloud config set project ${GCP_PROJECT_ID}
                                gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                                
                                # Wait for Docker daemon to start
                                while ! docker info >/dev/null 2>&1; do
                                    echo 'Waiting for Docker daemon to start...'
                                    sleep 1
                                done
                                
                                # Build and push image
                                docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                                docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${imageTag}
                                docker push ${imageTag}
                                echo 'Build completed successfully!'
                            "
                            
                            # Clean up build pod
                            kubectl delete pod docker-build-${BUILD_NUMBER} -n jenkins --ignore-not-found=true
                            
                            echo "Image built and pushed using Kubernetes build pod: ${imageTag}"
                        fi
                    """
                    
                    // Store the full image tag for deployment
                    env.DOCKER_IMAGE_FULL = imageTag
                    echo "Image tag stored: ${env.DOCKER_IMAGE_FULL}"
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            agent any
            steps {
                script {
                    // Create namespace if it doesn't exist (though Terraform should have created it)
                    sh """
                        kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                        
                        # Apply application manifests if first deployment
                        if ! kubectl get deployment ace-fitness-app -n ${K8S_NAMESPACE} 2>/dev/null; then
                            echo "First deployment - applying deployment and ingress manifests"
                            kubectl apply -f infrastructure/k8s/manifest_files/app/deployment.yaml
                            kubectl apply -f infrastructure/k8s/manifest_files/app/ingress.yaml
                        fi
                        
                        # Update the deployment with the new image
                        kubectl set image deployment/ace-fitness-app ace-fitness-app=${env.DOCKER_IMAGE_FULL} -n ${K8S_NAMESPACE}
                        kubectl rollout status deployment/ace-fitness-app -n ${K8S_NAMESPACE} --timeout=300s
                        
                        # Verify deployment
                        kubectl get pods -n ${K8S_NAMESPACE}
                        kubectl get services -n ${K8S_NAMESPACE}
                        
                        # Show access information
                        APP_IP=\$(kubectl get service ace-fitness-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
                        echo "Application will be accessible at: http://\${APP_IP}"
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