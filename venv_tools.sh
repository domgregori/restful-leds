#! /bin/bash

# Script credit: DHRUV MAKWANA
# https://makwanadhruv.medium.com/automating-virtual-environments-bash-script-magic-for-python-developers-3a06df1777a6

check_virtualenv() {
  if ! command -v python -m venv -h &> /dev/null; then
    echo "virtualenv is not installed. Installing..."
    if ! python3 -m pip install --user virtualenv; then
      sudo apt update && sudo apt install python3-venv python3-pip
      echo "virtualenv installation complete."
    fi
    echo "virtualenv installation complete."
  fi
  }

create_venv() {
  # Check if virtualenv is installed, if not, install it
  check_virtualenv

  local env_name=${1:-".venv"}

  if [ -d "$env_name" ]; then
    echo "Virtual environment '$env_name' already exists. Aborting."
    return 1
  fi

  python3 -m venv "$env_name"
  source "./$env_name/bin/activate"
  pip install -U pip
  
  echo "Activate venv enviroment with (unless dependencies still need to ne installed:"
  echo "source ./$env_name/bin/activate"
  echo
  echo "Install deps if needed using:"
  echo "./venv_tools install"
}

activate_venv() {
  local env_name=${1:-".venv"}

  if [ ! -d "$env_name" ]; then
    echo "Virtual environment '$env_name' not found. Use '$0 create [env_name]' to create one."
    return 1
  fi
  
  echo "To enter venv enviroment run:"
  echo "source ./$env_name/bin/activate"

  #source "./$env_name/bin/activate"
}

install_deps() {
  local env_name=${1:-".venv"}

  if [ ! -d "$env_name" ]; then
    echo "Virtual environment '$env_name' not found. Use '$0 create [env_name]' to create one."
    return 1
  fi

  source "./$env_name/bin/activate"

  if [ -f "requirements.txt" ]; then
    pip install -r ./requirements.txt
  fi

  if [ -f "setup.py" ]; then
    pip install -e .
  fi

  echo "Dependencies installed"
  echo
  echo "To enter venv enviroment run:"
  echo "source ./$env_name/bin/activate"

}

export_deps() {
  local env_name=${1:-".venv"}

  if [ ! -d "$env_name" ]; then
    echo "Virtual environment '$env_name' not found. Use '$0 create [env_name]' to create one."
    return 1
  fi

  source "./$env_name/bin/activate"
  pip freeze > requirements.txt
  echo "Dependencies exported to requirements.txt"
}

remove_venv() {
  local env_name=${1:-".venv"}

  if [ ! -d "$env_name" ]; then
    echo "Virtual environment '$env_name' not found."
    return 1
  fi

  deactivate
  rm -rf "$env_name"
}

print_help() {
  # Help message explaining script usage
  echo "Usage: $0 [option] [env_name]"
  echo "Options:"
  echo "  create   Create a new virtual environment (default name: .venv)"
  echo "  activate Activate an existing virtual environment (default name: .venv)"
  echo "  install  Install dependencies within a virtual environment (default name: .venv)"
  echo "  export   Export installed dependencies to requirements.txt within a virtual environment (default name: .venv)"
  echo "  remove   Remove an existing virtual environment (default name: .venv)"
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  print_help
  return 0
fi

case "$1" in
  "create")
    create_venv "$2"
    ;;
  "activate")
    activate_venv "$2"
    ;;
  "install")
    install_deps "$2"
    ;;
  "export")
    export_deps "$2"
    ;;
  "remove")
    remove_venv "$2"
    ;;
  *)
    echo "Unknown option: $1"
    print_help
    exit 1
    ;;
esac
