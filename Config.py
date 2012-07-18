#!/usr/bin/python
#
# vim: tabstop=4 expandtab shiftwidth=4 noautoindent
#
# nymserv.py - A Basic Nymserver for delivering messages to a shared mailbox
# such as alt.anonymous.messages.
#
# Copyright (C) 2012 Steve Crook <steve@mixmin.net>
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

import ConfigParser
import os
import sys


def makedir(d):
    """Check if a given directory exists.  If it doesn't, check if the parent
    exists.  If it does then the new directory will be created.  If not then
    sensible options are exhausted and the program aborts.

    """
    if not os.path.isdir(d):
        parent = os.path.dirname(d)
        if os.path.isdir(parent):
            os.mkdir(d, 0700)
            sys.stdout.write("%s: Directory created.\n" % d)
        else:
            msg = "%s: Unable to make directory. Aborting.\n" % d
            sys.stdout.write(msg)
            sys.exit(1)


# Configure the Config Parser.
config = ConfigParser.RawConfigParser()

# By default, all the paths are subdirectories of the homedir. We define the
# actual paths after reading the config file as they're relative to basedir.
config.add_section('paths')
homedir = os.path.expanduser('~')

# Logging
config.add_section('logging')
config.set('logging', 'level', 'info')
config.set('logging', 'format', '%(asctime)s %(levelname)s %(message)s')
config.set('logging', 'datefmt', '%Y-%m-%d %H:%M:%S')
config.set('logging', 'retain', 7)

# Config options for NNTP Posting
config.add_section('nntp')
config.set('nntp', 'injection_host', 'mail2news.domain.invalid')

config.add_section('thresholds')
config.set('thresholds', 'socket_timeout', 10)
config.set('thresholds', 'hours_past', 48)
config.set('thresholds', 'hours_future', 24)
config.set('thresholds', 'max_crossposts', 3)
config.set('thresholds', 'max_bytes', 200 * 1024)

# Try and process the .mail2newsrc file.  If it doesn't exist, we bailout
# as some options are compulsory.
if 'MAIL2NEWS' in os.environ:
    configfile = os.environ['NYMSERV']
else:
    configfile = os.path.join(homedir, '.mail2newsrc')
if os.path.isfile(configfile):
    config.read(configfile)
else:
    sys.stdout.write("%s: Config file does not exist\n" % configfile)
    sys.exit(1)

# Now we check the directory structure exists and is valid.
if config.has_option('paths', 'basedir'):
    basedir = config.get('paths', 'basedir')
else:
    basedir = os.path.join(homedir, 'mail2news')
    config.set('paths', 'basedir', basedir)
makedir(basedir)

if not config.has_option('paths', 'etc'):
    config.set('paths', 'etc', os.path.join(basedir, 'etc'))
makedir(config.get('paths', 'etc'))

if not config.has_option('paths', 'log'):
    config.set('paths', 'log', os.path.join(basedir, 'log'))
makedir(config.get('paths', 'log'))

if not config.has_option('paths', 'lib'):
    config.set('paths', 'lib', os.path.join(basedir, 'lib'))
makedir(config.get('paths', 'lib'))

if not config.has_option('paths', 'history'):
    config.set('paths', 'history', os.path.join(basedir, 'history'))
makedir(config.get('paths', 'history'))

if not config.has_option('paths', 'maildir'):
    config.set('paths', 'maildir', os.path.join(basedir, 'Maildir'))
maildir = config.get('paths', 'maildir')
makedir(maildir)
makedir(os.path.join(maildir, 'cur'))
makedir(os.path.join(maildir, 'new'))
makedir(os.path.join(maildir, 'tmp'))

# Define some defaults where options haven't been explicitly set.
if not config.has_option('nntp', 'messageid'):
    config.set('nntp', 'messageid', config.get('nntp', 'injection_host'))
if not config.has_option('nntp', 'path_header'):
    config.set('nntp', 'path_header',
               config.get('nntp', 'injection_host') + '!not-for-mail')
if not config.has_option('nntp', 'contact'):
    config.set('nntp', 'contact',
               'abuse@' + config.get('nntp', 'injection_host'))
if not config.has_option('nntp', 'default_from'):
    config.set('nntp', 'default_from',
               ('Unknown User <nobody@' +
                config.get('nntp', 'injection_host') + ">"))

with open('example.cfg', 'wb') as configfile:
    config.write(configfile)
