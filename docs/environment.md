---
title: Settings
description: Woodchipper settings are set using environment variables
---

## Environment variables

The following environment variables change the operation of Woodchipper.

### `WOODCHIPPER_KEY_PREFIX`

If set, any context variable emitted that does not have an explicit prefix set for it wil be prefixed with this value.
For example, if you set this environment variable to `tackle`, then a key `user` would appear in log messages as
`tackle.user`.

If you want to override this, call the clear_prefix() function on the logger once initialized.

### `WOODCHIPPER_CONTEXT_LOG_LEVEL`

If set, all entrance and exit logging for contexts will be logged at the level specified. Default is `"INFO"`.

### `WOODCHIPPER_DISABLE_SENTRY`

If set to a non-empty value, the built-in Sentry integration will be disabled.

### `WOODCHIPPER_DISABLE_COLORS`

In the `DevLogToStdout` configuration, the output of log messages is colorized. Setting this to a non-empty value will
disable the use of colors.

### `WOODCHIPPER_COLOR_STYLE`

In the `DevLogToStdout` configuration, the output of log messages is colorized. You can override the default color
scheme by setting this to a dot-separated Python import path to a dictionary with the color scheme you desire. To see
what should go into this dictionary, compare with the
[default style](https://github.com/hynek/structlog/blob/9446227b451730b05a8b618848403feedc4b7597/src/structlog/dev.py#L450-L459).
