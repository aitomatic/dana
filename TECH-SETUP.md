# Setup checklist

- Python 3.12 or higher
- Git
- GitHub developer access token with repo access permissions
- enable long paths on Windows:
  - https://geekrewind.com/how-to-enable-win32-long-paths-in-windows-11/
  - Japanese https://www.autodesk.com/jp/support/technical/article/caas/sfdcarticles/sfdcarticles/JPN/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html
- reboot computer after enabling long paths
- `git config --system core.longpaths true`
- `git clone https://github.com/aitomatic-oss/dana`
- `cd dana`
- `git checkout support/windows`
- `bin\windows\setup`
- put in `.env` file per `.env.example` either in the `dana` directory or in the "home" directory
