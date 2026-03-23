pipeline {
    agent any

    stages {

        stage('Checkout Code') {
            steps {
                git(
                    branch: 'main',
                    credentialsId: 'github-jenkins',
                    url: 'https://github.com/ParvezThabarak/secure-file-locker.git'
                )
            }
        }

        stage('Test Stage') {
            steps {
                bat 'echo Jenkins CI Working Successfully'
            }
        }
    }
}
