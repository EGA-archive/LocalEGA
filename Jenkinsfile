pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent any
      steps {
        sh '''docker ps
pip install tox
tox'''
      }
    }
  }
}