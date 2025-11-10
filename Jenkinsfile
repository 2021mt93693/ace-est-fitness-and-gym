pipeline {
    agent any
    
    triggers {
        // Poll SCM every 2 minutes to detect changes
        pollSCM('H/2 * * * *')
    }
    
    tools {
        // Ensure Docker is available
        dockerTool 'docker'
    }
    
    environment {
        PYTHONPATH = "${WORKSPACE}/src"
        DOCKER_IMAGE = 'ace-est-fitness-and-gym'
        DOCKER_TAG = "${BUILD_NUMBER}"
        GCP_PROJECT_ID = 'itd-2021mt93693'  // Your project ID
        GCP_REGION = 'us-central1'
        ARTIFACT_REGISTRY_REPO = 'ace-fitness-repo'
        K8S_NAMESPACE = 'ace-fitness'
        GKE_CLUSTER_NAME = 'ace-fitness-cluster'
        GCP_SERVICE_ACCOUNT_KEY = credentials('gcp-service-account-key')  // Add this credential in Jenkins
        
        // Disable Python bytecode generation for cleaner builds
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
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Code Quality Check') {
            steps {
                sh '''
                    echo "Running code quality checks..."
                    flake8 src/ --max-line-length=120 --exclude=__pycache__ || true
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    echo "Running unit tests..."
                    cd ${WORKSPACE}
                    python -m pytest tests/ -v --tb=short --cov=src --cov-report=xml --cov-report=html
                '''
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'test-results.xml', allowEmptyResults: true
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
            steps {
                script {
                    sh '''
                        echo "Building Docker image..."
                        docker build -t ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} .
                        docker tag ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} ${FULL_IMAGE_NAME}
                        docker tag ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} ${LATEST_IMAGE_NAME}
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    sh '''
                        echo "Running basic security scan..."
                        # Simple vulnerability check - can be enhanced with tools like Trivy
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                          aquasec/trivy image --exit-code 0 --severity HIGH,CRITICAL \
                          --no-progress ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} || true
                    '''
                }
            }
        }
        
        stage('Authenticate with GCP') {
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
            steps {
                sh '''
                    echo "Pushing image to Google Artifact Registry..."
                    docker push ${FULL_IMAGE_NAME}
                    docker push ${LATEST_IMAGE_NAME}
                '''
            }
        }
        
        stage('Update Kubernetes Manifests') {
            steps {
                script {
                    sh '''
                        echo "Updating Kubernetes deployment manifest..."
                        # Update the image in deployment.yaml
                        sed -i "s|image: ace-est-fitness-and-gym:latest|image: ${FULL_IMAGE_NAME}|g" infrastructure/k8s/manifest_files/app/deployment.yaml
                        
                        # Show the updated manifest
                        echo "Updated deployment.yaml:"
                        cat infrastructure/k8s/manifest_files/app/deployment.yaml
                    '''
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh '''
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
            steps {
                script {
                    sh '''
                        echo "Performing health check..."
                        
                        # Get the external IP of the service
                        EXTERNAL_IP=""
                        echo "Waiting for external IP..."
                        for i in {1..30}; do
                            EXTERNAL_IP=$(kubectl get service ace-fitness-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
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
                                if curl -f http://$EXTERNAL_IP/health; then
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
                        git tag "v${version}-${BUILD_NUMBER}"
                        git push origin "v${version}-${BUILD_NUMBER}"
                    """
                }
            }
        }
    }

    
    post {
        always {
            script {
                // Clean up Docker images to save space
                sh '''
                    echo "Cleaning up Docker images..."
                    docker rmi ${DOCKER_IMAGE}:${VERSION}-${BUILD_NUMBER} || true
                    docker system prune -f || true
                '''
                
                // Clean workspace
                cleanWs()
                
                // Archive test results if they exist
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
                
                // Send notification (can be customized for Slack, email, etc.)
                // slackSend channel: '#deployments', 
                //          color: 'good', 
                //          message: "✅ ACE Fitness App deployed successfully!\nVersion: ${env.VERSION ?: 'N/A'}\nBuild: ${BUILD_NUMBER}"
            }
        }
        failure {
            script {
                echo "❌ Pipeline failed!"
                echo "🔍 Check the logs above for error details"
                echo "💡 Common issues: Docker build failure, K8s deployment timeout, authentication issues"
                
                // Send failure notification
                // slackSend channel: '#deployments', 
                //          color: 'danger', 
                //          message: "❌ ACE Fitness App deployment failed!\nBuild: ${BUILD_NUMBER}\nCheck: ${BUILD_URL}"
            }
        }
        unstable {
            echo "⚠️  Pipeline completed with warnings!"
        }
    }
}