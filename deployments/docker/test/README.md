## Testing script

Testing script is used to replicate upload and submission functionalities from an end user.
Before using the script make sure there is a key `~/.ssh/lega.pub` and `~/.ssh/lega` or replace them with
your own in the `Makefile`. Also `MAIN_REPO=~/LocalEGA` should reflect the path do the LocalEGA project.

Using the script:
```
make user
make upload
make submit
```
