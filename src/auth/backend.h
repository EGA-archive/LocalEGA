#ifndef __LEGA_BACKEND_H_INCLUDED__
#define __LEGA_BACKEND_H_INCLUDED__

#include <stdbool.h>
#include <nss.h>
#include <pwd.h>

bool backend_open(int stayopen);

void backend_close(void);

enum nss_status backend_get_userentry(const char *name, struct passwd *result, char** buffer, size_t* buflen, int* errnop);

bool add_to_db(const char* username, const char* pwdh, const char* pubkey);

bool backend_authenticate(const char *user, const char *pwd);

#endif /* !__LEGA_BACKEND_H_INCLUDED__ */
