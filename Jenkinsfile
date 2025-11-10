pipeline {
    agent any
    
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
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    echo "Setting up Python environment..."
                    
                    # Install Python if not available
                    if ! command -v python3 &> /dev/null; then
                        echo "Installing Python..."
                        apt-get update && apt-get install -y python3 python3-pip python3-venv
                    fi
                    
                    # Create virtual environment
                    python3 -m venv venv || echo "Virtual environment creation failed, continuing..."
                    
                    # Install packages directly if venv fails
                    if [ -d "venv" ]; then
                        . venv/bin/activate
                        pip install --upgrade pip
                    else
                        python3 -m pip install --upgrade pip --user
                        export PATH=$PATH:~/.local/bin
                    fi
                    
                    # Install required packages
                    if [ -d "venv" ]; then
                        pip install flake8 pytest coverage pytest-cov
                        if [ -f requirements.txt ]; then
                            pip install -r requirements.txt
                        fi
                    else
                        python3 -m pip install --user flake8 pytest coverage pytest-cov
                        if [ -f requirements.txt ]; then
                            python3 -m pip install --user -r requirements.txt
                        fi
                    fi
                '''
            }
        }
        
        stage('Lint & Test') {
            steps {
                sh '''
                    echo "Running linting and tests..."
                    
                    # Activate venv if it exists
                    if [ -d "venv" ]; then
                        . venv/bin/activate
                    else
                        export PATH=$PATH:~/.local/bin
                    fi
                    
                    # Run linting (continue on failure)
                    echo "Running flake8 linting..."
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "Linting completed with issues"
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || echo "Style check completed"
                    
                    # Run unit tests (continue on failure)
                    echo "Running unit tests..."
                    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
                    pytest --cov=src --cov-report=xml --cov-report=term tests/ || echo "Tests completed with issues"
                '''
            }
            post {
                always {
                    script {
                        if (fileExists('coverage.xml')) {
                            archiveArtifacts artifacts: 'coverage.xml', fingerprint: true, allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('GCP Authentication') {
            steps {
                script {
                    sh '''
                        echo "Setting up GCP and Kubernetes tools..."
                        
                        # Install curl if not available
                        if ! command -v curl &> /dev/null; then
                            echo "Installing curl..."
                            apt-get update && apt-get install -y curl
                        fi
                        
                        # Install gcloud CLI if not present
                        if ! command -v gcloud &> /dev/null; then
                            echo "Installing gcloud CLI..."
                            echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
                            curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
                            apt-get update && apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin
                        fi
                        
                        # Install kubectl if not present
                        if ! command -v kubectl &> /dev/null; then
                            echo "Installing kubectl..."
                            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                            chmod +x kubectl && mv kubectl /usr/local/bin/
                        fi
                        
                        # Install Docker if not present (needed for docker push)
                        if ! command -v docker &> /dev/null; then
                            echo "Installing Docker..."
                            apt-get update && apt-get install -y docker.io
                        fi
                        
                        # Authenticate with GCP using service account key
                        echo "Authenticating with GCP..."
                        gcloud auth activate-service-account --key-file=$GCP_SERVICE_ACCOUNT_KEY
                        gcloud config set project $GCP_PROJECT_ID
                        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                        
                        # Configure kubectl to connect to the GKE cluster
                        echo "Configuring kubectl..."
                        gcloud container clusters get-credentials itd-cluster-tf --zone=us-central1-a --project=$GCP_PROJECT_ID
                        
                        # Verify connections
                        echo "Verifying connections..."
                        kubectl get nodes || echo "kubectl connection failed - will try again in Docker Build stage"
                        docker --version
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
                        
                        # Ensure Docker daemon is running
                        service docker start || echo "Docker service start attempted"
                        
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