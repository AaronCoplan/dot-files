#!/bin/bash

set -e

# install a brew formula if not already installed
brew_install() {
  if brew list "$1" &>/dev/null; then
    print_header "$1 already installed, skipping"
  else
    print_header "Installing $1"
    brew install "$1"
  fi
}

# install a brew cask if not already installed
brew_install_cask() {
  if brew list --cask "$1" &>/dev/null; then
    print_header "$1 already installed, skipping"
  else
    print_header "Installing $1"
    brew install --cask "$1"
  fi
}

mac_specific_install() {
  # install Homebrew if not already installed
  if ! command -v brew &> /dev/null; then
    print_header "Installing Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    print_header "Homebrew already installed, skipping"
  fi
  brew_install node
  brew_install tmux
  brew_install zsh
  brew_install bat
  brew_install coreutils
  brew_install_cask font-source-code-pro
  brew_install_cask emacs
  # configure system settings
  # allow quitting finder via Command-Q, this hides Desktop icons/files
  defaults write com.apple.finder QuitMenuItem -bool true
}

apt_install() {
  if dpkg -s "$1" &>/dev/null; then
    print_header "$1 already installed, skipping"
  else
    print_header "Installing $1"
    sudo apt install -y "$1"
  fi
}

ubuntu_specific_install() {
  # update package lists
  print_header "Updating package lists"
  sudo apt update
  # upgrade packages
  print_header "Upgrading packages"
  sudo apt upgrade -y
  apt_install git
  # install node and npm via apt
  if ! command -v node &>/dev/null; then
    print_header "Installing Node and NPM"
    curl -sL https://deb.nodesource.com/setup_8.x | sudo bash
    sudo apt update
    sudo apt install -y nodejs
  else
    print_header "Node already installed, skipping"
  fi
  apt_install tmux
  apt_install zsh
}

# source helper function for printing
source aliases/printheader

# determine OS and perform OS specific install
print_header "Begining Installation"
PS3='Please select your OS: '
options=("Mac" "Ubuntu" "Other/Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Mac")
            mac_specific_install
            break
            ;;
        "Ubuntu")
            ubuntu_specific_install
            break
            ;;
        "Quit")
            exit 1
            ;;
        *)
            echo "[ERROR] Invalid Option: $REPLY, exiting."
            exit 1
            ;;
    esac
done

# now that zsh is installed, make it default shell
if [ "$(basename "$SHELL")" = "zsh" ]; then
  print_header "zsh is already default shell, skipping"
else
  print_header "Setting zsh as default shell"
  echo $(which zsh) | sudo tee -a /etc/shells
  chsh -s $(which zsh)
fi

# install oh-my-zsh
if [ -d "$HOME/.oh-my-zsh" ]; then
  print_header "oh-my-zsh already installed, skipping"
else
  print_header "Installing oh-my-zsh"
  set +e
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
  set -e
fi

# install pure-prompt
if npm list --global pure-prompt &>/dev/null; then
  print_header "pure-prompt already installed, skipping"
else
  print_header "Installing pure-prompt"
  sudo npm install --global pure-prompt --allow-root --unsafe-perm=true
fi

# install zsh-syntax-highlighting oh-my-zsh plugin
ZSH_SYNTAX_DIR="${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting"
if [ -d "$ZSH_SYNTAX_DIR" ]; then
  print_header "zsh-syntax-highlighting already installed, skipping"
else
  print_header "Installing zsh-syntax-highlighting plugin"
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_SYNTAX_DIR"
fi

# setup gitconfig
print_header "Setting up gitconfig"
echo -n "Enter your GitHub username for your gitconfig: "
read GITHUB_USERNAME

echo -n "Enter your GitHub email for your gitconfig: "
read GITHUB_EMAIL

cp configs/gitconfig ~/.gitconfig
sed -i -e "s/GIT_USERNAME_PLACEHOLDER/$GITHUB_USERNAME/g" ~/.gitconfig
sed -i -e "s/GIT_EMAIL_PLACEHOLDER/$GITHUB_EMAIL/g" ~/.gitconfig

# setup emacs config
print_header "Setting up emacs config"
mkdir -p ~/.emacs.d
cp configs/init.el ~/.emacs.d/init.el

# setup tmux.conf
print_header "Setting up tmux.conf"
cp configs/tmux.conf ~/.tmux.conf

# setup aliases
print_header "Setting up aliases"
rm -rf ~/.dotfiles_aliases
cp -r aliases ~/.dotfiles_aliases

# setup zshrc
print_header "Setting up zshrc"
cp configs/zshrc ~/.zshrc

print_header "Setup completed successfully"
