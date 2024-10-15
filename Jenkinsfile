pipeline {
    agent any
    triggers {
        // This trigger will run the pipeline when a PR is created or updated
        githubPullRequest()
    }
    environment {
        REPO_URL = 'https://github.com/sc-ajagup/Jenkins-POC.git'
    }
    stages {
        stage('Checkout') {
            steps {
                // Check out the code from the PR branch
                checkout scm
            }
        }
        stage('Unit Tests') {
            steps {
                // Run your unit tests with coverage
                sh 'coverage run -m unittest discover -s tests'
                // Generate a coverage report
                sh 'coverage report -m'
            }
        }
    }
    post {
        always {
            echo 'Cleaning up workspace...'
            cleanWs()
        }
        success {
            echo 'All tests passed successfully.'
        }
        failure {
            echo 'One or more tests failed.'
        }
    }
}
