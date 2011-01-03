#!/usr/bin/python
#
# vim: tabstop=4 expandtab shiftwidth=4 autoindent
#
# Copyright (C) 2009 Steve Crook <steve@mixmin.net>
# $Id$
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

import os.path
import shelve

ACTIVE = '/usr/local/news/db/active'
HOMEDIR = os.path.expanduser('~')
MODFILE = os.path.join(HOMEDIR, 'db', 'moderated.db')

mod = shelve.open(MODFILE, flag='n')
f = open(ACTIVE, 'r')
for line in f:
    fields = line.rstrip().split(' ')
    if len(fields) == 4:
        if fields[3] == 'm':
            grp = fields[0]
            mod[grp] = 1
print "%d: Moderated groups written" % len(mod)
mod.close()
f.close()
