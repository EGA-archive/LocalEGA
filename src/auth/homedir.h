#ifndef __LEGA_HOMEDIR_H_INCLUDED__
#define __LEGA_HOMEDIR_H_INCLUDED__

#include <stdbool.h>
#include <pwd.h>

void create_homedir(struct passwd *pw);

#endif /* !__LEGA_HOMEDIR_H_INCLUDED__ */
