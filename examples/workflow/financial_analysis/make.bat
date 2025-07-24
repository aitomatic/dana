@echo off

:: TARGETS
:: =======
SET TARGET=%1

IF "%TARGET%"=="test-all" GOTO test-all

:: INSTALLATION
:: ============
:test-all
  dana2 test.na
  dana2 test-adj-income.na
  dana2 test-cap-intens.na
  dana2 test-income-util-ratios.na
  dana2 test-leverage.na
  dana2 test-liquidity.na
  dana2 test-margin-ratios.na
  dana2 test-return-ratios.na
  dana2 test-turnover-ratios.na
  GOTO end

:: END
:: ===
:end
