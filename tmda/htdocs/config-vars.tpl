Title: TMDA Configuration Variables
Links: overview-links.h usage-links.h config-links.h support-links.h

<h3>TMDA Configuration Variables</h3>

<ul>

<li>Set TMDA configuration variables in /etc/tmdarc or ~/.tmda/config only.
Settings in ~/.tmda/config override those in /etc/tmdarc.
<br><br>

<li>Each variable has a default value, and in most cases that will suffice.
You only need to set a variable in your configuration file if you want to
override the default value.
<br><br>

<li>/etc/tmdarc and ~/.tmda/config are interpreted as executable Python code.
Thus, variable declarations must adhere to proper 
<a href="http://www.python.org/doc/current/" TARGET="Resource Window">Python syntax</a>.
Each variable definition below contains one or more examples.

</ul>

<h3>Index</h3>

<!--config_vars-->
