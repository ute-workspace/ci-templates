// SonarQube analysis of this repository. SonarQube is internal and is reached
// only from Jenkins, so this pipeline runs it; the required check stays the
// GitHub Actions workflow validate.yml (linters and tests).
@Library('jenkins-library') _

pipeline {
  // Isolated agents only: no fallback to the controller's built-in node.
  agent { label 'ci-standard' }
  options {
    disableConcurrentBuilds(abortPrevious: true)
    // Bounds the wait for a free agent and the run itself.
    timeout(time: 45, unit: 'MINUTES')
  }
  stages {
    stage('Copied agent standards') {
      steps { copiedAgentStandardsCheck() }
    }

    stage('Secret scan') {
      steps { secretScan() }
    }

    stage('Tests') {
      steps {
        // The same unit and workflow integration tests as validate.yml, in a
        // container that has Python 3.13 and git; --user keeps the files it
        // writes owned by the agent user.
        sh """#!/usr/bin/env bash
          set -euo pipefail
          docker run --rm --user "\$(id -u):\$(id -g)" -e HOME=/tmp \\
            -v "\$WORKSPACE:/workspace" -w /workspace python:3.13-bookworm sh -lc '
            pip install --quiet --user PyYAML==6.0.2
            git config --global --add safe.directory "*"
            python3 -m unittest discover -s tests -v
          '
        """
      }
    }

    stage('SonarQube analysis') {
      steps { sonarQubeScan() }
    }
  }
}
