pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent {
        docker {
          image 'python:3.7'
        }

      }
      steps {
        sh '''pip install tox
tox'''
      }
    }
  }
}