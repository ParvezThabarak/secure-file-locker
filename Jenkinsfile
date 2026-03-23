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

        stage('Install Dependencies') {
            steps {
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Run Application') {
            steps {
                bat 'python app.py'
            }
        }
    }
}
