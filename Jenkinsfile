pipeline {
    agent any

    environment {
        REGISTRY         = 'jessimey'
        APP_NAME         = 'group5-banking-app'
        IMAGE            = 'jessimey/group5-banking-app'
        TAG              = "${env.GIT_COMMIT.take(7)}"
        
        // Target EC2 Details (Update TARGET_EC2_IP if the banking EC2 IP is different)
        TARGET_EC2_IP    = '34.234.163.173'
        TARGET_EC2_USER  = 'ubuntu'
        CONTAINER_PORT   = '5000'
        HOST_PORT        = '5001'
        
        // Jenkins Credentials IDs
        DOCKER_HUB_CREDS = 'docker-hub-credentials'
        SSH_KEY_CREDS    = 'webserver-banking-ssh'
    }

    stages {
        stage('Build & Unit Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --no-cache-dir -r requirements.txt pytest
                    pytest || [ $? -eq 5 ]
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest ."
            }
        }

        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${DOCKER_HUB_CREDS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh "docker push ${IMAGE}:${TAG}"
                    sh "docker push ${IMAGE}:latest"
                }
            }
        }

        stage('Deploy to EC2 Host') {
            steps {
                sshagent(["${SSH_KEY_CREDS}"]) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${TARGET_EC2_USER}@${TARGET_EC2_IP} "
                            docker pull ${IMAGE}:${TAG}
                            docker rm -f ${APP_NAME} 2>/dev/null || true
                            docker run -d --name ${APP_NAME} --restart always -p ${HOST_PORT}:${CONTAINER_PORT} ${IMAGE}:${TAG}
                            docker image prune -f
                        "
                    """
                }
            }
        }

        stage('Smoke Test') {
            steps {
                sh "sleep 5"
                sh "curl --fail http://${TARGET_EC2_IP}:${HOST_PORT}/pay || exit 1"
            }
        }
    }

    post {
        always {
            sh "docker rmi ${IMAGE}:${TAG} ${IMAGE}:latest || true"
        }
    }
}
