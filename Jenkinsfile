pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = '4ddocker'
        DOCKER_HUB_PASS = credentials('docker')
        IMAGE_NAME = "${DOCKER_HUB_USER}/lab1:${env.BUILD_NUMBER}"
        IMAGE_LATEST = "${DOCKER_HUB_USER}/lab1:latest"
    }

    stages {
        stage('Checkout') {
            steps {
                echo '📦 Клонирование репозитория из GitHub...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/prog-js/DevOPS_Lab1.git',
                        credentialsId: 'github-token'
                    ]]
                ])
                echo '✅ Код успешно получен'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🏗️ Сборка Docker образа...'
                bat "docker build -t ${IMAGE_NAME} ."
                bat "docker tag ${IMAGE_NAME} ${IMAGE_LATEST}"
                echo '✅ Образ собран'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo '📤 Публикация образа на Docker Hub...'
                bat "echo ${DOCKER_HUB_PASS} | docker login -u ${DOCKER_HUB_USER} --password-stdin"
                bat "docker push ${IMAGE_NAME}"
                bat "docker push ${IMAGE_LATEST}"
                bat "docker logout"
                echo '✅ Образ опубликован'
            }
        }

        stage('Test Container') {
            steps {
                echo '🧪 Запуск тестового контейнера...'
                bat """
                    docker run -d --name test-container -p 8888:8000 ${IMAGE_NAME}
                    timeout /t 10 /nobreak > nul
                    curl -f http://localhost:8888/health || exit 1
                    docker stop test-container
                    docker rm test-container
                """
                echo '✅ Контейнер успешно протестирован'
            }
        }
    }

    post {
        always {
            script {
                bat 'docker logout || true'
            }
        }
        success {
            echo '🎉 CI/CD Pipeline успешно выполнен!'
        }
        failure {
            echo '❌ Pipeline завершился с ошибкой. Проверьте логи выше.'
        }
    }
}