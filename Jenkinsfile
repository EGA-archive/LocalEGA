pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent {
        docker {
          image 'n42org/tox'
        }

      }
      steps {
        sh '''python --version
pip --version
tox'''
      }
    }
  }
}