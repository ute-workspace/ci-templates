// SonarQube analysis of this repository. SonarQube is internal and is reached
// only from Jenkins, so this pipeline runs it; the required check stays the
// GitHub Actions workflow validate.yml (linters and tests).
@Library('jenkins-library') _

pipeline {
  // Falls back to the controller's built-in node when the ci-standard
  // pool has no free agent, instead of queuing indefinitely.
  agent { label 'ci-standard || built-in' }
  stages {
    stage('Copied agent standards') {
      steps { copiedAgentStandardsCheck() }
    }

    stage('Secret scan') {
      steps { secretScan() }
    }

    stage('SonarQube analysis') {
      steps { sonarQubeScan() }
    }
  }
}
