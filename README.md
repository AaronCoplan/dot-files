# dot-files

Personal configurations, shell utilities, and an automated setup script for macOS and Ubuntu environments.

## Setup

Run the setup script to install everything and configure your environment:

```bash
./setup.sh
```

The script will prompt you to select your OS (Mac or Ubuntu) and then:

- Install core tools: Homebrew (macOS), Node/NPM, tmux, zsh, bat, coreutils
- Install and configure [oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh) with [pure prompt](https://github.com/sindresorhus/pure)
- Install [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting) plugin
- Set up git config (prompts for your GitHub username and email)
- Copy tmux, zsh, and alias configurations into place

## Structure

```
setup.sh                          # Automated setup script
configs/
  zshrc                           # Zsh configuration (oh-my-zsh, pure prompt, aliases)
  gitconfig                       # Git config template with useful aliases
  tmux.conf                       # tmux config (Ctrl-D prefix, alt-arrow pane navigation)
  terminal-conf.terminal          # macOS Terminal.app profile (Nord theme)
  vscode-user-settings.json       # VS Code settings
  init.el                         # Emacs configuration
aliases/
  cdu                             # cd up N directories (e.g. `cdu 3`)
  createdockspacer                # Add a spacer tile to the macOS Dock
  currentbranch                   # Print the current git branch (`curbr`)
  printheader                     # Print formatted section headers
  waitforhost                     # Ping a host until it comes online
nord.txt                          # Nord color palette reference
```

## License

See [LICENSE](LICENSE).
