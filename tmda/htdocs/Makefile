# Copyright (C) 2001-2006 Jason R. Mastaler <jason@mastaler.com>
#
# This file is part of TMDA.
#
# TMDA is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.  A copy of this license should
# be included in the file COPYING.
#
# TMDA is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with TMDA; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

DEF2HTML =      ../contrib/def2html

SOURCES =	config-vars.html
TARGETS =	config-vars.html

DEST =          jason@tmda.net:/www/tmda.net/htdocs
EXCLUDES =      --exclude "*"
INCLUDES =	--include "*.html" --include "*.css"
ARGS =          -e ssh -v -a -z --delete $(INCLUDES) $(EXCLUDES)

all: 		$(TARGETS)

config-vars.tmp: ../TMDA/Defaults.py
		$(DEF2HTML) ../TMDA/Defaults.py > config-vars.tmp

config-vars.html: config-vars.tpl config-vars.tmp
		sed -e '/<!--config_vars-->/r config-vars.tmp' -e \
		'/<!--config_vars-->/d' < config-vars.tpl > config-vars.html

clean: 		
		-rm -f *~
		-rm -f config-vars.tmp

remake: 	clean all

install: 
		rsync $(ARGS) . $(DEST)
