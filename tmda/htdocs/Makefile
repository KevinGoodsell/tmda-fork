# Copyright (C) 2001,2002 Jason R. Mastaler <jason@mastaler.com>
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

HTROOT = 	.
HT2HTML =	/usr/local/packages/ht2html/ht2html.py
HTSTYLE =	TMDAGenerator
HTALLFLAGS =	-f -s $(HTSTYLE)
HTFLAGS =	$(HTALLFLAGS) -r $(HTROOT)

SOURCES =	$(shell echo *.ht)
TARGETS =	$(filter-out *.html,$(SOURCES:%.ht=%.html)) $(EXTRA_TARGETS)
GENERATED_HTML= $(SOURCES:.ht=.html)

.SUFFIXES:	.ht .html

.ht.html:
	$(HT2HTML) $(HTFLAGS) $<

all: $(TARGETS)

clean: clean
	-rm -f *~
	-rm -f $(GENERATED_HTML)

remake: clean all
