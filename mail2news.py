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

import config
import datetime
import random
import re
import email
import StringIO
import sys
import logging
import os.path
import socket
from email.Utils import formatdate
import nntplib
from optparse import OptionParser

def init_logging():
    """Initialise logging.  This should be the first thing done so that all
    further operations are logged."""
    loglevels = {'debug': logging.DEBUG, 'info': logging.INFO,
                'warn': logging.WARN, 'error': logging.ERROR}
    if loglevels.has_key(options.loglevel):
        level = loglevels[options.loglevel]
    else:
        level = loglevels['info']
    global logger
    logger = logging.getLogger('m2n')
    logpath = options.logpath.rstrip("/")
    logfile = "%s-%s-%s" % ymd()
    filename = "%s/%s" % (logpath, logfile)
    try:
        if not os.path.isfile(filename):
            lf = open(filename, 'w')
            lf.close()
            os.chmod(filename, 0644)
            logger.debug('Created new logfile %s', filename)
        hdlr = logging.FileHandler(filename)
    except IOError:
        print "Error: Unable to initialize logger.  Check file permissions?"
        sys.exit(1)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(level)

def init_parser():
    """Initialise the the Options Parser and read options.  It would be nice
    to do this after logging is initialised, but we need options in order to
    do that, so the egg must come before the chicken!"""
    parser = OptionParser()
    parser.add_option("-l", "--logpath", action = "store", type = "string",
                      dest = "logpath", default = config.logpath,
                      help = "Location of the log files.")
    parser.add_option("--histpath", action = "store", type = "string",
                      dest = "histpath", default = config.histpath,
                      help = "Location of history file")
    parser.add_option("--loglevel", action = "store", type = "string",
                      dest = "loglevel", default = config.loglevel,
                      help = "Logging level, (error, warn, notice, info, debug)")
    parser.add_option("-u", "--user", action = "store", type = "string",
                      dest = "user",
                      help = "Recipient of the message.")
    parser.add_option("-n", "--newsgroups", action = "store", type = "string",
                      dest = "newsgroups",
                      help = "Newsgroups to post the message in.")
    parser.add_option("--path", action = "store", type = "string",
                      dest = "path", default = config.path,
                      help = "Entry to use in Path header")
    parser.add_option("--helo", action = "store", type = "string",
                      dest = "helo",
                      help = "HELO/EHLO from sender.")
    parser.add_option("--nohist", action = "store_true", dest = "nohist",
                      default = False,
                      help = "Don't store messages in a history file")
    global options
    (options, args) = parser.parse_args()

def parse_recipient(user):
    """Check to see if the recipient of the email is in the format
    yyyymmdd-newsgroups.  If it is then return the decoded timestamp and
    newsgroups components, along with a True/Flase nospam indicator."""
    # Check that the header we are validating is username only with no domain
    # component.  If there is a domain, strip it off.
    domainchk = re.match('(.*)@', user)
    if domainchk:
        user = domainchk.group(1)
    userfmt = re.match('(mail2news|mail2news_nospam)\-([0-9]{8})\-(.*)', user)
    if userfmt:
        logger.info('Message has a correctly formatted recipient. Validating it.')
        recipient = userfmt.group(1)
        timestamp = userfmt.group(2)
        newsgroups = userfmt.group(3)
        # Replace = seperator with commas
        newsgroups = newsgroups.replace('=', ',')

        # Check to see if the header includes a 'nospam' instruction.
        nospam = False
        if recipient == 'mail2news_nospam':
            logger.info('Message includes a nospam directive.  Will munge headers accordingly.')
            nospam = True
        return timestamp, newsgroups, nospam
    else:
        logger.warn('Badly formatted recipient.  Rejecting message.')
        sys.exit(0)

def validate_stamp(stamp):
    """Validate that the timestamp decoded from the recipient details is both
    a valid timestamp and falls within acceptable time boundaries."""
    # Get timestamps for hours before and ahead of current UTC
    beforetime = datetime.datetime.utcnow() - \
      datetime.timedelta(hours=config.hours_past)
    aftertime = datetime.datetime.utcnow() + \
      datetime.timedelta(hours=config.hours_future)
    # Extract elements of the date stamp.
    year = int(stamp[0:4])
    month = int(stamp[4:6])
    day = int(stamp[6:8])
    # We don't know if the date is valid, just that it contains 8 numeric
    # digits.  If the Try succeeds, at least it is a parsable date.
    try:
        nowtime = datetime.datetime(year,month,day)
    except ValueError:
        logger.warn('Malformed date element. Rejecting message.')
        sys.exit(0)

    # By this point, the supplied date arg must be valid, but does
    # it fall within acceptable bounds?
    if nowtime > beforetime and nowtime < aftertime:
        logger.info('Timesstamp (%s) is valid and within bounds.', stamp)
        return True
    else:
        logger.warn('Timestamp (%s) is out of bounds.  Rejecting message.', stamp)
        sys.exit(0)

def ngvalidate(newsgroups):
    """Weed out rogue entries in the Newsgroups header.  This is more polite
    than feeding junk to the News servers."""
    newsgroups = newsgroups.rstrip(",")
    groups = newsgroups.split(',')
    goodng = [] # This will become a list of good newsgroups

    # Check each group is correctly formatted.  Drop those that aren't.
    for ng in groups:
        ng = ng.strip() # Strip whitespaces
        fmtchk = re.match('[a-z]{1,9}(\.[0-9a-z-+_]+)+$', ng)
        if fmtchk:
            if ng in goodng:
                logger.info("Duplicate newsgroup entry of %s.  Dropping one.", ng)
            else:
                goodng.append(ng)
        else:
            logger.info("%s is not a validated newsgroup, ignoring.", ng)

    # No point proceeding if there are no valid Newsgroups.
    if len(goodng) < 1:
        logger.warn("Message has no valid newsgroups.  Rejecting it.")
        sys.exit(0)

    # Create a valid entry for a Newsgroups header.  The first entry is just the
    # group name.  Subsequent ones are prefixed with a comma.
    header = goodng[0]
    for ng in range(1, len(goodng)):
        header = header + ',' + goodng[ng]
    logger.info("Validated Newsgroups header is: %s", header)

    # Check crosspost limit
    if len(goodng) > config.maxcrossposts:
        logger.warn('Message contains %d newsgroups, exceeding crosspost limit of %d. Rejecting.', len(goodng), config.maxcrossposts)
        sys.exit(0)
    # We return a list of good newsgroups, and a full comma-seperated header.
    return goodng, header

def extract_posting_hosts(allhosts, groups):
    """We expect to receive a dict of nntphosts and a list of groups. If each
    group in the list matches a regex, we include that host in a new dict
    called goodhosts.  This is returned in the required format for passing to
    our actual posting routine."""
    # These are the outgoing feed methods we understand.
    good_methods = ["post", "ihave"]
    goodhosts = {}
    for server in allhosts:
        # Reject a given server if we didn't get passed the two parameters
        # we require:- Regex Pattern and Posting Method.
        if len(allhosts[server]) == 2:
            pattern, method = allhosts[server]
        else:
            logger.warn("Invalid configuration for server %s", server)
            continue
        # Validate the feed method we are configured to use.
        if not method in good_methods:
            logger.warn("Unknown feed method for server %s", server)
            continue
        select = True
        for group in groups:
            match = re.search(pattern, group)
            if not match:
                # As we need all groups to match this pattern, there's no
                # point carrying on trying once one has failed.
                select = False
                break
        if select:
            logger.debug("Selecting host %s as a feed recipient with method %s", server, method)
            goodhosts[server] = method
    return goodhosts

def middate():
    """Return a date in the format yyyymmdd.  This is useful for generating
    a component of Message-ID."""
    utctime = datetime.datetime.utcnow()
    utcstamp = utctime.strftime("%Y%m%d%H%M%S")
    return utcstamp

def ymdh():
    """Return current year, month, day, hour."""
    utctime = datetime.datetime.utcnow()
    return utctime.year, utctime.month, utctime.day, utctime.hour

def ymd():
    """Return current year, month and date."""
    utctime = datetime.datetime.utcnow()
    return utctime.year, utctime.month, utctime.day


def midrand(numchars):
    """Return a string of random chars, either uc, lc or numeric.  This
    is used to provide randomness in Message-ID's."""
    randstring = ""
    while len(randstring) < numchars:
        rndsrc = random.randint(1,3)
        if rndsrc == 1:
            a = random.randint(48,57)
        elif rndsrc == 2:
            a = random.randint(65,90)
        elif rndsrc == 3:
            a = random.randint(97,122)
        randstring = randstring + chr(a)
    return randstring

def messageid():
    """Compile a valid Message-ID.  This should never be called outside
    of testing as a message cannot reach the gateway without an ID."""
    leftpart = middate() + "." + midrand(12)
    mid = '<' + leftpart + '@' + options.path + '>'
    return mid

def msgparse(message):
    """This routine is the engine room of the whole program.  It parses the
    message and if all is well, spits it out in a text format ready for
    posting."""
    
    # Use the email library to create the msg object.
    msg = email.message_from_string(message)

    # Check to see if we have a Message-ID.  If not, one is assigned
    # automatically.  This will generate a Warning as messages must have
    # valid ID's to have reached the gateway at all.
    if not msg.has_key('Message-ID'):
        msg['Message-ID'] = messageid()
        logger.warn('Processing message with no Message-ID.  Assigning %s.' % msg['Message-ID'])
    else:
        logger.info('Processing message %s' % msg['Message-ID'])

    # Before anything else, lets write the message to a history file so that
    # we have a means to see why messages succeeded or failed.  This is very
    # useful during testing, but can be run with a nohist switch in prod.
    if not options.nohist:
        histpath = options.histpath.rstrip("/")
        histfile = "%s-%s-%s" % ymd()
        filename = "%s/%s" % (histpath, histfile)
        try:
            if not os.path.isfile(filename):
                hf = open(filename, 'w')
                hf.close()
                os.chmod(filename, 0644)
                logger.debug('Created new history file: %s', filename)
        except IOError:
            logger.error("Unable to initialize history file.  Check file permissions?")
        hist = open(filename, 'a')
        hist.write(message)
        hist.write('\n')
        hist.close()
    else:
        logger.info("Message not logged due to --nohist switch.")

    # Check to see if the client HELO is blacklisted.  This only works if the
    # HELO is passed by the MTA to the program.
    if options.helo:
        helo = blacklist(options.helo, config.poison_helo)
        if helo:
            logger.warn('Message received from blacklisted relay %s.  Rejecting it.', helo)
            sys.exit(0)

    # Check for poison headers in the message.  Any of these will result in the
    # message being rejected.
    for header in config.poison_headers:
        if msg.has_key(header):
            logger.warn("Message contains a blacklisted %s header. Rejecting it.", header)
            sys.exit(0)

    # Check for blacklisted From headers.
    fr = blacklist(msg['From'], config.poison_from)
    if fr:
        logger.warn("Rejecting due to blacklisted From \'%s\'", fr)
        sys.exit(0)

    # In priority order (highest first) look for the recipient details in these
    # headers or parameters.  Using To or Cc is nothing but a nasty last-ditch
    # option and shouldn't be used.
    recipients = [options.user, msg['X-original-To'], msg['To'], msg['Cc']]
    recipient = find_recipient(recipients)

    # Lets assume we're not running in NoSpam mode until something
    # proves we are.
    nospam = False

    # Check for a Newsgroups header.  If there isn't one, then check for a
    # valid recipient in the correct format and with a valid timestamp.
    if options.newsgroups:
        dest = options.newsgroups
        logger.debug("Newsgroups passed as arguement: %s", dest)
        if msg.has_key('Newsgroups'):
            logger.info("Newsgroups header overridden by --newsgroups arguement")

    elif msg.has_key('Newsgroups'):
        dest = msg['Newsgroups']
        del msg['Newsgroups']
        logger.debug('Message has a Newsgroups header of %s', dest)
        if recipient.startswith('mail2news_nospam'):
            nospam = True
            logger.info('Message includes a nospam directive.  Will munge headers accordingly.')
    else:
        logger.info('No Newsgroups header, trying to parse recipient information.')
        (stamp, dest, nospam) = parse_recipient(recipient)
        # Check to see if the timestamp extracted from the recipient is valid.
        if not validate_stamp(stamp):
            logger.warn('No Newsgroups header or valid recipient.  Rejecting message.')
            sys.exit(0)

    # Clean the newsgroups list by checking that each element seperated by ','
    # are in an accepted newsgroup format.
    groups, msg['Newsgroups'] = ngvalidate(dest)

    # If the message doesn't have a Date header, insert one.
    if not msg.has_key('Date'):
        logger.info("Message has no Date header. Inserting current timestamp.")
        msg['Date'] = formatdate()

    # If the message doesn't have a From header, insert one.
    if not msg.has_key('From'):
        logger.info("Message has no From header. Inserting a null one.")
        msg['From'] = 'Unknown User <nobody@mixmin.net>'
    else:
        logger.info("From: %s", msg['From'])

    # If we are in nospam mode, edit the From header and create an
    # Author-Supplied-Address header.
    if nospam:
        name,addy = fromparse(msg['From'])
        if addy:
            del msg['Author-Supplied-Address']
            del msg['From']
            msg['Author-Supplied-Address'] = addy
            msg['From'] = name + '<Use-Author-Supplied-Address-Header@[127.1]>'

    # If the message doesn't have a Subject header, insert one.
    if not msg.has_key('Subject'):
        logger.info("Message has no Subject header. Inserting a null one.")
        msg['Subject'] = 'None'
    else:
        logger.info("Subject: %s", msg['Subject'])

    # Check for preloaded Path headers, these are legal but unusual.
    if msg.has_key('Path'):
        logger.info("Message has a preloaded path header of %s", msg['Path'])

    # If the message has an X-Newsserver header, use the specified posting host
    # instead of the default servers.
    # TODO probably should do some error checking of the supplied hostname:port
    if msg.has_key('X-Newsserver'):
        logger.info("Message directs posting to %s. Adding Comment header.", msg['X-Newsserver'])
        comment1 = "A user of this Mail2News Gateway has issued a directive to force posting through %s." % msg['X-Newsserver']
        comment2 = " If this is undesirable, please contact the administrator at the supplied abuse address."
        if not msg.has_key('Comments'):
            logger.debug("Assigned header: Comments")
            msg['Comments'] = comment1 + comment2
        else:
            for free_comment in range(1,99):
                comments_header = 'Comments' + str(free_comment)
                if not msg.has_key(comments_header):
                    msg[comments_header] = comment1 + comment2
                    logger.debug("Assigned header: %s", comments_header)
                    break
        dest_server = {msg['X-Newsserver']: 'post'}
    else:
        # If we don't have an X-Newserver header, we use our configured nntphosts
        # dictionary.
        dest_server = extract_posting_hosts(config.nntphosts, groups)


    # Check for blacklisted Newsgroups
    ng = blacklist(msg['Newsgroups'], config.poison_newsgroups)
    if ng:
        logger.warn("Rejecting message due to blacklisted Newsgroup \'%s\' in distribution.", ng)
        sys.exit(0)
    
    # Look for headers to remove from the message.
    for header in config.bin_headers:
        del msg[header]

    # Add additional headers relating to the mail2news gateway.
    try:
        msg['Path'] = options.path
    except:
        logger.error('Cannot assign domain to Path header. We must have one to proceed.')
        sys.exit(1)
    try:
        msg['X-Abuse-Contact'] = config.abuse_contact
    except:
        logger.warn("We don't appear to have an abuse contact address.  This will make recipients of abuse feel sad.")
    
    # The following section parses the message payload.  Remove
    # them to pass the payload unchanged.
    if msg.is_multipart():
        logger.info('This is a multipart message.  Bypassing payload parsing.')
    else:
        payload = msg.get_payload(decode=1)
        msg.set_payload(body_parse(payload))

    return msg['Message-ID'], dest_server, msg.as_string()

def blacklist(item, list):
    """Check for headers that contain a blacklisted string."""
    for name in list:
        if item.find(name):
            return name
    return False

def body_parse(body):
    """Parse the message body and replace selected strings. This isn't
    always considered acceptable practice as the body belongs to the sender.
    Only delimiter-type strings should be tweeked."""
    oldbody = body
    for string in config.bin_body:
        body = body.replace(string, "")
    if oldbody <> body:
        logger.info('Payload has been modified due to matching remove strings.')
    return body

def find_recipient(recipients):
    """Our recipient info could be supplied from a number of headers or passed
    as an arguement.  We need to find the best-matching one using an order of
    preference where first match is best."""
    for recipient in recipients:
        if recipient:
            if recipient.startswith('mail2news'):
                logger.debug('Selected recipient is %s', recipient)
                return recipient
    logger.debug('Recipient is not mail2news. Returning an arbitrary value.')
    return 'foobar'

def fromparse(fromhdr):
    """This does the good old mail2news_nospam processing to extract the name
    and address out of the From header so they can be split into the From and
    Author-Supplied-Address headers."""
    addy = False
    name = False
    matched = False
    fmt = re.match('([^<>]*)<([^<>\s]+@[^<>\s]+)>$', fromhdr)
    if fmt:
        name = fmt.group(1)
        addy = fmt.group(2)
        matched = True
    fmt = re.match('([^<>\s]+@[^<>\s]+)\s+\(([^\(\)]*)\)$', fromhdr)
    if fmt and not matched:
        name = fmt.group(2)
        addy = fmt.group(1)
        matched = True
    fmt = re.match('([^<>\s]+@[^<>\s]+)$', fromhdr)
    if fmt and not matched:
        name = ""
        addy = fmt.group(1)
    if addy:
        addy = addy.replace('.', '<DOT>')
        addy = addy.replace('@', '<AT>')
    return name,addy

def newssend(mid, nntphosts, content):
    """Time to send the message using either IHAVE or POST for each defined
    recipient of the message.  We also do a crude size check."""
    size = len(content)
    if size > config.maxbytes:
        logger.warn('Message exceeds %d size limit. Rejecting.', config.maxbytes)
        sys.exit(0)
    logger.debug('Message is %d bytes', size)
    # Socket timeout prevents processes hanging forever if an NNTP server is
    # unreachable.
    socket.setdefaulttimeout(config.timeout)
    for host in nntphosts:
        payload = StringIO.StringIO(content)
        logger.debug("Attempting delivery to %s", host)
        if nntphosts[host] == 'ihave':
            try:
                s = nntplib.NNTP(host)
                logger.debug("IHAVE process connected to %s", host)
            except:
                logger.error("Error during IHAVE connection to %s. %s",  host, sys.exc_info()[1])
                continue
            try:
                s.ihave(mid, payload)
                logger.info("%s successful IHAVE to %s." % (mid, host))
            except nntplib.NNTPTemporaryError:
                logger.info("IHAVE to %s returned: %s", host, sys.exc_info()[1])
            except nntplib.NNTPPermanentError:
                logger.warn("IHAVE to %s returned a permanent error: %s", host, sys.exc_info()[1])
            except:
                logger.error("IHAVE to %s returned an unknown error: %s %s", host, sys.exc_info()[0], sys.exc_info()[1])
        else:
            try:
                s = nntplib.NNTP(host, readermode=True)
            except:
                logger.error("Error during POST connection to %s. %s",  host, sys.exc_info()[1])
                continue
            try:
                s.post(payload)
                logger.info("%s successful POST to %s." % (mid, host))
            except nntplib.NNTPTemporaryError:
                logger.info("POST to %s returned: %s", host, sys.exc_info()[1])
            except nntplib.NNTPPermanentError:
                logger.warn("POST to %s returned a permanent error: %s", host, sys.exc_info()[1])
            except:
                logger.error("POST to %s returned an unknown error: %s %s", host, sys.exc_info()[0], sys.exc_info()[1])
