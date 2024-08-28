import eo_install_jobs.defaults.Defaults

for (def job_name: [
        'eo-rv-capo-installation',
        'eo-rv-capo-installation-debug'
    ])

{
    freeStyleJob(job_name) {
        description Defaults.description("""<h2>Job for CAPO installation</h2>""")

        label Defaults.SLAVE
        logRotator(50, 200)
        concurrentBuild()

        publishers {
            wsCleanup()
        }

        parameters {
            choiceParam('ENV', Defaults.capoEnvList, 'Choose the environment you want to install')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('ECCD_LINK', 'https://arm.sero.gic.ericsson.se/artifactory/proj-erikube-generic-local/erikube/releases/2.25.0/CXP9043015/CXP9043015R1B.tgz', 'Provide link to download CAPO package.')
            stringParam('MASTER_DIMENSIONS', '3, 4, 8, 50', 'Provide info about naster node from CPI.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB)')
            stringParam('WORKER_DIMENSIONS', '6, 18, 25, 116', 'Provide info about worker (control plane) node from CPI.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB)')
            stringParam('GERRIT_BRANCH', 'master', 'eo-install repository branch')
            if (job_name.contains('debug')) {
                stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from commit')
            }
        }

        environmentVariables {
            keepBuildVariables(true)
        }

        wrappers {
            preBuildCleanup()
            buildName('#${BUILD_NUMBER}_${ENV}')
        }

        scm {
            git {
                remote {
                    url(Defaults.INSTALL_PROJECT_GIT_REPO)
                    credentials(Defaults.GIT_CRED)
                }
                branch('${GERRIT_BRANCH}')
            }
        }

        steps {
            environmentVariables {
                envs(
                    [
                        'LOG_LEVEL': 'DEBUG',
                        'PYTHON_PATH': Defaults.PYTHON_PATH,
                        'GIT_REPO': Defaults.INSTALL_PROJECT_GIT_REPO,
                        'INSTALL_CAPO': true,
                    ]
                )
            }

            if (job_name.contains('debug')) {
                shell(Defaults.pullFromCommitShellCommand)
            }
            shell(Defaults.virtualEnvInstallShellCommand)
            shell(Defaults.triggerTest('eo_install.main'))
        }

        publishers {
            archiveArtifacts{
                pattern('*.log')
                pattern('cluster_artifacts.tar.gz')
                onlyIfSuccessful(false)
                allowEmpty(true)
            }
        }
    }
}
