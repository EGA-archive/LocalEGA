## Testing script

Testing script is used to replicate upload and submission functionalities from an end user.
Before using the script make sure there is a key `~/.ssh/lega.pub` and `~/.ssh/lega` or replace them with
your own in the `Makefile`. Also `MAIN_REPO=~/LocalEGA` should reflect the path do the LocalEGA project.

Using the script:
Generate RSA YML file
```
make user
```
the output will be in `deployments/kube/yml/cega-users/ega-box-999.yml`.
Copy the file contents to like 152 of the cm.cega.yml file.
After this the we can start the `kubectl create -f ../yml/cega-users --namespace=testing`

The actual test:
```
make upload
make submit
```
