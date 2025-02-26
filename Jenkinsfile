import groovy.json.JsonSlurper

def BUILD_SUMMARY = new StringBuffer()

pipeline {
    agent any

    
    options {
        timestamps()
        // Add timeout to prevent hanging builds
        timeout(time: 60, unit: 'MINUTES')
        // Discard old builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        CHANGED_FILES = ''
        IS_PR_VALID = sh(
            script: '[[ "${target_branch}" == "main" && ("${action}" == "opened" || "${action}" == "reopened") ]] && echo "true" || echo "false"',
            returnStdout: true
        ).trim()

        // Default values to avoid null pointer exceptions
        REQUESTOR_EMAIL = ''
        ALL_EMAILS = ''

        GIT_URL = "https://github.com/sc-lovpre/Jenkins-POC.git"
        GIT_CREDENTIALS = 'github-credentials'
        GIT_API_URL = "https://api.github.com/repos/sc-lovpre/Jenkins-POC/"
        GIT_TO_USER_EMAIL_PATH = "${JENKINS_HOME}/email.json"
        
        requestor = "${requestor_user_name ?: ''}"
        repo = "${repo ?: ''}"
        OUTPUT_FILE = "${WORKSPACE}/logs/${repo ?: 'unknown'}_log.txt"
        PR_NUMBER = "${pr_number ?: ''}"
        commit_sha = "${commit_sha ?: ''}"
        source_branch = "${source_branch ?: ''}"
        target_branch = "${target_branch ?: ''}"
        action = "${action ?: ''}"
        requested_reviewers = "${requested_reviewers ?: '[]'}"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // Create logs directory if it doesn't exist
                    sh "mkdir -p ${WORKSPACE}/logs"
                    
                    // Log all parameters for debugging
                    def paramsLog = "Pipeline Parameters:\n"
                    each { key, value ->
                        paramsLog += "${key}: ${value}\n"
                    }
                    echo paramsLog
                    echo "PR Number is ${pr_number}"
                    echo "PR Number is ${PR_NUMBER}"
                    
                    // Add validation for required parameters
                    if (!PR_NUMBER || !commit_sha || !source_branch || !target_branch) {
                        error "Missing required parameters. PR_NUMBER: ${PR_NUMBER}, commit_sha: ${commit_sha}, source_branch: ${source_branch}, target_branch: ${target_branch}"
                    }
                }
            }
        }

        stage('Checkout') {
            when {
                expression { return IS_PR_VALID == 'true' }
            }
            steps {
                script {
                    BUILD_SUMMARY.append("Source Branch: ${source_branch}\n")
                    BUILD_SUMMARY.append("Target Branch: ${target_branch}\n")
                }
                checkout scmGit(
                    branches: [[name: "*/${source_branch}"]],
                    userRemoteConfigs: [[credentialsId: GIT_CREDENTIALS, url: GIT_URL]]
                )
            }
        }

        stage('Get Email from Git User') {
            when {
                expression { return IS_PR_VALID == 'true' }
            }
            steps {
                script {
                    try {
                        echo "Repo is: ${repo}"
                        echo "Requestor is: ${requestor}"
                        
                        sh "rm -f ${OUTPUT_FILE} && touch ${OUTPUT_FILE}"
                        
                        // Validate that the email mapping file exists
                        if (!fileExists(GIT_TO_USER_EMAIL_PATH)) {
                            error "Email mapping file not found at: ${GIT_TO_USER_EMAIL_PATH}"
                        }
                        
                        def gitUserEmail = readFile(GIT_TO_USER_EMAIL_PATH)
                        def emailData = new JsonSlurper().parseText(gitUserEmail)
                        
                        // Set default email if requestor not found in mapping
                        REQUESTOR_EMAIL = emailData[requestor] ?: 'jenkins@example.com'
                        ALL_EMAILS = REQUESTOR_EMAIL
                        
                        // Safely parse requested reviewers JSON
                        def parsedReviewers = []
                        try {
                            parsedReviewers = new JsonSlurper().parseText(requested_reviewers)
                        } catch (Exception e) {
                            echo "Warning: Could not parse requested_reviewers: ${e.message}"
                            parsedReviewers = []
                        }
                        
                        // Add reviewers' emails
                        for (gitUser in parsedReviewers) {
                            def userEmail = emailData[gitUser]
                            if (userEmail) {
                                ALL_EMAILS = ALL_EMAILS + ',' + userEmail
                            }
                        }
                        
                        // Log environment details
                        def outputFileContent = """
                        All Emails: ${ALL_EMAILS}
                        Requestor Email: ${REQUESTOR_EMAIL}
                        PR State: ${state ?: 'Unknown'}
                        Sender: ${requestor}
                        Requested Reviewers: ${requested_reviewers}
                        Source Branch: ${source_branch}
                        Target Branch: ${target_branch}
                        Action: ${action}
                        Commit SHA: ${commit_sha}
                        GIT API URL: ${GIT_API_URL}
                        Git URL: ${GIT_URL}
                        """
                        writeFile file: OUTPUT_FILE, text: outputFileContent
                    } catch (Exception e) {
                        echo "Error in Environment setup: ${e.message}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Fetch Changed Files') {
            when {
                expression { return IS_PR_VALID == 'true' }
            }
            steps {
                script {
                    try {
                        withCredentials([string(credentialsId: 'github-credentials-secret-text', variable: 'GITHUB_ACCESS_TOKEN')]) {
                            def suffix = "${GIT_API_URL}pulls/${PR_NUMBER}/files"
                            def curlCommand = """
                                curl -L -s \
                                -H 'Accept: application/vnd.github+json' \
                                -H 'Authorization: Bearer ${GITHUB_ACCESS_TOKEN}' \
                                -H 'X-GitHub-Api-Version: 2022-11-28' \
                                ${suffix}
                            """
                            def response = sh(script: curlCommand, returnStdout: true).trim()
                            
                            // Validate response before parsing
                            if (response) {
                                def jsonResponse = new JsonSlurper().parseText(response)
                                CHANGED_FILES = jsonResponse.collect { it.filename }
                                
                                // Filter files by extension
                                env.PY_FILES = CHANGED_FILES.findAll { it.endsWith('.py') }.join(',')
                                env.JS_FILES = CHANGED_FILES.findAll { it.endsWith('.js') }.join(',')
                                
                                echo "Changed Python files: ${env.PY_FILES}"
                                echo "Changed JavaScript files: ${env.JS_FILES}"
                            } else {
                                error "Empty response from GitHub API"
                            }
                        }
                    } catch (Exception e) {
                        echo "Error fetching changed files: ${e.message}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Set Build Status Pending') {
            when {
                expression { return IS_PR_VALID == 'true' }
            }
            steps {
                script {
                    updateGitHubStatus('pending', 'Jenkins job is running')
                }
            }
        }

        stage('Setup Python Environment') {
            when {
                expression { return IS_PR_VALID == 'true' }
            }
            steps {
                script {
                    try {
                        echo 'Setting up Python environment and installing dependencies'
                        
                        // Check Python version
                        sh 'python3 --version'
                        
                        // Create virtual environment if it doesn't exist
                        sh '''
                            if [ ! -d "venv" ]; then
                                python3 -m venv venv
                            fi
                        '''
                        
                        // Install dependencies
                        sh '''
                            source venv/bin/activate
                            pip install --upgrade pip
                            pip install coverage python-dotenv
                            pip freeze > requirements-lock.txt
                        '''
                    } catch (Exception e) {
                        echo "Error setting up Python environment: ${e.message}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Unit Tests') {
            when {
                expression { return IS_PR_VALID == 'true' && env.PY_FILES != '' }
            }
            steps {
                script {
                    try {
                        echo 'Running unit tests with coverage'
                        
                        sh '''
                            source venv/bin/activate
                            coverage run -m unittest discover -s tests
                            coverage report -m | tee coverage_report.txt
                            coverage xml -o coverage.xml
                        '''
                        
                        // Archive coverage reports
                        archiveArtifacts artifacts: 'coverage_report.txt,coverage.xml', allowEmptyArchive: true
                        
                        // Add test results to build summary
                        def coverageReport = readFile('coverage_report.txt')
                        BUILD_SUMMARY.append("\nTest Coverage:\n${coverageReport}\n")
                    } catch (Exception e) {
                        echo "Error running unit tests: ${e.message}"
                        BUILD_SUMMARY.append("\nTests FAILED: ${e.message}\n")
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (env.IS_PR_VALID == 'true') {
                    def buildStatus = currentBuild.currentResult
                    def emailText = """
                    Project: ${env.JOB_NAME}
                    Build Number: ${env.BUILD_NUMBER}
                    PR Number: ${PR_NUMBER}
                    URL of the build: ${env.BUILD_URL}
                    Build Status: ${buildStatus}
                    Summary:
                    ${BUILD_SUMMARY}
                    """
                    
                    // Ensure send_report.py exists
                    if (fileExists('send_report.py')) {
                        try {
                            sh """
                                source venv/bin/activate
                                python send_report.py \
                                    "${ALL_EMAILS ?: 'jenkins@example.com'}" \
                                    "${emailText.replaceAll('"', '\\"')}" \
                                    "${target_branch}" \
                                    "${source_branch}" \
                                    "${PR_NUMBER}"
                            """
                        } catch (Exception e) {
                            echo "Failed to send email report: ${e.message}"
                        }
                    } else {
                        echo "Warning: send_report.py not found"
                    }
                    
                    // Update GitHub status
                    updateGitHubStatus(
                        currentBuild.result == 'SUCCESS' ? 'success' : 'failure',
                        currentBuild.result == 'SUCCESS' ? 'Build succeeded' : 'Build failed'
                    )
                }
            }
            
            // Cleanup workspace
            cleanWs(
                cleanWhenNotBuilt: true,
                deleteDirs: true,
                patterns: [
                    [pattern: 'venv/', type: 'EXCLUDE'],
                    [pattern: '*.log', type: 'INCLUDE'],
                    [pattern: 'logs/', type: 'INCLUDE']
                ]
            )
        }
    }
}

// Helper function to update GitHub status
def updateGitHubStatus(String state, String description) {
    try {
        withCredentials([string(credentialsId: 'github-credentials-secret-text', variable: 'GITHUB_ACCESS_TOKEN')]) {
            def data = """
            {
                "state":"${state}",
                "target_url":"${env.BUILD_URL}",
                "description":"${description}",
                "context":"continuous-integration/jenkins"
            }
            """
            def suffix = "${GIT_API_URL}statuses/${commit_sha}"
            def curlCommand = """
                curl -L -s -X POST \
                -H 'Accept: application/vnd.github+json' \
                -H 'Authorization: Bearer ${GITHUB_ACCESS_TOKEN}' \
                -H 'X-GitHub-Api-Version: 2022-11-28' \
                ${suffix} -d '${data}'
            """
            def response = sh(script: curlCommand, returnStatus: true)
            
            if (response != 0) {
                echo "Failed to update GitHub status. HTTP Status Code: ${response}"
                return false
            }
            return true
        }
    } catch (Exception e) {
        echo "Error updating GitHub status: ${e.message}"
        return false
    }
}
