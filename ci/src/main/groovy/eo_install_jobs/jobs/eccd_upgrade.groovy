import eo_install_jobs.defaults.Defaults

def warningMessage = "<div><b style='color: red;'>WARNING: make sure the project (tenancy) has additional vCPUs and RAM for an extra VM</b></div><div>(additional vCPUs and RAM are equivalent to the biggest flavor of any node type)</div>"

for (def job_name: [
        'eo-rv-eccd-upgrade',
        'eo-rv-eccd-upgrade-debug'
    ])

{
    freeStyleJob(job_name) {
        description Defaults.description("""<h2>Job for upgrading an ECCD</h2>${warningMessage}""")

        label Defaults.SLAVE
        logRotator(50, 200)
        concurrentBuild()

        publishers {
            wsCleanup()
        }

        parameters {
            choiceParam('ENV', Defaults.eccdEnvList, 'Choose an environment you want to upgrade' + warningMessage)
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('ECCD_LINK', 'https://arm.rnd.ki.sw.ericsson.se/artifactory/proj-erikube-generic-local/erikube/releases/2.18.0/CXP9036305R26A.tgz', 'Provide link to download ECCD package. <div><b style="color: red;">WARNING: make sure you are providing the same package version as installed</b></div>')
            stringParam('DIRECTOR_DIMENSIONS', '2, 2, 4, 90, 10', 'Provide info about Director VM from CPI.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB), Configuration Volume')
            stringParam('MASTER_DIMENSIONS', '3, 2, 4, 20, 10', 'Provide info about Master VM from CPI.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB), Configuration Volume')
            stringParam('WORKER_DIMENSIONS', '4, 16, 33, 120', 'Provide info about Worker VM from CPI.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB)')
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
                        'UPGRADE_ECCD': true
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
                pattern('env_file.yaml')
                onlyIfSuccessful(false)
                allowEmpty(true)
            }
        }
    }
}
