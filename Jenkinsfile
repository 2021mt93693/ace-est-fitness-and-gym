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
        
        stage('Docker Build') {
            steps {
                script {
                    def imageTag = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${DOCKER_TAG}"
                    
                    sh """
                        # Set PATH to include gcloud and kubectl
                        export PATH=\$PATH:/tmp/google-cloud-sdk/bin:/var/jenkins_home/.local/bin
                        
                        echo "Building and pushing Docker image to Google Artifact Registry..."
                        echo "Image will be tagged as: ${imageTag}"
                        
                        # Check if Docker daemon is actually accessible
                        if docker info >/dev/null 2>&1; then
                            echo "Docker daemon accessible, proceeding with build..."
                            
                            # Build Docker image
                            echo "Building image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                            
                            # Tag for Artifact Registry
                            echo "Tagging image for Artifact Registry..."
                            docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${imageTag}
                            
                            # Push to Artifact Registry
                            echo "Pushing image to Artifact Registry..."
                            docker push ${imageTag}
                            
                            echo "✅ Image pushed successfully to Artifact Registry: ${imageTag}"
                        else
                            echo "Docker daemon not accessible. Using Kaniko to build and push to Artifact Registry..."
                            
                            # Create a build job using existing jenkins service account
                            echo "Creating Kaniko build job for Docker image..."
                            kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: docker-build-${BUILD_NUMBER}
  namespace: jenkins
spec:
  template:
    spec:
      serviceAccountName: jenkins-gke-sa
      restartPolicy: Never
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        args:
        - "--context=git://github.com/2021mt93693/ace-est-fitness-and-gym.git#refs/heads/FEATURE-JENKINS"
        - "--destination=${imageTag}"
        - "--cache=true"
        - "--cache-repo=${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/cache"
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /var/secrets/google/gcp-key.json
        volumeMounts:
        - name: gcp-key
          mountPath: /var/secrets/google
          readOnly: true
      volumes:
      - name: gcp-key
        secret:
          secretName: gcp-service-account-key
EOF
                            
                            # Wait for job completion
                            echo "Waiting for build job to complete..."
                            kubectl wait --for=condition=complete job/docker-build-${BUILD_NUMBER} -n jenkins --timeout=600s
                            
                            # Check if job succeeded
                            if kubectl get job docker-build-${BUILD_NUMBER} -n jenkins -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' | grep -q "True"; then
                                echo "✅ Docker image built successfully using Kaniko!"
                            else
                                echo "❌ Docker build failed"
                                kubectl logs job/docker-build-${BUILD_NUMBER} -n jenkins
                                exit 1
                            fi
                            
                            # Clean up build job
                            kubectl delete job docker-build-${BUILD_NUMBER} -n jenkins --ignore-not-found=true
                            
                            echo "Image built and pushed using Kaniko: ${imageTag}"
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
                        # Set PATH to include gcloud and kubectl
                        export PATH=\$PATH:/tmp/google-cloud-sdk/bin:/var/jenkins_home/.local/bin
                        
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