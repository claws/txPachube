#!/usr/bin/env python

#
# This script provides a sequential, live, test of the client functionality.
# It is a fairly comprehensive test of the JSON format aspect of the client API.
#
# It performs a sequence of steps that:
#  1. Read API key details to check if the supplied key can perform all the following actions
#
#  2. Read API key list
#  3. Create an API key
#  4. Read the API key details
#  5. Delete the API key
#
#  6. Read a list of feeds visible to the API key
#  7. Create a new feed
#  8. Read the feed details
#  9. Update the feed
# 10. Read the updated feed details
#
# 11. Create a datastream
# 12. Read the datastream details
# 13. Update the datastream
# 14. Read the updated datastream details
#
# 15. Create a datapoint
# 16. Read the datapoint details
# 17. Update the datapoint
# 18. Read the updated datapoint details
# 19. Delete the datapoint
#
# 20. Create a trigger
# 21. Read the trigger details
# 22. Update the trigger
# 23. Read the updated trigger details
# 24. Delete the trigger
#
# 25. Delete the datastream
# 26. Delete the feed
#

# XX. Users - to do
#


import datetime
from optparse import OptionParser
from twisted.internet import reactor, defer
import logging
import traceback
try:
    import txpachube
    import txpachube.client
except ImportError:
    # cater for situation where txpachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import txpachube
    import txpachube.client

    
    
parser = OptionParser("")
parser.add_option("-k", "--keyfile", dest="keyfile", default=None, help="Path to file containing your Pachube API key")



@defer.inlineCallbacks
def demo(user_api_key):
    """ Perform the txpachube.client.Client tests """
    
    user_api_key_id = None
    user_api_key_found = False
    required_permissions = [u'get', u'put', u'post', u'delete']
    required_permissions_available = True
    
    client = txpachube.client.Client()
    
    
    ################################################################################
    # Api Keys 
    ################################################################################
    
    
    # check that supplied key has appropriate permissions for the test. 
    try:
        logging.info("Requesting details of the supplied API key")
        apikey = yield client.read_api_key(api_key=user_api_key, key_id=user_api_key)
        logging.info("Received API key:\n%s\n" % apikey)
        
        # Multiple access_methods declarations can exist within a permissions dict.
        # Create a consolidated list that can be checked once.
        consolidated_access_methods = []
        for permission in apikey.permissions:
            for method in permission.access_methods:
                if method not in consolidated_access_methods:
                    consolidated_access_methods.append(method)        
        
        for required_permission in required_permissions:
            if required_permission not in consolidated_access_methods:
                logging.error("The supplied key does not have the %s permission which is required" % required_permission)
                defer.returnValue(False)
                
        logging.info("The supplied API key supports the required permissions for this test")
        
    except Exception, ex:
        logging.error("Error reading key details: %s" % str(ex))
        defer.returnValue(False)    
    
    
    # Getting to this point means that the supplied API key holds the required permissions
    # to perform all the actions in the rest of the demo.
    
    
    # obtain a list of keys that are visible to the supplied key
    try:
        logging.info("Requesting API key list visible to the supplied key")
        api_key_list = yield client.list_api_keys(api_key=user_api_key)
        logging.info("Received API key list:\n%s\n" % api_key_list)     
    except Exception, ex:
        logging.error("Error listing keys: %s" % str(ex))   


    # create a new api key
    try:
        candidate_key = txpachube.Key(label='temp key', permissions=[{'access_methods' : [u'get']}])
        logging.info("Requesting a new key be created")
        created_key_id = yield client.create_api_key(api_key=user_api_key, data=candidate_key.encode())
        logging.info("Received new API key: %s" % created_key_id)
        
        if created_key_id:
            
            # read the newly created key
            try:
                logging.info("Requesting details for new key using key_id: %s" % created_key_id)
                read_key = yield client.read_api_key(api_key=user_api_key, key_id=created_key_id)
                logging.info("Received API key:\n%s\n" % read_key)
            except Exception, ex:
                logging.error("Error reading new key details: %s" % str(ex))
            
            # delete the newly created key
            try:
                logging.info("Deleting the created key with key_id: %s" % created_key_id)
                delete_success = yield client.delete_api_key(api_key=user_api_key, key_id=created_key_id)
                logging.info("Received delete key result: %s" % delete_success)
            except Exception, ex:
                logging.error("Error deleting new key: %s" % str(ex))
                            
        else:
            logging.info("Can't read or delete new key as no key id was returned for the new key")
            
    except Exception, ex:
        logging.error("Problem creating new API key: %s" % str(ex))
    
    
    
    ################################################################################
    # Feeds
    ################################################################################ 
    

    # list some feeds visible to this key    
    try:        
        logging.info("Requesting a feed list")
        environment_list = yield client.list_feeds(api_key=user_api_key, parameters={'per_page' : 1, 'status' : 'live'})
        logging.info("Success retrieving a feed list:\n%s\n" % environment_list)
    except Exception, ex:
        logging.error("Error retrieving feed list: %s" % str(ex))
    
            
    # create a new feed    
    try:
        logging.info("Creating a new feed")
        environment = txpachube.Environment(title="A Temporary Test Feed", version="1.0.0")
        new_feed_id = yield client.create_feed(api_key=user_api_key, data=environment.encode())
        if new_feed_id:
            logging.info("Success creating a new feed. New feed id is: %s" % new_feed_id)
        else:
            logging.error("Problem occurred creating the new feed")
    except Exception, ex:
        logging.error("Error creating feed: %s" % str(ex))
        defer.returnValue(False)
        
    if new_feed_id:
        
        # read the new feed details  
        try:
            logging.info("Requesting details of the created feed %s" % new_feed_id)
            environment = yield client.read_feed(api_key=user_api_key, feed_id=new_feed_id)
            if environment:
                logging.info("Success retrieving created feed details:\n%s\n" % environment)
            else:
                logging.error("Problem reading created feed")
        except Exception, ex:
            logging.error("Error retrieving feed list: %s" % str(ex))


        # update the new environment
        try:
            updated_title = "Temp Updated Title"
            environment_update = txpachube.Environment(title=updated_title, version="1.0.0")
            logging.info("Updating the new environment with content:\n%s\n" % environment_update)
            environment_was_updated = yield client.update_feed(api_key=user_api_key, 
                                                               feed_id=new_feed_id, 
                                                               data=environment_update.encode())
            if environment_was_updated:
                logging.info("Success updating the new environment: %s" % environment_was_updated)
            else:
                logging.error("Problem occurred updating the new environment")
        except Exception, ex:
            logging.error("Error updating the new environment: %s" % str(ex))


        # read back the updated feed details  
        try:
            logging.info("Requesting details of the updated feed %s" % new_feed_id)
            updated_environment = yield client.read_feed(api_key=user_api_key, feed_id=new_feed_id)
            if updated_environment:
                logging.info("Success retrieving updated feed details:\n%s\n" % updated_environment)
                logging.info("Updated environment title value matches expected result: %s" % (updated_environment.title == updated_title))
            else:
                logging.error("Problem updating title in new environment")
        except Exception, ex:
            logging.error("Error retrieving feed list: %s" % str(ex))

   
        ################################################################################
        # Datastreams
        ################################################################################ 


        new_datastream_name = 'test_datastream'
        original_current_value = "20"
        updated_current_value = "40"
        new_datastream_id = None
                
        # create a new datastream in the new feed    
        try:
            #
            # Interesting... it seems to create a new datastream that an environment
            # wrapper must be placed around the new datastream data to be created.
            #
            environment = txpachube.Environment(version="1.0.0", datastreams=[{'id':new_datastream_name, 'current_value':original_current_value}])
            logging.info("Creating a new datastream with content:\n%s\n" % environment)
            new_datastream_id = yield client.create_datastream(api_key=user_api_key, 
                                                               feed_id=new_feed_id, 
                                                               data=environment.encode())
            if new_datastream_id:
                logging.info("Success creating a new datastream. New datastream is: %s" % new_datastream_id)
            else:
                logging.error("Problem creating a new datastream")
        except Exception, ex:
            logging.error("Error creating new datastream: %s" % str(ex))


        if new_datastream_id:
            
            # read datastream
            try:
                logging.info("Requesting details of the created datastream %s" % new_datastream_id)
                datastream = yield client.read_datastream(api_key=user_api_key, 
                                                          feed_id=new_feed_id, 
                                                          datastream_id=new_datastream_id)
                if datastream:
                    logging.info("Success retrieving created datastream details:\n%s\n" % datastream)
                    logging.info("Created datastream current value matches expected result: %s (%s == %s)" % (original_current_value == datastream.current_value, original_current_value, datastream.current_value))
                else:
                    logging.error("Problem reading created datastream")                
            except Exception, ex:
                logging.error("Error reading new datastream: %s" % str(ex))
            
            
            # update datastream with a new current value
            try:
                
                datastream = txpachube.Datastream(id=new_datastream_id, current_value=updated_current_value)
                logging.info("Updating new datastream in the new feed with content:\n%s\n" % datastream)
                datastream_updated = yield client.update_datastream(api_key=user_api_key, 
                                                                    feed_id=new_feed_id,
                                                                    datastream_id=new_datastream_id,
                                                                    data=datastream.encode())
                if datastream_updated:
                    logging.info("Success updating new datastream: %s" % datastream_updated)
                else:
                    logging.error("Problem updating the datastream")                
            except Exception, ex:
                logging.error("Error updating new datastream: %s" % str(ex))            
            
            
            # read datastream
            try:
                logging.info("Requesting details of the updated datastream %s" % new_datastream_id)
                updated_datastream = yield client.read_datastream(api_key=user_api_key, 
                                                                  feed_id=new_feed_id, 
                                                                  datastream_id=new_datastream_id)
                if updated_datastream:
                    logging.info("Success retrieving updated datastream details:\n%s\n" % updated_datastream)
                    logging.info("Updated datastream current value matches expected result: %s (%s == %s)" % (updated_current_value == updated_datastream.current_value, updated_current_value, updated_datastream.current_value))
                else:
                    logging.error("Problem reading updated datastream")                 
            except Exception, ex:
                logging.error("Error reading updated datastream: %s" % str(ex))            


            ################################################################################
            # Datapoints
            ################################################################################ 
            
            
            datapoint_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
            datapoint_timestamp = "%sZ" % datapoint_time.isoformat()
            original_value = "30.0"
            updated_value = "10"

            # add a datapoint to the new datastream - make sure the timestamp is older
            # than any earlier datapoints (so this datapoint create does not get stuck
            # in the datastream's at/current_value)
            try:
                datapoints = txpachube.Datastream(id=new_datastream_id, datapoints=[{'at':datapoint_timestamp, 'value':original_value}])
                logging.info("Creating a new datapoint [%s] with content:\n%s\n" % (datapoint_timestamp, datapoints))
                new_datapoint_created = yield client.create_datapoints(api_key=user_api_key, 
                                                                       feed_id=new_feed_id, 
                                                                       datastream_id=new_datastream_id, 
                                                                       data=datapoints.encode())
                if new_datapoint_created:
                    logging.info("Success creating a new datapoint: %s" % new_datapoint_created)
                else:
                    logging.error("Problem occurred creating new datapoint")
            except Exception, ex:
                logging.error("Error creating a datapoint: %s" % str(ex))
            
            
            if new_datapoint_created:
                
                # read the created datapoint back
                try:
                    logging.info("Reading back the created datapoint")
                    datapoint = yield client.read_datapoint(api_key=user_api_key, 
                                                            feed_id=new_feed_id, 
                                                            datastream_id=new_datastream_id, 
                                                            timestamp=datapoint_timestamp)
                    if datapoint:
                        logging.info("Success reading the created datapoint:\n%s\n" % datapoint)
                        logging.info("Datapoint value matches expected result: %s, (%s == %s)" % (original_value == datapoint.value, original_value, datapoint.value))
                    else:
                        logging.error("Problem occurred reading back new datapoint")
                except Exception, ex:
                    logging.error("Problem reading the created datapoint: %s" % str(ex))

            
                # update the new datapoint
                try:
                    datapoint = txpachube.Datapoint(value=updated_value)
                    logging.info("Updating the new datapoint [%s] with content:\n%s\n" % (datapoint_timestamp, datapoint))
                    datapoint_updated = yield client.update_datapoint(api_key=user_api_key, 
                                                                      feed_id=new_feed_id, 
                                                                      datastream_id=new_datastream_id,
                                                                      timestamp=datapoint_timestamp,
                                                                      data=datapoint.encode())
                    if datapoint_updated:
                        logging.info("Success updating the new datapoint: %s" % datapoint_updated)
                    else:
                        logging.error("Problem occurred updating the new datapoint")
                except Exception, ex:
                    logging.error("Error updating a datapoint: %s" % str(ex)) 
                    logging.error("Traceback:\n%s\n" % traceback.print_exc())                         
                
                
                # read the updated datapoint
                try:
                    logging.info("Reading back the updated datapoint")
                    updated_datapoint = yield client.read_datapoint(api_key=user_api_key, 
                                                                    feed_id=new_feed_id, 
                                                                    datastream_id=new_datastream_id, 
                                                                    timestamp=datapoint_timestamp)
                    if updated_datapoint:
                        logging.info("Success reading the updated datapoint:\n%s\n" % updated_datapoint)
                        logging.info("Datapoint value matches expected result: %s, (%s == %s)" % (updated_value == updated_datapoint.value, updated_value, updated_datapoint.value))
                    else:
                        logging.error("Problem occurred reading back new datapoint")
                except Exception, ex:
                    logging.error("Problem reading the created datapoint: %s" % str(ex))
                
                  
                # delete the new datapoint
                try:
                    datapoint = txpachube.Datapoint(at=datapoint_timestamp, value=updated_value)
                    logging.info("Deleting the new datapoint")
                    datapoint_deleted = yield client.delete_datapoint(api_key=user_api_key, 
                                                                      feed_id=new_feed_id, 
                                                                      datastream_id=new_datastream_id, 
                                                                      timestamp=datapoint_timestamp)
                    if datapoint_deleted:
                        logging.info("Success deleting the specified datapoint: %s" % datapoint_deleted)
                    else:
                        logging.error("Problem occurred deleting the specified datapoint")
                except Exception, ex:
                    logging.error("Error deleting a datapoint: %s" % str(ex))
                    logging.error("Traceback:\n%s\n" % traceback.print_exc())               
                
            else:
                logging.error("Datapoint was not created - can't perform datapoint update, read or delete actions")



            ################################################################################
            # Triggers
            ################################################################################
        

            # list any triggers visible to this key    
            try:        
                logging.info("Requesting a trigger list")
                trigger_list = yield client.list_triggers(api_key=user_api_key)
                if trigger_list:
                    logging.info("Success retrieving a trigger list:\n%s\n" % trigger_list)
                else:
                    logging.error("Problem occurred listing triggers")
            except Exception, ex:
                logging.error("Error retrieving trigger list: %s" % str(ex))
        
                    
            original_value = "50"
            updated_value = "45"
            new_trigger_id = None
            
            # create a new trigger
            try:
                # feed id appears to want a int rather than a string.
                trigger = txpachube.Trigger(environment_id=new_feed_id, 
                                            stream_id=new_datastream_name,
                                            threshold_value=original_value,
                                            trigger_type="gt",
                                            url="http://www.postbin.org/1ijyltn")
                logging.info("Creating a new trigger with content:\n%s\n" % trigger)
                new_trigger_id = yield client.create_trigger(api_key=user_api_key, data=trigger.encode())
                if new_trigger_id:
                    logging.info("Success creating a new trigger. New trigger id is: %s" % new_trigger_id)
                else:
                    logging.error("Problem occurred creating new trigger")
            except Exception, ex:
                logging.error("Error creating a trigger: %s" % str(ex))
            
            if new_trigger_id:
                
                # read the created trigger
                try:
                    logging.info("Requesting details of the new trigger %s" % new_trigger_id)
                    created_trigger = yield client.read_trigger(api_key=user_api_key, trigger_id=new_trigger_id)
                    if created_trigger:
                        logging.info("Success retrieving created trigger details:\n%s\n" % created_trigger)
                        logging.info("Trigger threshold value matches expected result: %s, (%s == %s)" % (original_value == created_trigger.threshold_value, original_value, created_trigger.threshold_value))
                    else:
                        logging.error("Problem reading created trigger")                    
                except Exception, ex:
                    logging.error("Error reading the created trigger: %s" % str(ex))
                
                
                # update the trigger
                try:
                    trigger_update = txpachube.Trigger(environment_id=new_feed_id, 
                                                       stream_id=new_datastream_name,
                                                       threshold_value=updated_value)
                    logging.info("Updating trigger with content:\n%s\n" % trigger_update)
                    trigger_updated = yield client.update_trigger(api_key=user_api_key, trigger_id=new_trigger_id, data=trigger_update.encode())
                    if trigger_updated:
                        logging.info("Success updating trigger details: %s" % trigger_updated)
                    else:
                        logging.error("Problem updating trigger")                
                except Exception, ex:
                    logging.error("Error updating the trigger: %s" % str(ex))            
                
                
                # read the updated trigger
                try:
                    logging.info("Requesting details of the updated trigger %s" % new_trigger_id)
                    updated_trigger = yield client.read_trigger(api_key=user_api_key, trigger_id=new_trigger_id)
                    if created_trigger:
                        logging.info("Success retrieving updated trigger details:\n%s\n" % updated_trigger)
                        logging.info("Updated trigger threshold value matches expected result: %s, (%s == %s)" % (updated_value == updated_trigger.threshold_value, updated_value, updated_trigger.threshold_value))
                    else:
                        logging.error("Problem reading updated trigger")                    
                except Exception, ex:
                    logging.error("Error reading the updated trigger: %s" % str(ex))            
                
                
                # delete the new trigger   
                try:
                    logging.info("Deleting the new trigger %s" % new_trigger_id)
                    trigger_deleted = yield client.delete_trigger(api_key=user_api_key, trigger_id=new_trigger_id)
                    if trigger_deleted:
                        logging.info("Success deleting new trigger: %s" % trigger_deleted)
                    else:
                        logging.error("Problem occurred deleting the new trigger")
                except Exception, ex:
                    logging.error("Error deleting new trigger: %s" % str(ex)) 
    
            else:
                logging.error("Problem creating a new trigger")


            
            

            # delete the datastream
            try:
                logging.info("Deleting the new datastream")
                new_datastream_deleted = yield client.delete_datastream(api_key=user_api_key, 
                                                                        feed_id=new_feed_id, 
                                                                        datastream_id=new_datastream_id)
                if new_datastream_deleted:
                    logging.info("Success deleting the new datastream: %s" % new_datastream_deleted)
                else:
                    logging.error("Problem occurred deleting the new datastream")
            except Exception, ex:
                logging.error("Error creating feed: %s" % str(ex))
        
        else:
            logging.error("Problem creating a new datastream in the new feed")
            
                              
        # delete the new feed   
        try:
            logging.info("Deleting the new feed %s" % new_feed_id)
            feed_deleted = yield client.delete_feed(api_key=user_api_key, feed_id=new_feed_id)
            if feed_deleted:
                logging.info("Success deleting new feed details: %s" % feed_deleted)
            else:
                logging.error("Problem occurred deleting the new feed")
        except Exception, ex:
            logging.error("Error deleting new feed: %s" % str(ex))            
            
            
    else:
        logging.error("Problem creating a new feed")



        
    ################################################################################
    # Users - this functionality must be explicitly enabled by Pachube for you
    ################################################################################
    
#    firstname = 'FirstName'
#    lastname = 'LastName'
#    email='test@nowhere.com'
#    
#    # create user
#    try:
#        candidate_user = txpachube.User(first_name=firstname, last_name=lastname, email=email, login='test')
#        logging.info("Requesting to create a new user %s" % candidate_user)
#        new_user_id = yield client.create_user(api_key=user_api_key, data=None)
#        if new_user_id:
#            logging.info("Success crating new user. New user id is: %s" % new_user_id)
#        else:
#            logging.error("Problem occurred crating the new user")
#        except Exception, ex:
#            logging.error("Error creating new user: %s" % str(ex))
#                
#    if new_user_id:
#        
#        # read user
#        try:
#            logging.info("Requesting to read the new user")
#            new_user = yield client.read_user(api_key=user_api_key, user_id=new_user_id)
#            if new_user:
#                logging.info("Success retrieving created user details:\n%s\n" % new_user)
#            else:
#                logging.error("Problem reading created user")
#        except Exception, ex:
#            logging.error("Error reading created user: %s" % str(ex))
#                    
#        # update user
#        try:
#            updated_firstname = 'Beef'
#            updated_lastname = 'Jerky'
#            user_update = txpachube.User(first_name=firstname, last_name=lastname)
#            logging.info("Requesting to update the new user with content:\n%s\n" % user_update)
#            user_updated = yield client.update_user(api_key=user_api_key, user_id=new_user_id, data=user_update.encode())
#            if user_updated:
#                logging.info("Success updating new user details: %s" % user_updated)
#            else:
#                logging.error("Error updating new user: %s" % str(ex))
#        except Exception, ex:
#            logging.error("Error updating new user: %s" % str(ex))
#                    
#        # read user
#        try:
#            logging.info("Requesting to read the updated user")
#            updated_user = yield client.read_user(api_key=user_api_key, user_id=new_user_id)
#            if updated_user:
#                logging.info("Success retrieving updated user details:\n%s\n" % updated_user)
#            else:
#                logging.error("Problem reading updated user")
#        except Exception, ex:
#            logging.error("Error reading updated user: %s" % str(ex))
#                    
#        # delete user
#        try:
#            logging.info("Requesting to delete the new user")
#            user_deleted = yield client.delete_user(api_key=user_api_key, user_id=new_user_id)
#            if user_deleted:
#                logging.info("Success deleting new user: %s" % user_deleted)
#            else:
#                logging.error("Error deleting new user: %s" % str(ex))
#        except Exception, ex:
#            logging.error("Error deleting new user: %s" % str(ex))
#                
#    else:
#        logging.error("Problem creating a new user")
        
        
    logging.info("Demo finished, stopping")
    reactor.callLater(0.1, reactor.stop)
    defer.returnValue(True)          
        
        

        
        
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s : %(message)s")

    (options, args) = parser.parse_args()
    
    # confirm keyfile is suppplied and valid
    if options.keyfile is None:
        print parser.get_usage()
        print "No key file supplied"
        sys.exit(1)
    
    
    keyfile = os.path.expanduser(options.keyfile)
    if not os.path.exists(keyfile):
        print "Invalid API key file path: %s" % keyfile
        sys.exit(1)
    
    fd = open(keyfile, 'r')
    user_api_key = fd.read().strip()
    fd.close()

    
    reactor.callWhenRunning(demo, user_api_key)
    reactor.run()





