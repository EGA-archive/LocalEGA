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
        sh '''pip install tox
tox'''
      }
    }
  }
}