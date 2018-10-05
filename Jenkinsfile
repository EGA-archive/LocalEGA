pipeline {
  agent any
  stages {
    stage('Unit tests') {
      agent {
        docker {
          image 'painless/tox'
        }

      }
      steps {
        sh 'tox'
      }
    }
  }
}