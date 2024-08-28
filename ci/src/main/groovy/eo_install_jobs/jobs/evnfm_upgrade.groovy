import eo_install_jobs.defaults.Defaults

String sectionHeaderStyleCss = 'color: white; background: #06A39C; font-family: Roboto, sans-serif !important; padding: 5px; text-align: center;'
String separatorStyleCss = 'border: 0; background: #999;'

for ( def job_name : [
        'eo-rv-evnfm-upgrade',
        'eo-rv-evnfm-upgrade-debug'
        ]
    )
{

    freeStyleJob(job_name) {
        description Defaults.description("""<h2>Job to upgrade EO products (using CSAR packages)</h2>""")

        label Defaults.SLAVE
        logRotator(50, 200)
        concurrentBuild()

        publishers{
            wsCleanup()
        }

        parameters {
            parameterSeparatorDefinition{
                name('EVNFM SECTION')
                separatorStyle(separatorStyleCss)
                sectionHeader('EVNFM SECTION')
                sectionHeaderStyle(sectionHeaderStyleCss)
                }
            choiceParam('ENV', Defaults.evnfmEnvList, 'Choose the environment you want to upgrade')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 2.7.0-310#1.42.0-451)')
            stringParam('HELM_TIMEOUT', '2400', 'Provide the EO pgrade timeout in seconds. The default value is 2400 seconds')
            parameterSeparatorDefinition{
                name('GR SECTION')
                separatorStyle(separatorStyleCss)
                sectionHeader('GR SECTION')
                sectionHeaderStyle(sectionHeaderStyleCss)
                }
            booleanParam('ENABLE_GR', false, 'Check to enable GR during EVNFM installation')
            choiceParam('CLUSTER_ROLE', ['PRIMARY', 'SECONDARY'], 'Choose role for environment you\'ve selected in ENV list')
            choiceParam('NEIGHBOR_ENV', Defaults.evnfmEnvList, 'Choose the neigbor environment')
            choiceParam('GLOBAL_REGISTRY', Defaults.globalRegistryList, 'Provide global registry hostname')
            parameterSeparatorDefinition{
                name('ADDITIONAL OPTIONS SECTION')
                separatorStyle(separatorStyleCss)
                sectionHeader('ADDITIONAL OPTIONS SECTION')
                sectionHeaderStyle(sectionHeaderStyleCss)
                }
            if (job_name.contains('debug')) {
                booleanParam('ENABLE_VM_VNFM_HA', true, 'Check to enable VM VNFM HA. Available starting from helmfile 2.22.x')
                stringParam('NAMESPACE', '', 'Provide for specific needs only.')
                stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please change only in case need to run from commit.')
                booleanParam('ASSERT_UPGRADE_TIME', false, 'For TERE needs, assert upgrade less then 90 minutes.')
            }
            stringParam('GERRIT_BRANCH', 'master', 'eo-install repository branch')
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
                    'UPGRADE_EVNFM': true
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
                pattern('*.log')
                pattern('site_values_*.yaml')
                onlyIfSuccessful(false)
                allowEmpty(true)
                }
            }
        }
    }
}
