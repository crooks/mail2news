#!/usr/bin/python
#
# vim: tabstop=4 expandtab shiftwidth=4 noautoindent
#
# m2n.py -- This is a simple mail2news script that accepts messages formatted
# with a Newsgroups header or delivered to a recipient in the format
# mail2news-yyyymmdd-news.group@domain.com
#
# Copyright (C) 2006 Steve Crook <steve@mixmin.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

import mail2news
import sys

def main():
    mail2news.init_parser()
    mail2news.init_logging()
    print "Type message here.  Finish with Ctrl-D."
    (mid, dest_server, payload) = mail2news.msgparse(sys.stdin.read())
    print payload
    mail2news.newssend(mid, dest_server, payload)

# Call main function.
if (__name__ == "__main__"):
    main()
