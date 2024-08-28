import eo_install_jobs.defaults.Defaults

all_envs = Defaults.evnfmEnvList + Defaults.cmEnvsList + Defaults.eccdEnvList
needed_envs = all_envs.unique()

freeStyleJob('eo-rv-eccd-registry-cleanup') {
    description Defaults.description("""<h2>Job for ECCD registry cleanup</h2>""")

    label Defaults.SLAVE
    logRotator(50, 200)
    concurrentBuild()

    publishers{
        wsCleanup()
    }

    parameters {
        choiceParam('ENV', needed_envs, 'Choose the environment you want to cleanup')
        booleanParam('DELETE_NODE_IMAGES', false, 'Choose to delete docker images tagged to k8s-registry on both master and worker nodes. Requires access to director/cp VM')
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
                'CLEAN_ECCD': true,
                'CONTROLLER_ENV': 'eo_node_ie'
                ]
            )
        }
    shell(Defaults.pullFromCommitShellCommand)
    shell(Defaults.virtualEnvInstallShellCommand)
    shell(Defaults.triggerTest('tools.cluster_cleanup.cleanup_mgr'))
        }
    publishers {
        archiveArtifacts{
            pattern('*.log')
            onlyIfSuccessful(false)
            allowEmpty(true)
        }
    }
}
