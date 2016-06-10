# yellow-tools

A collection of little scripts that make developing for jujucharms.com easier.

[charmcheck.py](charmcheck.py)
------------------------------

Checks the status of a charm-id across the many systems we care about: legacy
charmstore, charmworld, staging charmstore, and production charmstore.

Usage:

`charmcheck.py charm-id`

Example:

`charmcheck.py "~bac/precise/charmworld"`

[jujucharms-status.sh](jujucharms-status.sh)
--------------------------------------------

Checks the status information across many microservices.

Usage:

`jujucharms-status.sh` (checks production)

`jujucharms-status.sh staging` (checks staging)

Requirements:
[httpie](https://pypi.python.org/pypi/httpie)


[lxd-launch](lxd-launch)
------------------------

Creates a new lxd instance and binds your host home directory.

Usage:

`lxd-launch <image> <name>`

for example:

`lxd-launch ubuntu:wily wily-test`

Note the script is not idempotent. If an instance has already been created,
you can just use the `lxc` tools to start and stop it but you don't need to
recreate it.  The home directory remains bound even if you start/stop the
instance.

[lxd-ssh](lxd-ssh)
------------------------

Creates a new lxd instance and binds your host home directory.

Usage:

`lxd-ssh <name>`

for example:

`lxd-ssh wily-test`

If multiple instances match the searched name, the first will be used.  For instance if you have `trusty` and `trusty2`, then `lxd-ssh trusty` will connect to the `trusty` instance.

[uitest-runner.sh](uitest-runner.sh)
------------------------------------

Run uitest with an opininated set of options and shortcuts for the system to
test.

Usage:

```
cd $MYGITREPO/juju-uitest
make
uitest-runner.sh system [test]
```

The value for `system` can be 'production' or 'staging'. If it is omitted or
anything else, then GUIMAAS will be used.

The optional `test` parameter is the name of a single test to run. If blank,
all tests are run.

You'll need to create a file `$HOME/.uitest-creds` with:

```
credentials=LPUSERNAME:LPPASSWORD
admin=admin:ADMINPASSWORD
```
