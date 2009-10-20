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
import os.path
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
        # Handle errors when URL cannot be retreived.
        except IOError,e:
            if hasattr(e, 'reason'):
                message = "Unable to reach server: %s" % e.reason
            elif hasattr(e, 'code'):
                message = "Server unable to fulfil request: %s" % e.code
            elif hasattr(e, 'strerror'):
                message = "Server unable to fulfil request: %s" % e.strerror
            else:
                message = "Unknown error: Unable to retreive %s" % url
            return False, message

        # If we get here then the URL must have been retreived as all
        # exception conditions must return.
        local_file = open(bz2file, "w")
        local_file.write(response.read())
        local_file.close()
        return self.Extract_Moderated(config.moderated_shelve,
                                                      bz2file)
    def Extract_Moderated(self, dictfile, bz2file):
        """Sequentially decompress a Usenet active file and generate a
        persistent Shelve of the contents."""
        # If we don't have a compressed file to work from, just bail out.
        if not os.path.isfile(bz2file):
            error = "Unable to open %s" % bz2file
            return False, error
        # Open the persistent shelve to write changes to moderated groups
        # extracted from the bz2 compressed active file.
        dictobj = shelve.open(dictfile)
        local_file = bz2.BZ2File(bz2file, 'r')

        # Process each line of the bz2 active file and write moderated groups
        # to the shelve.
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
        return True, "Moderated shelve updated"

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
    retcode, message = test.GetUrl(config.active_url, config.active_bz2_file)
    print message
    print "Testing Moderated Group, (should return newsgroup)"
    print test.CheckModerated(['news.admin.net-abuse.policy'])
    print "Testing Unmoderated Group, (should return False)"
    print test.CheckModerated(['news.admin.net-abuse.usenet'])

# Call main function.
if (__name__ == "__main__"):
    test = moderated()
    main()
