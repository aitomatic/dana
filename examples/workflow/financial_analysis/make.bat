@echo off

:: TARGETS
:: =======
SET TARGET=%1

IF "%TARGET%"=="test-all" GOTO test-all

:: TESTS
:: =====
:test-all
  dana test.na
  dana test-adj-income.na
  dana test-cap-intens.na
  dana test-income-util-ratios.na
  dana test-leverage.na
  dana test-liquidity.na
  dana test-margin-ratios.na
  dana test-return-ratios.na
  dana test-turnover-ratios.na
  GOTO end

:: END
:: ===
:end
