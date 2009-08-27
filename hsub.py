#!/usr/bin/python
#
# vim: tabstop=4 expandtab shiftwidth=4 autoindent
#
# Copyright (C) 2009 Steve Crook <steve@mixmin.net>
# $Id: hsub.py 25 2009-06-25 09:12:08Z crooks $
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

from hashlib import sha256
from os import urandom

class hsub:
    """The concept of hSub is to provide an alternative to the existing eSub.
    eSub relies on the patented IDEA cipher to generate an encrypted Subject
    for use in common mailboxes, (such as a Newsgroup).  hSub works on a
    similar principle but uses a SHA hash instead of IDEA."""

    def hash(self, text, iv = None, hsublen = 48):
        """Create an hSub (Hashed Subject). This is constructed as:
        --------------------------------------
        | 64bit iv | 256bit SHA2 'iv + text' |
        --------------------------------------"""
        # Generate a 64bit random IV if none is provided.
        if iv is None: iv = urandom(8)
        # Concatenate our IV with a SHA1 hash of text + IV.
        hsub = iv + sha256(iv + text).digest()
        return hsub.encode('hex')[:hsublen]

    def check(self, text, hsub):
        """Create an hSub using a known iv, (stripped from a passed hSub).  If
        the supplied and generated hSub's collide, the message is probably for
        us."""
        # We are prepared to check variable length hsubs within boundaries.
        # The low bound is the current Type-I esub length.  The high bound
        # is the 256 bits within SHA2-256.
        hsublen = len(hsub)
        # 48 digits = 192 bit hsub, the smallest we allow.
        # 80 digits = 320 bit hsub, the full length of SHA256 + 64 bit IV
        if hsublen < 48 or hsublen > 80:
            return False
        try:
            # The first 64 bits of an hSub are the IV.
            iv = hsub[:16].decode('hex')
        except TypeError:
            # Not all Subjects are hSub'd so just bail out if it's non-hex.
            return False
        # Return True if our generated hSub collides with the supplied
        # sample.
        return (self.hash(text, iv, hsublen) == hsub)

def main():
    """Only used for testing purposes.  We Generate an hSub and then check it
    using the same input text.  A returned True indicates a match."""
    text = "Testing"
    hsub = test.hash(text)
    print "hsub: " + hsub
    print "Length: %d" % len(hsub)
    print "Collision: %s" % test.check(text, hsub)

# Call main function.
if (__name__ == "__main__"):
    test = hsub()
    main()
