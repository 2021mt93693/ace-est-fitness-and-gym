# ace-est-fitness-and-gym
An automated application that demonstrates core functionalities pertinent to a fitness and gym management system.

# Install pyenv
brew install pyenv

# Add these lines (in this exact order) in ~/.zshrc:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv init --path)"

# Reload shell
source ~/.zshrc

# Install Python
pyenv install 3.13.0
pyenv global 3.13.0

# Setting Vitual Environment for python runtime
mkdir .env
python3 -m venv .env
source .env/bin/activate

# Intall required python libraries
pip install -r requirements.txt