"""Sidebar generator.
"""

import sys
from types import StringType
from cStringIO import StringIO

# a useful constant
BLANKCELL = (None, '&nbsp;')



class Sidebar:
    def __init__(self, links):
        """Initialize the Sidebar instance.

        This class is indented to be a mixin-class with Skeleton.

        links must be a list of elements for the sidebar.  Each entry in the
        list can either be a string, indicating that the entry is a category
        header, or a 2-tuple of the form: (URL, text) indicating it is taken
        as a link to include under the category.

        If the entry is a two tuple, the URL can be None to indicate that
        there is no link to that text.

        """
        self.links = links

    def get_sidebar(self):
        stdout = sys.stdout
        html = StringIO()
        try:
            sys.stdout = html
            self.__start_table()
            self.__do_link()
            self.__finish()
        finally:
            sys.stdout = stdout
        return html.getvalue()

    def get_validated(self):
        return """<tr><td bgcolor="%s">
        <center>
        <a href="http://validator.w3.org/check/referer"><img border="0"
        src="http://www.w3.org/Icons/valid-html401"
        alt="Valid HTML 4.01!" height="31" width="88"%s</a></center>
        </td></tr>
        """ % (self.get_lightshade(), self.empty_tag_end)

    def __start_table(self):
        print '<!-- start of sidebar table -->'
        print '<table width="100%%" border="0" %s>' % self.get_sidebar_metrics()

    def __finish(self):
        print '</table><!-- end of sidebar table -->'

    def __do_link(self):
        itemnum = 1
        for item in self.links:
            if type(item) == StringType:
                # category header
                if (itemnum > 1) and self.use_spacers():
                    # get some separation between header and last item
                    print '<tr><td bgcolor="%s">&nbsp;</td></tr>' % (
                        self.get_lightshade())
                print '<tr>%s</tr>' % self.get_category(item, itemnum)
                itemnum += 1
            else:
                if len(item) == 3:
                    url, text, extra = item
                else:
                    url, text = item
                    extra = ''
                print self.get_item(url, text, extra)

    def get_sidebar_metrics(self):
        return 'cellspacing="0" cellpadding="3" bgcolor="%s"' % \
            self.get_bgcolor()

    def get_category(self, item, itemnum):
        return '<td bgcolor="%s"><b><font color="%s">%s</font></b></td>' % (
            self.get_darkshade(), self.get_bgcolor(), item)

    def get_item(self, url, text, extra):
        if url is None:
            s = text
        else:
            s = '<a href="%s">%s</a>' % (url, text)
        return '<tr><td bgcolor="%s">%s%s</td></tr>' % (
            self.get_lightshade(), s, extra)


from Skeleton import _Skeleton
from Banner import _Banner

class _Sidebar(_Skeleton, _Banner, Sidebar):
    def __init__(self, sitelinks, toclinks):
        _Banner.__init__(self, sitelinks)
        Sidebar.__init__(self, toclinks)

    def get_sidebar(self):
        return Sidebar.get_sidebar(self)

    def get_banner(self):
        return _Banner.get_banner(self)


if __name__ == '__main__':
    t = _Sidebar(
        # banner links
        [('page1.html', 'First Page'),
         ('page2.html', 'Second Page'),
         ('page3.html', 'Third Page'),
         ('page4.html', 'Fourth Page'),
         (None,         '<b>Fifth Page</b>'),
         ('page6.html', 'Sixth Page'),
         ],
        # sidebar links
        ['Special Topics',
         ('topics.html', 'Topic Guides'),
         ('download.html', 'Downloads'),
         ('windows.html', 'Windows'),
         ('jpython.html', 'JPython'),
         ('tkinter.html', 'Tkinter'),
         ('emacs.html', 'Emacs'),
         'See also',
         ('conferences.html', 'Python Conferences'),
         ('sitemap.html', 'Site map'),
         ('mirrors.html', 'Mirror sites'),
         (None, '<b>What is Python?</b>'),
         'Exits',
         ('starship.html', '(New) Starship'),
         ('starship.html', 'Old Starship'),
         ('cnri.html', 'CNRI'),
         'Email us',
         (None, 'For help with Python:'),
         ('help.html', 'python-help@python.org'),
         (None, 'For help with Website:'),
         ('web.html', 'webmaster@python.org'),
         (None, '<br>'),
         ('pp.html', '[Python Powered]'),
         ])

    print t.makepage()
