/* tmda-cgi.c

Copyright (C) 2002 Gre7g Luterman <gre7g@wolfhome.com>

This file is part of TMDA.

TMDA is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.  A copy of this license should
be included in the file COPYING.

TMDA is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with TMDA; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307 USA */

#include <stdlib.h>

#include "dirs.h"

int main(int argc, char *argv[])
{
#ifdef TMDARC
  putenv(TMDARC);
#endif
#ifdef AUTH_ARG
  putenv(AUTH_TYPE);
  putenv(AUTH_ARG);
  #ifdef AUTH_TRUE
  putenv(AUTH_TRUE);
  #endif
#endif
  putenv(MODE);
  putenv(USER);
  putenv(DISP_DIR);
  putenv(BASE_DIR);

  if (!chdir(INSTALL))
  {
    execl(PYTHON, PYTHON, "tmda-cgi.py", 0);
    return 0;
  }
  printf("Content-type: text/html\n\nCannot change to directory: %s", INSTALL);
  return 1;
}
