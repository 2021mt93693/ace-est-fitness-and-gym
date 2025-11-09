pipeline {
    agent any
    
    environment {
        PYTHONPATH = "${WORKSPACE}/src"
        DOCKER_IMAGE = 'ace-est-fitness-and-gym'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install flake8 pytest coverage pytest-cov
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }
        
        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
                    pytest --cov=src --cov-report=xml --cov-report=term tests/
                '''
            }
            post {
                always {
                    // Archive test results
                    publishTestResults testResultsPattern: 'coverage.xml'
                    
                    // Archive coverage report
                    archiveArtifacts artifacts: 'coverage.xml', fingerprint: true
                    
                    // Display coverage summary
                    sh '. venv/bin/activate && coverage report'
                }
            }
        }
        
        stage('Docker Build') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}")
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