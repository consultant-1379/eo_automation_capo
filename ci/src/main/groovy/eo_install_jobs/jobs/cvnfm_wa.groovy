import eo_install_jobs.defaults.Defaults

all_envs = Defaults.evnfmEnvList + Defaults.cmEnvsList + Defaults.eccdEnvList
needed_envs = all_envs.unique()

freeStyleJob('eo-rv-cvnfm-wa') {
    description Defaults.description("""<h2>Job to apply WA for CVFNM to work with internal-trust certs</h2>""")

    label Defaults.SLAVE
    logRotator(50, 200)
    concurrentBuild()

    publishers{
        wsCleanup()
    }

    parameters {
        choiceParam('ENV', needed_envs, 'Choose the needed environment')
        stringParam('CLUSTER_CRED', '', 'Specify cluster credentials that is used as a CISM (e.g. eccd@10.0.0.1)')
        stringParam('PRIVATE_KEY', '', 'Specify private key to access the cluster')
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
                'CONTROLLER_ENV': 'eo_node_ie'
            ]
            )
        }
    shell(Defaults.pullFromCommitShellCommand)
    shell(Defaults.virtualEnvInstallShellCommand)
    shell(Defaults.triggerTest('tools.wa_for_cvnfm'))
    }
    publishers {
        archiveArtifacts{
            pattern('*.log')
            onlyIfSuccessful(false)
            allowEmpty(true)
        }
    }
}
