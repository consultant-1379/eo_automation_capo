# Overview
This project contains automation script for EVNFM, cCM, AAT, CAPO, and ECCD installation and upgrade.

# Getting Started
## Requirements
* Python (version 3.11 or higher)

## Project setup (Windows)
1. Install Python from https://www.python.org/downloads/.
2. Make sure to add location of the python.exe to the PATH in System variables.
3. Install virtualenv using command `python -m pip install virtualenv`. (Read more about virtualenv https://docs.python.org/3/tutorial/venv.html)
4. Clone this project from Gerrit.
5. Create virtualenv within project root `python -m virtualenv venv`.
6. Activate virtualenv - execute `venv\Scripts\activate` in project root folder.
7. Install python libraries using pip `pip install -r requirements.txt`.

## Project setup (Ubuntu)
1. Install Python.
2. Install virtualenv using command `sudo apt install python3-venv`.
3. Clone this project from Gerrit.
4. Create virtualenv - execute `python -m venv venv` in project root folder.
5. Activate virtualenv - execute `source venv/bin/activate` in project root folder.
6. Install python libraries using pip `pip install -r requirements.txt`.

## Test Configuration
You can configure test execution against specific environment using environment variables:

| Name                | Required | Default         | Example         | Description                                  |
|---------------------|----------|-----------------|-----------------|:---------------------------------------------|
| ENV                 | yes      | none            | c16a024         | The environment you want to reinstall        |                     
| CONTROLLER_ENV      | yes      | none            | eo_node         | The controller VM used for installation      |    
| EO_VERSION          | yes      | none            | 1.7.0-214       | Desired EO version                           |
| INSTALL_EVNFM       | yes      | false           | true            | Option to install EO EVNFM                   |
| UPGRADE_EVNFM       | yes      | false           | true            | Option to upgrade EO EVNFM                   |
| DOWNLOAD_PACKAGES   | yes      | true            | false           | Option to download EO packages               |
| HELM_TIMEOUT        | yes      | 1800            | 5400            | EO installation helm timeout                 |
| ECCD_LINK           | yes      | none            | << link >>      | The link to the ECCD package                 |
| INSTALL_ECCD        | yes      | false           | true            | Option to install IBD ECCD cluster           |
| UPGRADE_ECCD        | yes      | false           | true            | Option to upgrade IBD ECCD cluster           |
| INSTALL_CAPO        | yes      | false           | true            | Option to install VM ECCD cluster            |
| UPGRADE_CAPO        | yes      | false           | true            | Option to upgrade VM ECCD cluster            |
| DIRECTOR_DIMENSIONS | yes      | 1, 2, 4, 90, 10 | 2, 2, 4, 90, 10 | Dimensions for Director VMs                  |
| MASTER_DIMENSIONS   | yes      | 3, 6, 8, 50     | 3, 6, 8, 50     | Dimensions for Master VMs                    |
| WORKER_DIMENSIONS   | yes      | 6, 15, 36, 181  | 6, 18, 62, 313  | Dimensions for Worker VMs                    |
| INSTALL_AAT         | no       | false           | true            | Option to install AAT test service           |
| CLEAN_ECCD          | no       | false           | true            | Option to clean IBD ECCD registry            |
| DELETE_NODE_IMAGES  | no       | false           | true            | Option to delete docker images on ECCD nodes |
| ASSERT_UPGRADE_TIME | no       | false           | true            | Option to assert upgrade time (for TERE)     |

## Script Execution
### Execution tests from CMD (Windows)
```
set ENV=c16a024
set CONTROLLER_ENV=eo_node 
set EO_VERSION=2.21.0-129#1.43.88
set INSTALL_EVNFM=true
set UPGRADE_EVFNM=false
set DOWANLOAD_PACKAGES=true
set INSTALL_CM=false
set UPGRADE_CM=false
set HELM_TIMEOUT=1800
set ECCD_LINK=https://arm.rnd.ki.sw.ericsson.se/artifactory/proj-erikube-generic-local/erikube/releases/2.25.1/CXP9036305/CXP9036305R33C.tgz
set INSTALL_ECCD=false
set UPGRADE_ECCD=false
set INSTALL_CAPO=false
set UPGRADE_CAPO=false
set DIRECTOR_DIMENSIONS="1, 2, 4, 90, 10"
set MASTER_DIMENSIONS="3, 6, 8, 50"
set WORKER_DIMENSIONS="6, 15, 36, 181"
set INSTALL_AAT=false
set CLEAN_ECCD=false
set ASSERT_UPGRADE_TIME=false

python -m eo_install.main
```
### Execution tests from terminal (Ubuntu)

```
export ENV=c16a024
export CONTROLLER_ENV=eo_node 
export EO_VERSION=2.21.0-129#1.43.88
export INSTALL_EVNFM=true
export UPGRADE_EVFNM=false
export DOWANLOAD_PACKAGES=true
export INSTALL_CM=false
export UPGRADE_CM=false
export HELM_TIMEOUT=1800
export ECCD_LINK=https://arm.rnd.ki.sw.ericsson.se/artifactory/proj-erikube-generic-local/erikube/releases/2.25.1/CXP9036305/CXP9036305R33C.tgz
export INSTALL_ECCD=false
export UPGRADE_ECCD=false
export INSTALL_CAPO=false
export UPGRADE_CAPO=false
export DIRECTOR_DIMENSIONS="1, 2, 4, 90, 10"
export MASTER_DIMENSIONS="3, 6, 8, 50"
export WORKER_DIMENSIONS="6, 15, 36, 181"
export INSTALL_AAT=false
export CLEAN_ECCD=false
export ASSERT_UPGRADE_TIME=false

python -m eo_install.main
```

## Python requirements file

Located within root folder file `requirements.txt` contains list of all needed for the project python libraries.

## Configuration files

All configuration files are stored in this directory: `/config`
To use automation installation script, please create config file with values should be used during installation.
Use example config file in each directory as a reference.

## Project structure

- `/ci` - Groovy DSL jobs
- `/config` - config files 
- `/eo_install` - directory with entry point to the script and the main runner of the installation procedure
- `/libs` - different libs that are using for the installation
- `/resources` - directory where private ssh keys and project certificates are stored
- `/test_service_install` - code to install AAT
- `/tests` - tests to check code consistency
- `/tools` - set of different tools: cluster cleanup, post-build actions for CI, WA for CVNFM

# Project branches

There are branches in the project for each EO version. Please choose needed one. 
Master branch always has the latest code.
