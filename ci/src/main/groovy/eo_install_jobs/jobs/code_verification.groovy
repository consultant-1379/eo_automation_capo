import eo_install_jobs.defaults.Defaults

freeStyleJob('eo-install-commit-verification') {
    description Defaults.description("""<h2>EO-install project commit verification job</h2>""")

    publishers {
        wsCleanup()
    }

    label Defaults.SLAVE
    logRotator(50, 200)
    concurrentBuild()

    parameters {
        stringParam('GERRIT_BRANCH', 'master', 'eo-install repository branch')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from commit')
    }

    wrappers {
        preBuildCleanup()
    }

    scm {
        git {
            remote {
                url(Defaults.INSTALL_PROJECT_GIT_REPO)
                credentials(Defaults.GIT_CRED)
                name(Defaults.ORIGIN)
                refspec(Defaults.GERRIT_REFSPEC)
            }
            branch('${GERRIT_BRANCH}')
            extensions {
                choosingStrategy {
                    gerritTrigger()
                }
            }
        }
    }

    triggers {
        gerrit {
            events {
                patchsetCreated()
            }
            project('plain:rv/common/eo-install', ['ant:**'])
        }
    }

    steps {
        environmentVariables {
            envs(
            [
                'LOG_LEVEL': 'DEBUG',
                'PYTHON_PATH' : Defaults.PYTHON_PATH,
                'GIT_REPO': Defaults.INSTALL_PROJECT_GIT_REPO,
                'CONTROLLER_ENV': 'eo_node_ie'
                ]
            )
        }
    shell(Defaults.pullFromCommitShellCommand)
    shell(Defaults.virtualEnvInstallShellCommand)
    shell(Defaults.triggerTest('tests.code_verify.code_verification_script'))
    }
}
