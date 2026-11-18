pipeline {
    agent any

    environment {
        AWS_CLI = '/var/lib/jenkins/.local/bin/aws'
        AWS_REGION = 'us-east-1'
        TARGET_INSTANCE = 'i-051b29c7854e0977c'
        APP_URL = 'http://34.207.235.9:8000'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/Heramb-Acharya/SupplyChainX.git'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    docker run --rm \
                        -v "$WORKSPACE:/app" \
                        -w /app \
                        python:3.12-slim \
                        sh -c "pip install --no-cache-dir -r requirements.txt && python -m pytest -v --cov=app --cov-report=term"
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t supplychainx:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy via AWS SSM') {
            steps {
                sh '''
                    set -e

                    COMMAND_ID=$($AWS_CLI ssm send-command \
                        --region "$AWS_REGION" \
                        --instance-ids "$TARGET_INSTANCE" \
                        --document-name "AWS-RunShellScript" \
                        --comment "SupplyChainX deployment from Jenkins build ${BUILD_NUMBER}" \
                        --parameters '{"commands":["set -e","cd /opt/supplychainx/source","git pull origin main","docker compose up -d --build","sleep 10","docker compose ps","curl -fsS http://127.0.0.1:8000/api/health"]}' \
                        --query 'Command.CommandId' \
                        --output text)

                    echo "SSM Command ID: $COMMAND_ID"

                    for i in $(seq 1 36); do
                        STATUS=$($AWS_CLI ssm get-command-invocation \
                            --region "$AWS_REGION" \
                            --command-id "$COMMAND_ID" \
                            --instance-id "$TARGET_INSTANCE" \
                            --query 'Status' \
                            --output text 2>/dev/null || echo Pending)

                        echo "Deployment status: $STATUS"

                        if [ "$STATUS" = "Success" ]; then
                            echo "Deployment completed successfully."
                            exit 0
                        fi

                        if [ "$STATUS" = "Failed" ] || [ "$STATUS" = "Cancelled" ] || [ "$STATUS" = "TimedOut" ]; then
                            $AWS_CLI ssm get-command-invocation \
                                --region "$AWS_REGION" \
                                --command-id "$COMMAND_ID" \
                                --instance-id "$TARGET_INSTANCE" \
                                --query '{Status:Status,Output:StandardOutputContent,Error:StandardErrorContent}' \
                                --output json
                            exit 1
                        fi

                        sleep 5
                    done

                    echo "Deployment timed out. Check SSM command status."
                    exit 1
                '''
            }
        }

        stage('Verify Live Application') {
            steps {
                sh '''
                    set -e
                    curl -fsS "$APP_URL/api/health"
                    echo
                    echo "SupplyChainX deployment verified."
                '''
            }
        }
    }

    post {
        success {
            echo 'SupplyChainX CI/CD pipeline completed successfully.'
        }
        failure {
            echo 'SupplyChainX CI/CD pipeline failed. Check the stage logs.'
        }
    }
}
