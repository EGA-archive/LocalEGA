# Troubleshooting

* Use `-h` to see the possible options of each script, and `-v` for
  verbose output.

* If bootstrapping take more than a few seconds to run, it is usually
  because your computer does not have enough entropy. You can use the
  program `rng-tools` to solve this problem. E.g. on Debian/Ubuntu
  system, install the software by

	   sudo apt-get install rng-tools

  and then run

 	  sudo rngd -r /dev/urandom


