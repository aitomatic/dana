# Technical Setup Guide

- Mac:

  - install Homebrew by running command on [brew.sh](https://brew.sh)

    - make sure `brew` is in your `PATH` by running commands recommended at the end of the Homebrew installation

  - install Python 3.12+ by running `brew install Python`

    - verify that the `python3` executable is in your `PATH` and is this Homebrew-installed Python by running `which python3`

    - make sure Python-installed scripts are in your `PATH` by adding the following to your `~/.zprofile` file: `export PATH=$PATH:~/Library/Python/3.13/bin` (substitute `3.13` with the version of Python you installed)

Clone this repo down to your machine:

- Mac: if using the HTTPS protocol, then it is best to have your GitHub credentials saved in your Mac's keychain

Windows issues to note:

- long file paths (over 266 characters) need to be enabled
- running `npm` on Windows is really troublesome


## Setup Guide

Have Python 3.12+ installed and available as the default `python3` executable from search path.

Fully sync the `.submodules/Dana` Git sub-module and check out its `aise/all` branch.

From this repo's root directory, run `make install` (on Linux or Mac) or `.\make install` (on Windows) to install dependencies.
