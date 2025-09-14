# Dana Technical Setup Guide

## Typical Developer Setup

### Python & Related Prerequisites

Dana requires Python __3.12__ or __3.13__.

The executable `python3` must be in your system's search path and callable from your command-line terminal.

#### Python Installation Recommendations for Linux

- Install Python 3.12 or 3.13 through your Linux package manager

- Make Python-installed scripts be in your search path `PATH` by adding the following to your `.bashrc` file: `export PATH=$PATH:/usr/.local/bin` _(or another location than `/usr/.local/bin` where your Python-installed scripts are placed)_

#### Recommendations for Mac

- Install Homebrew by running command on [brew.sh](https://brew.sh)

- Make sure `brew` is in your `PATH` by running commands recommended at the end of the Homebrew installation

- Install Python 3.12 or 3.13 by running `brew install bython`

  - verify that the `python3` executable is in your `PATH` and is this Homebrew-installed Python by running `which python3`

  - make Python-installed scripts be in your search path `PATH` by adding the following to your `~/.zprofile` file: `export PATH=$PATH:~/Library/Python/3.13/bin` _(substitute `3.13` with the version of Python you installed)_

#### Python Installation Recommendations for Windows

- Install Python 3.12 or 3.13 from Microsoft Store

- Make Python-installed scripts be in your search path `PATH` by adding the following to your user environment variable `Path`: `C:\Users\<Your Windows Username>\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts` _(substitute `PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0` with the the Python installation directory in your `C:\Users\<Your Windows Username>\AppData\Local\Packages\`)_

- Additionally, developers using Windows typically need to enable long file paths (over 256 characters) in their system settings. Below are several good guides for enabling long file paths on Windows:
  - [Autodesk](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html)
    - [Japanese](https://www.autodesk.com/jp/support/technical/article/caas/sfdcarticles/sfdcarticles/JPN/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html)
  - [Geek Rewind](https://geekrewind.com/how-to-enable-win32-long-paths-in-windows-11)

  Reboot computer after enabling long paths.

### Dana Library Installation

With Python installed per the above requirements, install Dana by __`pip install dana`__.

### LLM Backend Configurations

In your user home directory (`~/`), create a sub-directory `.dana/`.

Make a copy of the default Dana `.env` environment variables file template at https://github.com/aitomatic/dana/blob/main/.env.example and save it as `.env` inside that `~/.dana/` directory (or `~\.dana\` on Windows).

Customize the `.env` file with your preferred model providers and credentials.

### IDE Dana Extension Installation

The Dana Language extension is available at https://open-vsx.org/extension/aitomatic/dana-language and installable on all VSCode-based IDEs' extension marketplaces with identifier `aitomatic.dana-language`.

In your code project, have a `.vscode/extensions.json` file with the following content:
```
{
  "recommendations": [
    "aitomatic.dana-language",
    ...  // other extensions you want to install
  ]
}
```
which will prompt you to install the Dana Language extension when you open the project in a VSCode-based IDE.

### Setup Testing

In your command-line terminal, run `dana repl` to enter the Dana REPL.

Type `llm('Hello, Dana!')` to verify that the LLM backend is properly configured and activated.

## Dana Contributor Setup

Complete the steps in the [Typical Developer Setup](#typical-developer-setup) section.

### `uv` Tool Installation

Install `uv` by running `pip install uv`.

### Git Configuration

Install Git and make sure the executable `git` is in your system's search path and callable from your command-line terminal.

On Windows, enable long paths for Git by running `git config --global core.longpaths true`.

### Dana Repo Clone & Installation

Clone the Dana repo down to your machine using `git clone https://github.com/aitomatic/dana` or `git clone git@github.com:aitomatic/dana`.

In the cloned repo's root directory, run `uv sync --extra dev` to create a virtual environment and install dependencies that will enable you to develop and test the Dana library and examples.
