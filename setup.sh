#!/bin/bash -e

# check os
uname_out=$(uname -s)
case ${uname_out} in
    Linux)      installer='sudo apt install' ;;
    Darwin)     installer='brew install' ;;
    *)          echo 'Your system is not supported, choose installer manually.'
                exit 1
esac

${installer} python3.6
${installer} python3.6-venv

# set up virtualenv
PROJECT_PATH=$(dirname $0)
python3.6 -m venv ${PROJECT_PATH}/venv
source ${PROJECT_PATH}/venv/bin/activate
pip install -r ${PROJECT_PATH}/requirements.txt
chmod u+x ${PROJECT_PATH}/controller.py

echo 'Installed successfully'
