#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>
#include <errno.h>
#include <sys/stat.h>
#include <pwd.h>
#include <unistd.h>

#include "debug.h"
#include "config.h"

static bool
make_parent_dirs(const char *dir, int make)
{
  int rc = true;
  struct stat st;

  char *cp = strrchr(dir, '/');
  
  if (!cp || cp == dir) return rc;
  
  *cp = '\0';
  if (stat(dir, &st) && errno == ENOENT)
    rc = make_parent_dirs(dir, 1);
  *cp = '/';
  
  if (rc) return rc;
  
  if (make && mkdir(dir, 0755) && errno != EEXIST) {
    D("unable to create directory %s", dir);
    return false;
  }
  
  return rc;
}

void
create_homedir(struct passwd *pw){

  struct stat st;

  /* If we find something, we assume it's correct and return */
  if (stat(pw->pw_dir, &st) == 0){
    D("homedir already there: %s\n", pw->pw_dir);
    return;
  }

  if (!make_parent_dirs(pw->pw_dir, 0)){
    D("Could not create homedir %s\n", pw->pw_dir);
    return;
  }
  
  /* Create the new directory */
  if (mkdir(pw->pw_dir, 0750) && errno != EEXIST){
    D("unable to create directory %s\n", pw->pw_dir);
    return;
  }

  if (chown(pw->pw_dir, 0, pw->pw_gid) != 0){
    SYSLOG("unable to change permissions: %s", pw->pw_dir);
    return;
  }

  /* See if we need to copy the skel dir over. */
  /* cp options->skel into homedir */
  /* if (strcmp(dent->d_name,".") == 0 || */
  /*     strcmp(dent->d_name,"..") == 0) */
  /*   continue; */

  /* Creating the inbox */
  char* inboxdir = (char*)malloc(sizeof(char*));
  if(inboxdir == NULL){ D("unable to create inbox directory\n"); return; }
  sprintf(inboxdir, "%s/inbox", pw->pw_dir);
  if (mkdir(inboxdir, 0700) && errno != EEXIST){
    D("unable to create inbox directory %s\n", inboxdir);
  }
  if (chown(inboxdir, pw->pw_uid, pw->pw_gid) != 0){
    D("unable to change permissions: %s\n", inboxdir);
  }
  free(inboxdir);
  
  D("homedir created: %s\n", pw->pw_dir);
  return;
}
