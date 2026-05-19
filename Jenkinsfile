pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "4ddocker/Lab1"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.build("${DOCKER_IMAGE}:latest")
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('', 'docker-hub-credentials') {
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                        docker.image("${DOCKER_IMAGE}:latest").push()
                    }
                }
            }
        }
        
        stage('Test Container') {
            steps {
                sh '''
                    docker run -d --name test-${BUILD_NUMBER} -p 8888:8000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                    sleep 10
                    curl -f http://localhost:8888/health || exit 1
                    docker stop test-${BUILD_NUMBER}
                    docker rm test-${BUILD_NUMBER}
                '''
            }
        }
    }
    
    post {
        success {
            echo "✅ Образ ${DOCKER_IMAGE}:${DOCKER_TAG} успешно загружен!"
        }
        failure {
            echo "❌ Сборка не удалась!"
        }
    }
}