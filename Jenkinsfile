pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent {
        docker {
          image 'patrick91/docker-tox'
        }

      }
      steps {
        sh 'tox'
      }
    }
  }
}