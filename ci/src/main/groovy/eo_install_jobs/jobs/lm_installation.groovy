import eo_install_jobs.defaults.Defaults

for ( def job_name : [
        'eo-rv-lm-installation',
        'eo-rv-lm-installation-debug'
        ]
    )
{
    freeStyleJob(job_name) {
        description Defaults.description("""<h2>Job to install LM (using CSAR packages)</h2>""")

        label Defaults.SLAVE
        logRotator(50, 200)
        concurrentBuild()

        publishers{
            wsCleanup()
        }

        parameters {
            choiceParam('ENV', Defaults.lmEnvsList, 'Choose the environment you want to install')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 2.7.0-310#1.42.0-451)')
            stringParam('HELM_TIMEOUT', '1800', 'Provide the EO installation timeout in seconds. The default value is 5400 seconds')
            stringParam('GERRIT_BRANCH', 'master', 'eo-install repository branch')
            if (job_name.contains('debug')) {
                stringParam('NAMESPACE', '', 'Provide for specific needs only.')
                booleanParam('DOWNLOAD_PACKAGES', true, 'Must be checked if no packages are present in workdir.')
                booleanParam('SKIP_CHECKSUM', false, 'Check to skip checksum verification for CSARs.')
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
                    'PYTHON_PATH' : Defaults.PYTHON_PATH,
                    'GIT_REPO': Defaults.INSTALL_PROJECT_GIT_REPO,
                    'INSTALL_LM': true
                ]
            )
        }

        if (job_name.contains('debug')) {
            shell(Defaults.pullFromCommitShellCommand)
        }
        shell(Defaults.virtualEnvInstallShellCommand)
        shell(Defaults.triggerTest('eo_install.main'))
        publishers {
            postBuildTask{
                task('Build was aborted', Defaults.triggerTest('tools.post_build_step'))
            }
            archiveArtifacts{
                pattern('site_values_*.yaml')
                pattern('*.log')
                onlyIfSuccessful(false)
                allowEmpty(true)
                }
            }
        }
    }
}
