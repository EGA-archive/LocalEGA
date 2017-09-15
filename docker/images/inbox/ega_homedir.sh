#!/bin/bash

echo "EGA homedir for $PAM_USER: Running as $(whoami)"

[[ "$PAM_USER" = "ega" ]] && echo "Welcome ega...ok...not touching your homedir" && exit 0

[[ -z "$PAM_USER" ]] && exit 2

echo "EGA homedir: Running as $(whoami)"

skel=/ega/skel 
umask=0022

if [[ ! -d ~$PAM_USER ]]; then
   mkdir -p ~$PAM_USER
   cp -a $skel/. ~$PAM_USER

   chown root:ega ~$PAM_USER
   chmod 750 ~$PAM_USER
   chown -R ega:ega ~$PAM_USER/*
else
   echo "Not touching the homedir: $HOME"
fi
