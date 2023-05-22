---
title: Woodchipper
description: Contextually aware structured logging library
cascade:
  github_repo: https://github.com/tackle-io/woodchipper/
  github_subdir: docs
  github_branch: main
  path_base_for_github_subdir: content/\w+/services/woodchipper/
---

Woodchipper is a wrapper around the excellent [structlog](https://structlog.org/) library to enable drop-in,
contextually aware, structured logging. In development, Woodchipper outputs easy to read, colorized logs. In
production, Woodchipper emits JSON encoded log messages for consumption by an intelligent log management
system like ELK, CloudWatch, or DataDog.

## Quickstart

Adding Woodchipper to a Python project is easy.

```python
import os

import woodchipper
import woodchipper.configs

woodchipper.configure(
    config=(
        woodchipper.configs.DevLogToStdout
        if os.getenv("FLASK_ENV") == "development"
        else woodchipper.configs.JSONLogToStdout
    ),
    facilities={"": "INFO"},
)

logger = woodchipper.get_logger(__name__)

logger.info("Woodchipper configured.", env=os.getenv("FLASK_ENV"))
```

If we run the above, setting `FLASK_ENV` to `development`, we get:

```
2022-01-14 10:57.49 [info     ] Woodchipper configured.        [__main__] func_name=<module> lineno=17 module=demo env=development
```

Our log output not only contains the logger name, logger level, and log event, but it also contains details
about where in the code the log message was emitted and the extra key/value pair we provided about the
environment name.

If we run it without `FLASK_ENV` set to `production`, we get JSON output:

```json
{"env": "production", "event": "Woodchipper configured.", "level": "info", "logger": "__main__", "timestamp": "2022-01-14 11:08.30", "func_name": "<module>", "lineno": 17, "module": "demo"}
```
