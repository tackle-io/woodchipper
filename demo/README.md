Woodchipper Demo Application
-----------

Demo Application to display Woodchipper logging using Zappa and Flask in AWS to log out to Cloudwatch.

- Requires Tackle DEV AWS Access to publish.
- Run `zappa update dev` to publish

Basic routes to test
- GET `/` basic hello world with logs
- GET `/error` invokes error and logs
- GET `/context` logs request with context
- GET `/sql-event` SQLAlchemy request with context

