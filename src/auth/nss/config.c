#include "nss-ega.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>

#define HASHMAX 73
#define CFGLINEMAX 512

static char *_options[HASHMAX];
static unsigned int _confisopen = 0;

/*
 * create a simple hash from a string
 */
unsigned int texthash(const char *str)
{
  int i, s;
  
  for(i = s = 0; str[i]; i++) {
    s += str[i];
  }
  
  return s % HASHMAX;
}

/*
 * read configfile and save values in hashtable
 */
int readconfig(char* configfile)
{
  FILE *cf;
  char line[CFGLINEMAX], key[CFGLINEMAX], val[CFGLINEMAX], *c;
  unsigned int h;
  unsigned int lineno = 0;

  // Choose whether we are dealing with the shadow section or not
  if(_confisopen) {
    for(h = 0; h < HASHMAX; h++) {
      free(_options[h]);
    }
  }
  h = 0;
  while(h < HASHMAX) {
    _options[h] = NULL;
    ++h;
  }
  
  if(!(cf = fopen(configfile, "r"))) {
    DBGLOG("could not open config file  %s\n", configfile);
    return errno;
  }

  while(fgets(line, CFGLINEMAX, cf)) {
    lineno++;

    /* remove comments */
    c = strstr(line, "#");
    if(c) {
      line[c-line] = 0;
    }
    
    if (*line == 0 || *line == '\n')
      continue;
    
    /* read options */
    if(sscanf(line, " %s = %[^\n]", key, val) < 2) {
      DBGLOG("line %d in %s is unparseable: \"%s\"\n", lineno, configfile, line);
    } else {
      h = texthash(key);
      if (_options[h] != NULL ) {
	DBGLOG("line %d in %s is a duplicate hash: \"%s\"\n", lineno, configfile, key);
      } else {
	_options[h] = malloc(strlen(val)+1);
	strcpy(_options[h], val);
      }
    }
  }
  fclose(cf);

  _confisopen = 1;
  atexit(cleanup);

  return 0;
}

/*
 * free the hashmap, close connection to db if open
 */
void cleanup(void)
{
  int i;

  if(_confisopen) {
    for(i = 0; i < HASHMAX; i++) {
      free(_options[i]);
      _options[i] = NULL;
    }
  }
  _confisopen = 0;

  while(backend_isopen()) {
    backend_close();
  }
}


/*
 * get value for 'key' from the hashmap
 */
inline char *getcfg(const char *key)
{
  return _options[texthash(key)] ? _options[texthash(key)] : "";
}
