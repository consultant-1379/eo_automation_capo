package eo_install_jobs.defaults


class Defaults {
	static final String INSTALL_PROJECT_GIT_REPO = '${GERRIT_HTTP_URL}/rv/common/eo-install'
	static final String GIT_CRED = 'cloudman'
	static final String SLAVE = 'docker-ecm156x169'
	static evnfmEnvList = ["c13a3", "c15a2", "c15a3", "c16a024", "c12a002", "c12a5", "c16a033", "c16a026", "c16b027", "c16c027", "c16c029", "c16c022", "ci476", "ci480", "cnis-n293v1", "cnis-n293v5", "fs3", "nfvi-1", "nfvi-2", "nfvi-3", "c11a1", "c16c1"]
	static cmEnvsList = ["prod312", "prod324", "prod330", "prod336", "prod343", "prod344", "prod345", "prod347", "prod349", "prod367", "c16a026", "c16b027", "c16c027", "c16c029"]
	static lmEnvsList = ["c13a3", 'c15a2', 'c15a3', 'c16a024', "c16b033-1", "c16b033-2", "cnis-1", "cnis-2", "prod337", "prod352", "c15a7", "c11a3"]
	static capoEnvList = ["c13a3", "c15a2", "c15a3", "c16a024", "prod324", "prod330", "c12a4", "c13a16", "ci476", "fs3", "prod308"]
	static eccdEnvList = ["c13a3", "c15a2", "c15a3", "c16a024", "c5a1", "c11a2", "c12a4", "c12a5", "c13a16", "c15a010", "c15a011", "ci476", "ci480", "fs3", "prod337", "prod352"]
	static controllersList = ["eo_node_ie", "eo_node_se", "ieatflo13a-15", "atvts3430", "atvts3491"]
	static globalRegistryList = ["", "global-container-registry.ccd-c15a7.athtem.eei.ericsson.se", "global-container-registry.c16a033.athtem.eei.ericsson.se", "global-evnfm-registry.ccd-c11a1.athtem.eei.ericsson.se"]
	static GERRIT_BRANCH = '${GERRIT_BRANCH}'
	static GERRIT_REFSPEC = '${GERRIT_REFSPEC}'
	static ORIGIN = 'origin'
	static PYTHON_PATH = '/opt/local/dev_tools/python/3.11.5/bin/python3.11'

	static final String JENKINS_URL = 'https://fem6s11-eiffel052.eiffel.gic.ericsson.se:8443'

	static def description(msg) {
		return """
			<div><b>
			WARNING: Manual modifications will be overwritten by seed job.
			<div>The source code for this job can be found <a href=\"https://gerrit.ericsson.se/plugins/gitiles/rv/common/eo-install/+/master/ci/src/main/groovy/eo_install_jobs/jobs/">here</a>.</div>
			</b></div>
			<div>${msg}</div>
		"""
	}
	static final String virtualEnvInstallShellCommand = '''
echo Hello, user!'''
//$PYTHON_PATH -m virtualenv venv
//source venv/bin/activate
//pip install -r requirements.txt --no-cache-dir

    static String triggerTest(String test_path=null) {
        return "$PYTHON_PATH -m ${test_path}" }
//        return "source venv/bin/activate && python -m ${test_path}"

	static final String pullFromCommitShellCommand = '''
if [ "$GERRIT_REFSPEC" != 'refs/heads/${GERRIT_BRANCH}' ]; then
    git fetch $GIT_REPO $GERRIT_REFSPEC && git checkout FETCH_HEAD
fi'''
}
