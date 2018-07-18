## Testing script

Testing script is used to replicate upload and submission functionalities from an end user.
If you are running the script after using the "Somewhat Easy" deployment using the `deploy.py` script,
use the same password provided for the CEGA Users RSA key.
your own in the `Makefile`. Also `MAIN_REPO=~/LocalEGA` should reflect the path do the LocalEGA project.

The actual test:
```
make upload
make submit
```

Other option: `make clean` to remove generate files.
