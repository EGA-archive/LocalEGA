pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent {
        docker {
          image 'python:3.5.1'
        }

      }
      steps {
        sh '''sudo pip install tox
tox'''
      }
    }
  }
}