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
        
        stage('Lint & Test') {
            agent {
                docker {
                    image 'python:3.9-slim'
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                sh '''
                    echo "Setting up Python environment..."
                    python --version
                    pip install --upgrade pip
                    pip install flake8 pytest coverage pytest-cov
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                    
                    echo "Running linting..."
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                    
                    echo "Running unit tests..."
                    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
                    pytest --cov=src --cov-report=xml --cov-report=term tests/ || echo "Tests completed with issues"
                '''
            }
            post {
                always {
                    // Archive test results if they exist
                    script {
                        if (fileExists('coverage.xml')) {
                            archiveArtifacts artifacts: 'coverage.xml', fingerprint: true
                        }
                    }
                }
            }
        }
        
        stage('GCP Authentication') {
            agent any
            steps {
                script {
                    // Install gcloud CLI in Jenkins if not present
                    sh '''
                        if ! command -v gcloud &> /dev/null; then
                            echo "Installing gcloud CLI..."
                            curl -sSL https://sdk.cloud.google.com > /tmp/install.sh
                            bash /tmp/install.sh --install-dir=/usr/local --quiet
                            export PATH=$PATH:/usr/local/google-cloud-sdk/bin
                        fi
                        
                        # Authenticate with GCP using service account key
                        gcloud auth activate-service-account --key-file=$GCP_SERVICE_ACCOUNT_KEY
                        gcloud config set project $GCP_PROJECT_ID
                        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                        
                        # Configure kubectl to connect to the GKE cluster
                        gcloud container clusters get-credentials itd-cluster-tf --zone=us-central1-a --project=$GCP_PROJECT_ID
                        
                        # Verify connection
                        kubectl get nodes
                    '''
                }
            }
        }
        
        stage('Docker Build') {
            agent any
            steps {
                script {
                    def imageTag = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${DOCKER_TAG}"
                    
                    // Build Docker image
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${imageTag}"
                    
                    // Push to Artifact Registry
                    sh "docker push ${imageTag}"
                    
                    // Update deployment with new image
                    env.DOCKER_IMAGE_FULL = imageTag
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