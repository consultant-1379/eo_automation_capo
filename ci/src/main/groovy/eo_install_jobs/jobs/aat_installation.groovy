import eo_install_jobs.defaults.Defaults

freeStyleJob('eo-rv-aat-installation') {
    description Defaults.description("""<h2>Job for installing AAT test service (using CSAR package)</h2>""")

    label Defaults.SLAVE
    logRotator(50, 200)
    concurrentBuild()

    publishers{
        wsCleanup()
    }

    parameters {
        choiceParam('ENV', Defaults.evnfmEnvList + Defaults.cmEnvsList, 'Choose the environment you want to reinstall')
        stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 1.7.0-214)')
        stringParam('HELM_TIMEOUT', '1800', 'Provide the EO installation timeout in seconds (e.g. 3600). The default value is 1800 seconds')
        booleanParam('DELETE_OLD_WORKDIR', false, 'Check if you want to delete previous EO version workdir')
        stringParam('GERRIT_BRANCH', 'master', 'eo-install repository branch')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from commit')
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
                'UPGRADE_ECCD': false,
                'INSTALL_CODEPLOY': false,
                'INSTALL_ECCD': false,
                'INSTALL_AAT': true,
                'CONTROLLER_ENV': 'eo_node_ie'
            ]
        )
    }
        shell(Defaults.pullFromCommitShellCommand)
        shell(Defaults.virtualEnvInstallShellCommand)
        shell(Defaults.triggerTest('test_service_install.aat_main'))
    }

    publishers {
        postBuildTask{
            task('Build was aborted', Defaults.triggerTest('tools.post_build_step'))
        }
        archiveArtifacts{
            pattern('*.log')
            onlyIfSuccessful(false)
            allowEmpty(true)
        }
    }
}
