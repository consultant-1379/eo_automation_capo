import eo_install_jobs.defaults.Defaults

for ( def job_name : [
        'legacy-eo-rv-ccm-installation',
        'legacy-eo-rv-ccm-installation-debug'
        ]
    )
{

    freeStyleJob(job_name) {
        description Defaults.description("""<h2>Job to install cCM (using CSAR packages)</h2>""")

        label Defaults.SLAVE
        logRotator(50, 200)
        concurrentBuild()

        publishers{
            wsCleanup()
        }

        parameters {
            choiceParam('ENV', Defaults.cmEnvsList, 'Choose the environment you want to reinstall')
            stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 2.7.0-310#1.42.0-451)')
            stringParam('HELM_TIMEOUT', '5400', 'Provide the EO installation timeout in seconds (e.g. 3600). The default value is 1800 seconds')
            stringParam('NAMESPACE', 'eric-eo-cm-', 'Provide the namespace name should be used during installation')
            stringParam('STACK_NAME', 'ccd-', 'ECCD stack name on OpenStack')
            stringParam('GERRIT_BRANCH', 'eo', 'eo-install repository branch')
            if (job_name.contains('debug')) {
                stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from commit')
                booleanParam('SKIP_PKG', false, 'Use if you know what to do')
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
                    'PYTHON_PATH' : Defaults.PYTHON_PATH,
                    'GIT_REPO': Defaults.INSTALL_PROJECT_GIT_REPO,
                    'INSTALL_CM': true,
                    'CONTROLLER_ENV': 'eo_rv_install_node'
                    ]
                )
            }
        if (job_name.contains('debug')) {
            shell(Defaults.pullFromCommitShellCommand)
        }
        shell(Defaults.virtualEnvInstallShellCommand)
        shell(Defaults.triggerTest('eo_install.main'))
        publishers {
            archiveArtifacts{
                pattern('*.log')
                onlyIfSuccessful(false)
                allowEmpty(true)
                }
            }
        }
    }
}
