pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent any
      steps {
        dockerNode(dockerHost: 'unix:///var/run/docker.sock', image: 'nbisweden/os') {
          sh '''pip install tox
tox'''
        }

      }
    }
  }
}