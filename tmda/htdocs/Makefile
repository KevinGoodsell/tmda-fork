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
