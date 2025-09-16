@echo off


:: TARGETS
:: =======
SET TARGET=%1

IF "%TARGET%"=="setup" GOTO setup
IF "%TARGET%"=="test-setup" GOTO test-setup
IF "%TARGET%"=="update-git-submodule" GOTO update-git-submodule


:: SETUP
:: =====
:setup
  @ git pull
  .bin\install-venv-with-dana
  .bin\update-git-submodule
  GOTO end

:test-setup
  .bin\test-setup
  GOTO end

:update-git-submodule
  .bin\update-git-submodule
  GOTO end


:: END
:: ===
:end
