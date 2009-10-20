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

from urllib2 import Request, urlopen
import shelve
import bz2
import config
import socket

class moderated:
    """Moderated Newsgroups need to be handled differently to unmoderated
    ones.  When the distribution contains a moderated group, posting should
    be emailed to the group moderator instead of posting it.  The functions
    within this class retrieve the Usenet active file and extract a dictionary
    of moderated groups.  Posts can then be checked against that dict."""

    def GetUrl(self, url, bz2file):
        """Retreive the current Usenet active file."""
        process = False
        socket.setdefaulttimeout(config.timeout)
        req = Request(url)
        try:
            response = urlopen(req)
            process = True
        except IOError,e:
            if hasattr(e, 'reason'):
                print "Unable to reach server: %s" % e.reason
            elif hasattr(e, 'code'):
                print "Server unable to fulfil request: %s" % e.code
            elif hasattr(e, 'strerror'):
                print "Server unable to fulfil request: %s" % e.strerror
            else:
                print "Unknown error: Unable to retreive %s" % url
        if process:
            local_file = open(bz2file, "w")
            local_file.write(response.read())
            local_file.close()
            self.Extract_Moderated(config.moderated_shelve, bz2file)

    def Extract_Moderated(self, dictfile, bz2file):
        """Sequentially decompress a Usenet active file and generate a
        persistent Shelve of the contents."""
        dictobj = shelve.open(dictfile)
        local_file = bz2.BZ2File(bz2file, 'r')
        for line in local_file:
            grp, high, low, flag = line.rstrip().split(" ")
            if flag == 'm':
                if grp in dictobj:
                    continue
                else:
                    dictobj[grp] = 1
            else:
                if grp in dictobj:
                    del dictobj[grp]
        local_file.close()
        dictobj.close()

    def CheckModerated(self,
                       grouplist,
                       dictfile = config.moderated_shelve):
        """Take a list of group names and check if any of them are moderated.
        Should any of the list be moderated, the function will return the
        first moderated group in the distribution."""
        dictobj = shelve.open(dictfile)
        match = False
        for group in grouplist:
            if group in dictobj:
                match = group
                break
        dictobj.close()
        return match

def main():
    print "Retrieving URL"
    test.GetUrl(config.active_url, config.active_bz2_file)
    print "Testing Moderated Group, (should return newsgroup)"
    print test.CheckModerated(['news.admin.net-abuse.policy'])
    print "Testing Unmoderated Group, (should return False)"
    print test.CheckModerated(['news.admin.net-abuse.usenet'])

# Call main function.
if (__name__ == "__main__"):
    test = moderated()
    main()
