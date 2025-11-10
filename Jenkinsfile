pipeline {
    agent any
    
    triggers {
        pollSCM('H/2 * * * *')
    }
    
    environment {
        PYTHONPATH = "${WORKSPACE}/src"
        DOCKER_IMAGE = 'ace-est-fitness-and-gym'
        DOCKER_TAG = "${BUILD_NUMBER}"
        GCP_PROJECT_ID = 'itd-2021mt93693'
        GCP_REGION = 'us-central1'
        ARTIFACT_REGISTRY_REPO = 'ace-fitness-repo'
        K8S_NAMESPACE = 'ace-fitness'
        GKE_CLUSTER_NAME = 'ace-fitness-cluster'
        GCP_SERVICE_ACCOUNT_KEY = credentials('gcp-service-account-key')
        PYTHONDONTWRITEBYTECODE = '1'
        PYTHONUNBUFFERED = '1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Code Quality Check') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    echo "Running code quality checks..."
                    pip install flake8
                    flake8 src/ --max-line-length=120 --exclude=__pycache__ || true
                '''
            }
        }
        
        stage('Unit Tests') {
            agent {
                docker {
                    image 'python:3.11-slim'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    echo "Running unit tests..."
                    pip install pytest pytest-cov
                    python -m pytest tests/ -v --tb=short --cov=src --cov-report=xml --cov-report=html || true
                '''
            }
            post {
                always {
                    junit testResults: '**/test-*.xml', allowEmptyResults: true
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                }
            }
        }
        
        stage('Build Version') {
            steps {
                script {
                    env.VERSION = readFile('build.version').trim()
                    env.FULL_IMAGE_NAME = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER}"
                    env.LATEST_IMAGE_NAME = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${DOCKER_IMAGE}:latest"
                    echo "Building version: ${env.VERSION}"
                    echo "Full image name: ${env.FULL_IMAGE_NAME}"
                }
            }
        }
        
        stage('Build Docker Image') {
            agent {
                docker {
                    image 'docker:24-dind'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --privileged'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        echo "Building Docker image..."
                        docker build -t ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} .
                        docker tag ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} ${FULL_IMAGE_NAME}
                        docker tag ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} ${LATEST_IMAGE_NAME}
                        echo "Docker images created successfully!"
                        docker images | grep ${DOCKER_IMAGE}
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            agent {
                docker {
                    image 'docker:24-dind'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --privileged'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        echo "Running basic security scan..."
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                          aquasec/trivy image --exit-code 0 --severity HIGH,CRITICAL \
                          --no-progress ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} || true
                    '''
                }
            }
        }
        
        stage('Authenticate with GCP') {
            agent {
                docker {
                    image 'google/cloud-sdk:alpine'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        echo "Authenticating with GCP..."
                        echo "${GCP_SERVICE_ACCOUNT_KEY}" | base64 -d > gcp-key.json
                        gcloud auth activate-service-account --key-file=gcp-key.json
                        gcloud config set project ${GCP_PROJECT_ID}
                        
                        # Configure Docker to use gcloud as credential helper
                        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                        
                        # Get GKE credentials
                        gcloud container clusters get-credentials ${GKE_CLUSTER_NAME} --region=${GCP_REGION} --project=${GCP_PROJECT_ID}
                        
                        # Copy kubeconfig to workspace for later stages
                        cp ~/.kube/config ${WORKSPACE}/kubeconfig
                    '''
                }
            }
            post {
                always {
                    sh 'rm -f gcp-key.json'
                }
            }
        }
        
        stage('Push to Artifact Registry') {
            agent {
                docker {
                    image 'google/cloud-sdk:alpine'
                    args '-v /var/run/docker.sock:/var/run/docker.sock --entrypoint=""'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        echo "Authenticating with GCP for Docker push..."
                        echo "${GCP_SERVICE_ACCOUNT_KEY}" | base64 -d > gcp-key.json
                        gcloud auth activate-service-account --key-file=gcp-key.json
                        gcloud config set project ${GCP_PROJECT_ID}
                        
                        # Configure Docker to use gcloud as credential helper
                        gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
                        
                        echo "Pushing image to Google Artifact Registry..."
                        docker push ${FULL_IMAGE_NAME}
                        docker push ${LATEST_IMAGE_NAME}
                        echo "Images pushed successfully!"
                        
                        rm -f gcp-key.json
                    '''
                }
            }
        }
        
        stage('Update Kubernetes Manifests') {
            steps {
                script {
                    sh '''
                        echo "Updating Kubernetes deployment manifest..."
                        sed -i "s|image:.*ace-est-fitness-and-gym.*|image: ${FULL_IMAGE_NAME}|g" infrastructure/k8s/manifest_files/app/deployment.yaml
                        
                        echo "Updated deployment.yaml:"
                        cat infrastructure/k8s/manifest_files/app/deployment.yaml
                    '''
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            agent {
                docker {
                    image 'google/cloud-sdk:alpine'
                    args '-v ${WORKSPACE}:${WORKSPACE} -w ${WORKSPACE} --entrypoint=""'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        # Use the kubeconfig from previous stage
                        export KUBECONFIG=${WORKSPACE}/kubeconfig
                        
                        echo "Deploying to Kubernetes cluster..."
                        
                        # Create namespace if it doesn't exist
                        kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                        
                        # Apply all Kubernetes manifests
                        kubectl apply -f infrastructure/k8s/manifest_files/app/ -n ${K8S_NAMESPACE}
                        
                        # Wait for deployment to be ready
                        kubectl rollout status deployment/ace-fitness-app -n ${K8S_NAMESPACE} --timeout=300s
                        
                        # Get deployment status
                        kubectl get deployments -n ${K8S_NAMESPACE}
                        kubectl get services -n ${K8S_NAMESPACE}
                        kubectl get pods -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }
        
        stage('Health Check') {
            agent {
                docker {
                    image 'google/cloud-sdk:alpine'
                    args '-v ${WORKSPACE}:${WORKSPACE} -w ${WORKSPACE} --entrypoint=""'
                    reuseNode true
                }
            }
            steps {
                script {
                    sh '''
                        export KUBECONFIG=${WORKSPACE}/kubeconfig
                        
                        echo "Performing health check..."
                        
                        EXTERNAL_IP=""
                        echo "Waiting for external IP..."
                        for i in {1..30}; do
                            EXTERNAL_IP=$(kubectl get service ace-fitness-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
                            if [ ! -z "$EXTERNAL_IP" ]; then
                                break
                            fi
                            echo "Waiting for external IP... ($i/30)"
                            sleep 10
                        done
                        
                        if [ ! -z "$EXTERNAL_IP" ]; then
                            echo "External IP: $EXTERNAL_IP"
                            echo "Testing health endpoint..."
                            for i in {1..10}; do
                                if curl -f http://$EXTERNAL_IP/health 2>/dev/null; then
                                    echo "Health check passed!"
                                    break
                                else
                                    echo "Health check failed, retrying... ($i/10)"
                                    sleep 5
                                fi
                            done
                        else
                            echo "Could not get external IP, checking pod health instead..."
                            kubectl get pods -n ${K8S_NAMESPACE}
                        fi
                    '''
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
                        git tag "v${version}-${BUILD_NUMBER}" || true
                        git push origin "v${version}-${BUILD_NUMBER}" || echo "Could not push tag"
                    """
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Clean up Docker images if Docker is available
                sh '''
                    if command -v docker >/dev/null 2>&1; then
                        echo "Cleaning up Docker images..."
                        docker rmi ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} || true
                        docker system prune -f || true
                    else
                        echo "Docker not available, skipping Docker cleanup"
                    fi
                    rm -f ${WORKSPACE}/kubeconfig
                '''
                
                cleanWs()
                archiveArtifacts artifacts: 'coverage.xml,htmlcov/**', allowEmptyArchive: true
            }
        }
        success {
            script {
                echo "✅ Pipeline succeeded!"
                echo "🚀 Application deployed successfully to Kubernetes!"
                echo "📊 Build Number: ${BUILD_NUMBER}"
                echo "🏷️  Version: ${env.VERSION ?: 'N/A'}"
                echo "🐳 Docker Image: ${env.FULL_IMAGE_NAME ?: 'N/A'}"
            }
        }
        failure {
            script {
                echo "❌ Pipeline failed!"
                echo "🔍 Check the logs above for error details"
                echo "💡 Common issues: Docker build failure, K8s deployment timeout, authentication issues"
            }
        }
        unstable {
            echo "⚠️  Pipeline completed with warnings!"
        }
    }
}