#!/usr/bin/env python

"""
Lists key(s) detail(s) visible to the supplied Pachube user API key

To use this script you must create a text file containing your API key 
and pass it to this script using the --keyfile argument as follows:

List all feeds visible to supplied key:
$ key_view.py --keyfile=/path/to/apikey/file

List a particular feed
$ key_view.py --keyfile=path/to/apikey/file --key=XXX
"""

import logging
import sys
from optparse import OptionParser
from twisted.internet import reactor, defer
try:
    from txpachube.client import Client
except ImportError:
    # cater for situation where txpachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from txpachube.client import Client
    


parser = OptionParser("")
parser.add_option("-k", "--keyfile", dest="keyfile", default=None, help="Path to file containing your Pachube API key")
parser.add_option("-i", "--key", dest="key_id", default=None, help="A specific Pachube key id to view")




@defer.inlineCallbacks
def demo(key, key_id):

    client = Client()

    try:
        if key_id:
            # request key details for the supplied identifier only
            logging.info("Requesting key details for key: %s" % key_id)
            dataStructure = yield client.read_api_key(api_key=key, key_id=key_id)  
        else:
            # request feed details for all feeds visible to the key supplied
            logging.info("Requesting a key listing")
            dataStructure = yield client.list_api_keys(api_key=key)
            
        logging.info("Received response from Pachube:\n%s\n" % dataStructure)
        
        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)
        
    except Exception, ex:
        logging.error("Error: %s" % str(ex))
        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(False)
    


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s : %(message)s")

    (options, args) = parser.parse_args()

    # confirm keyfile is suppplied and valid
    if options.keyfile is None:
        print parser.get_usage()
        sys.exit(1)
    
    keyfile = os.path.expanduser(options.keyfile)
    if not os.path.exists(keyfile):
        logging.error("Invalid API key file path: %s" % keyfile)
        sys.exit(1)
    
    fd = open(keyfile, 'r')
    key = fd.read().strip()
    fd.close()
   
    reactor.callWhenRunning(demo, key, options.key_id)
    reactor.run()

    