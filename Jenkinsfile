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
                bat '"C:\Users\parve\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt'
            }
        }

        stage('Run Application') {
            steps {
                bat '"C:\Users\parve\AppData\Local\Programs\Python\Python312\python.exe" app.py'
            }
        }
    }
}
