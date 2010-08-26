#!/usr/bin/python
#
# vim: tabstop=4 expandtab shiftwidth=4 noautoindent
#
# m2n.py -- This is the config file for the mail2news script
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

# This entry is the default added to the Path header.  If the message
# doesn't contain a Message-ID, this entry is used for the right side
# of that too.
path = 'mail2news.mixmin.net'

# Socket timeout in seconds.  This prevents the posting process from hanging
# forever if an NNTP server is not reachable.
timeout = 10

# The hosts to send the message to and the delivery method (ihave or post).
nntphosts = {}
nntphosts['localhost'] = ['.*', 'ihave']
nntphosts['news-in.mixmin.net'] = ['^alt\.anonymous\.messages|^alt\.privacy\.anon-server|^local\.|\.test', 'ihave']
nntphosts['news-in.glorb.com'] = ['^alt\.anonymous\.messages|^alt\.privacy\.anon-server', 'ihave']
nntphosts['news2.arglkargh.de'] = ['^alt\.anonymous\.messages|^alt\.privacy\.anon-server', 'ihave']

# Abuse contact to insert in X-Abuse-Contact.
abuse_contact = 'abuse@mixmin.net'

# Headers to strip from the message prior to posting.
bin_headers = ['To', 'Return-Path', 'Received', 'X-Original-To', 'Delivered-To',
'Content-Length', 'Lines', 'Xref', 'NNTP-Posting-Host',
'X-Spam-Checker-Version', 'X-Spam-Level', 'X-Spam-Status',
'X-Spambayes-Classification']

# Reject messages that contain one of these headers.
poison_headers = ['Control']

# Strip the following statements from the message payload.
bin_body = ['-----BEGIN TYPE III ANONYMOUS MESSAGE-----\nMessage-type: plaintext\n\n',
'-----END TYPE III ANONYMOUS MESSAGE-----\n']

# Test to append to each message in a comments header.
comments = """Mail2News Gateway"""

# Reject messages received from HELO's matching these strings.
poison_helo = []

# When validating a message sent to mail2news-yyyymmdd, how many hours in the
# past and future are considered valid.
hours_past = 48
hours_future = 24

# The maximum number of valid newsgroups that will be accepted in a crossposted message.
maxcrossposts = 3

# Maximum number of bytes in a message
maxbytes = 200000

# Reject messages containing this string in the Newsgroups header.
# Note: This doesn't have to be an entire newsgroup, just a string match.
poison_newsgroups = ['soc.culture.russian']
