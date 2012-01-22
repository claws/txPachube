#!/usr/bin/env python



import json
import logging
import txpachube
import urllib
import uuid
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.web.client import Agent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements




# NOTE:
# In twisted 11.1.0 this class can be replaced by twisted.web.client.FileBodyProducer
#
class RequestBodyProducer(object):
    """
    This object is used to feed the request body data
    during a request to a remote server. It also allows
    the Agent request method to populate the content
    length header field.
    """
    implements(IBodyProducer)
  
    def __init__(self, body=None):
        if body is None:
            self.body = ""
        else:
            self.body = body
        self.length = len(body)
  
    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)
  
    def pauseProducing(self):
        pass
  
    def stopProducing(self):
        pass



class ResponseBodyProtocol(Protocol):
    """
    This object is used to receive the response body data
    after a request to a remote server.
    """
    def __init__(self, finished, response):
        self.finished = finished
        self.response = response
        self.buffer = []

    def dataReceived(self, bytes):
        """
        Receive and store some bytes of the response data
        """
        self.buffer.append(bytes)

    def connectionLost(self, reason):
        """ 
        Return the response and the response body via the finished deferred.
        """
        r = reason.trap(ResponseDone)
        if r == ResponseDone:
            logging.debug('Finished receiving body: %s' % reason.getErrorMessage())
            responseData = "".join(self.buffer)
            self.buffer = []
            result = (self.response, responseData)
            self.finished.callback(result)
            
            
            

class Client(object):
    """ 
    Encapsulates the Pachube API on top of the nonblocking,
    event driven twisted framework. 
    """
    
    api_url = "api.pachube.com/v2"
    
    
    def __init__(self, api_key=None, feed_id=None, use_http=False, timezone=None):
        """
        @param api_key: The default api key, with appropriate authorization privileges,
                        to use.
        @type api_key: string
        @param feed_id: The default feed identifier to use
        @type feed_id: string
        @param use_http: A flag instructing this object to use http instead of
                         the default https.
        @type use_http: boolean
        @param timezone: By default all get requests return results in UTC.
                         Defining a timezone results in the returned data
                         having local timestamps. For more information on
                         the available settings see:
                         http://api.pachube.com/#time-zones
        @type timezone: string (eg. +3.5 or Adelaide
        
        """
        self.feed_id = feed_id
        self.api_key = api_key

        prefix = "https"
        if use_http:
            prefix = "http"

        self.api_url = "%s://api.pachube.com/v2" % (prefix)
        
        self.timezone = None
        if timezone:
            self.timezone = "timezone=%s" % timezone
        
        # The agent web client is responsible for handling all 
        # requests to and responses from the pachube site.
        self.agent = Agent(reactor)
        
        # Common header settings used in every request.
        self.headers = {'User-Agent': 'txpachube Client',
                        'Content-Type' : 'application/x-www-form-urlencoded'}    
        
            
    #
    # Callbacks
    #


    def _handleResponseHeader(self, response, url):
        """
        Called upon successful receipt of the response headers. The response's
        body is then retrieved. Upon completion of the body retrieval the
        returned deferred is fired returning a tuple containing the response
        and the response body. 
        
        @param response: The response object
        @type response: twisted.web.client.Response
        @param url: The url used during the request
        @type url: string
        
        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred      
        """
        logging.debug("Success communicating with url: %s" % (url))
        finished = defer.Deferred()
        response.deliverBody(ResponseBodyProtocol(finished, response))
        return finished


    def _handleRequestFailure(self, failure, url=None):
        """
        Callback to handle an error resulting from an attempt to communicate with pachube.
        
        @param failure: A failure instance
        @type failure: twisted.python.failure.Failure instance
        @param url: The url used during the request
        @type url: string
        """
        if url:
            logging.error('Error communicating with url %s\nError: %s\n' % (url, failure))
        else:
            logging.error('Error detected: %s' % (failure))


    def _getResponseBody(self, result):
        """
        Most responses need to deliver the response body data. Some need
        to return data from the header only. This method provides the 
        ability to return only the response body data.
        """
        response, body = result
        return body
    
    
    def _convertToPachubeStructure(self, data, format, kind):
        """
        Convert the data into a DataStructure object
        """
        dataStructureClass = txpachube.getDataStructure(kind)
        dataStructure = dataStructureClass()
        dataStructure.decode(data, format)
        return dataStructure



    def _getResponseCodeStatusFromHeader(self, result):
        """
        Most responses need to deliver the response body data. Some need
        to return data from the header only. This method provides the 
        ability to return a success/fail criteria based on the response
        header code received.
        """
        response, body = result
        success = response.code == 200
        if not success:
            error_str = "%s : %s" % (response.code, response.phrase)
            logging.error("Unexpected response code: \'%s\', phrase: %s" % (error_str))
        return success
    
    
    def _getLocationFromHeader(self, result):
        """
        Extract and return the location of the created item 
        from the 'Location' field in the response header.
        """
        response, body = result
        if response.code == 201:
            # created ok
            if response.headers.hasHeader("Location"):
                locations = response.headers.getRawHeaders("Location")
                if locations:
                    if len(locations) > 1:
                        logging.warning("Unexpected number of location items in response header: %s" % locations)
                        # for now just return the first occurrence
                    location = locations[0]
                    return location
                else:
                    err_str = "No content in response header \'Location\' field"
                    logging.error(err_str)
                    raise Exception(err_str)
            else:
                err_str = "No response header \'Location\' field found"
                logging.error(err_str)
                raise Exception(err_str)
        else:
            err_str = "Unexpected response => %s:%s" % (response.code, response.phrase)
            logging.error(err_str)
            raise Exception(err_str) 

    #
    # 
    #
    
    
    def _sendRequest(self, method, url, headers, bodyProducer):
        """
        Send a request to the url, where the method argument defines the kind of request.
        Returns a deferred that returns a tuple containing the response header and the
        response body.
        
        @param method: The kind of request to make. [GET|PUT|POST|DELETE]
        @type method: string
        @param url: The url used during the request
        @type url: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict
        @param bodyProducer: An object implementing IBodyProducer that is capable
                             of being used to send the request body data.
        
        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred        
        """
        headers.update(self.headers)
        logging.debug("method=%s, url=%s, headers=%s, bodyLength=%s" % (method,
                                                                        url,
                                                                        str(headers),
                                                                        bodyProducer.length if bodyProducer else 0))
        d = self.agent.request(method=method,
                               uri=url,
                               headers=Headers(dict([(k, [v]) for k,v in headers.items()])),
                               bodyProducer=bodyProducer)
        d.addCallback(self._handleResponseHeader, url)
        d.addErrback(self._handleRequestFailure, url)
        return d        


    def _get(self, url, headers):
        """ 
        Perform a get at the specified url 
        
        @param url: The url used during the request
        @type url: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("GET", url, headers, None)
        
        
    def _put(self, url, headers, data):
        """ 
        Perform a put at the specified url 
        
        @param url: The url used during the request
        @type url: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict
        @param data: The data that forms the body of the request.
        @type data: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("PUT", url, headers, RequestBodyProducer(data))
    
    
    def _post(self, url, headers, data):
        """ 
        Perform a post at the specified url 
        
        @param url: The url used during the request
        @type url: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict
        @param data: The data that forms the body of the request.
        @type data: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("POST", url, headers, RequestBodyProducer(data))       
    
    
    def _delete(self, url, headers):
        """ 
        Perform a delete at the specified url
        
        @param url: The url used during the request
        @type url: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("DELETE", url, headers, None)        
        
    
    #
    # Environments (Feeds)
    #
    
    
    def list_feeds(self, api_key=None, format=txpachube.DataFormats.JSON, parameters=None):
        """ 
        Returns a paged list of Pachube's feeds that are viewable by 
        the authenticated account with a default page size of 50 feeds.
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param parameters: Additional parameters to configure the search query.
        @type parameters: dict
        
        @return: A deferred that returns the response body which is a paged
                 list of feeds (default 50 per page) viewable by the api_key 
                 provided.
        @rtype: string (in the format specified by the format argument)
        
        
        Available settings for parameters:
        
        page
            Integer indicating which page of results you are requesting. Starts from 1.
            http://api.pachube.com/v2/feeds?page=2
        
        per_page
            Integer defining how many results to return per page (1 to 1000).
            http://api.pachube.com/v2/feeds?per_page=5
        
        content
            String parameter ('full' or 'summary') describing whether we 
            want full or summary results. Full results means all datastream
            values are returned, summary just returns the environment meta 
            data for each feed.
            http://api.pachube.com/v2/feeds?content=summary
        
        q
            Full text search parameter. Should return any feeds matching this string.
            http://api.pachube.com/v2/feeds?q=arduino
        
        tag
            Returns feeds containing datastreams tagged with the search query.
            http://api.pachube.com/v2/feeds?tag=temperature
        
        user
            Returns feeds created by the user specified.
            http://api.pachube.com/v2/feeds.xml?user=pachube
        
        units
            Returns feeds containing datastreams with units specified by the 
            search query.
            http://api.pachube.com/v2/feeds.xml?units=celsius
        
        status
            Possible values ('live', 'frozen', or 'all'). Whether to search 
            for only live feeds, only frozen feeds, or all feeds. Defaults to all.
            http://api.pachube.com/v2/feeds.xml?status=frozen
        
        order
            Order of returned feeds. Possible values ('created_at', 'retrieved_at',
            or 'relevance').
            http://api.pachube.com/v2/feeds.xml?order=created_at
        
        show_user
            Include user login and user level for each feed. 
            Possible values: true, false (default).
            http://api.pachube.com/v2/feeds.xml?show_user=true
        
        
        The following additional advanced parameters are more intensive 
        queries that are restricted to particular account types:
        
        lat    
            Used to find feeds located around this latitude. 
            Used if ids/_datastreams_ are not specified.
            lat=51.5235375648154
        
        lon
            Used to find feeds located around this longitude. 
            Used if ids/_datastreams_ are not specified.
            lon=-0.0807666778564453
        
        distance
            search radius
            distance=5.0
        
        distance_units
            miles or kms (default).
            distance_units=miles        

        If api_key argument is not set when calling this method then the
        value set during this object's instantiation (ie. in __init__) is used.        
        """
        
        url = "%s/feeds.%s" % (self.api_url, format)
        
        if parameters:
            params = urllib.urlencode(parameters)
            url = "%s?%s" % (url, params)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.List_Feeds_Msg)
        return d
        
        
    def create_feed(self, api_key=None, format=txpachube.DataFormats.JSON, data=None):
        """ 
        Creates a new feed.
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param data: A string detailing the environment to be created.
        @type data: string
        
        @return: A deferred that returns the feed_id of the newly created feed. 
        @rtype: string

        If api_key argument is not set when calling this method then the
        value set during this object's instantiation (ie. in __init__) is used.
        """
        
        def getFeedIdFromLocation(location):
            """
            Extract and return the new feed id from the 'Location' field in the response header.
            """
            feed_id = location.split("/")[-1]
            return feed_id
                    
        
        if format == txpachube.DataFormats.CSV:
            raise Exception("CSV format is not supported for creating feeds")
        
        url = "%s/feeds.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._post(url, headers, data)
        d.addCallback(self._getLocationFromHeader)
        d.addCallback(getFeedIdFromLocation)
        return d
    
    
    def read_feed(self, api_key=None, feed_id=None, format=txpachube.DataFormats.JSON, parameters=None):
        """ 
        Returns the most recent datastreams for environment [feed_id], viewable by the api_key provided
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param parameters: Additional parameters to configure the search query.
        @type parameters: dict
        
        @return: A deferred that returns a txpachube.Environment object populated
                 from the body of the response.
        @rtype: txpachube.Environment
        
        
        Available settings for parameters:
        datastream
            Filter the returned datastreams. Comma separated datastream IDs.
            http://api.pachube.com/v2/feeds/123.json?datastreams=energy,power

        show_user
            Include user login and user level for each feed. 
            Possible values: true, false (default).
            http://api.pachube.com/v2/feeds/123.xml?show_user=true (json/xml only)        


        Available settings for parameters supporting historical queries:  
        start: 
            Defines the starting point of the query as a timestamp, 
            e.g. 2010-05-20T11:01:46Z. The default value is blank.

        end: 
        Defines the end point of the data returned as a timestamp, 
        e.g. 2010-05-21T11:01:46Z. The default value is set to the current timestamp.

        duration:
            Specifies the duration of the query.
            If used in conjunction with end it will request the data prior to the end date.
            If used in conjunction with start it will request the data after the start date.
            If used by itself it will give the most recent data for the duration specified.
            It is incorrect to specify start, end and duration

            The format is <number><time unit> e.g. 10minutes, 6hours

            The valid time units are:
            seconds
            minute(s)
            hour(s)
            day(s)
            week(s)
            month(s)
            year(s)

        page: 
            Defines which page we are looking at of the matching results. 
            If not set, the default value is 1

        per_page: 
            Defines how many results are returned per page. 
            If not set this value defaults to 100. Maximum value is 1000

        time: 
            Returns the feed with the values as they were at the specified timestamp. 
            There are a few points to note about this functionality:
                Only the values of the datastream and their timestamps are changed, 
                all other metadata reflects the current state of the feed and its datastreams
                If a datastream had no values at the time specified (either because it didn't
                exist or because it hadn't been updated) it will be excluded from the output
        
        find_previous:
            Will also return the previous value to the date range being requested. 
            Note that this is useful for any graphing because if you want to draw a graph of 
            the date range you specified you would end up with a small gap until the first value.

        interval_type:
            If set to "discrete" the data will be returned in fixed time interval format 
            according to the inverval value supplied. If this is not set, the raw datapoints
            will be returned.

        interval: 
            Determines what interval of data is requested and is defined in seconds between
            the datapoints. If a value is passed in which does not match one of these values, 
            it is rounded up to the next value. 
            The acceptable values are currently:
                Value    Description                     Maximum range in one query
                0        Every snapshot stored            6 hours
                30       30 second interval data          12 hours
                60       One snapshot every minute        24 hours
                300      One snapshot every 5 minutes     5 days
                900      One snapshot every 15 minutes    14 days
                3600     One snapshot per hour            31 days
                10800    One snapshot per three hours     90 days
                21600    One snapshot per six hours       180 days
                43200    One snapshot per twelve hours    1 year
                86400    One snapshot per day             1 year
                
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """

        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s.%s" % (self.api_url, feed_id, format)
        
        if parameters:
            params = urllib.urlencode(parameters)
            url = "%s?%s" % (url, params)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_Feed_Msg)
        return d        
        
        
    def update_feed(self, api_key=None, feed_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Updates [environment ID]'s environment and datastreams. If successful, the 
        current datastream values are stored and any changes in environment metadata
        overwrite previous values. Pachube stores a server-side timestamp in the 
        "updated" attribute and sets the feed to "live" if it wasn't before. 

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param data: A representation of the feed in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the update based on
                 the response header data. 
        @rtype: boolean

        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.                
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s.%s" % (self.api_url, feed_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._put(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d


    def delete_feed(self, api_key=None, feed_id=None):
        """
        The DELETE request does not require a format to be used. A request made to 
        this URL will delete the object referred to by the ID. 
        WARNING: This is final and cannot be undone.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        
        @return: A deferred that returns the success of the delete based on
                 the response header data. 
        @rtype: boolean

        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.      
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s" % (self.api_url, feed_id)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key,
                   'Content-Type' : self._getContentType(format)}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d


    #
    # Datastreams
    #
    
    def create_datastream(self, api_key=None, feed_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Creates new datastream(s) in environment [feed ID]. The body of the request 
        should contain a JSON, XML or CSV representation of the datastream to be created.
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param data: A representation of the datastream in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """       
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams.%s" % (self.api_url, feed_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._post(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
           
        
    def read_datastream(self, api_key=None, feed_id=None, datastream_id=None, format=txpachube.DataFormats.JSON, parameters=None): 
        """
        Read the requested datastream.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param parameters: Additional parameters to configure the png output.
        @type parameters: dict

        @return: A deferred that returns the response body which is the feed
                 (environment) with on the requested datastream
        @rtype: string (in the format specified by the format argument)
            
            
        Available settings for parameters supporting historical queries:  
        start: 
            Defines the starting point of the query as a timestamp, 
            e.g. 2010-05-20T11:01:46Z. The default value is blank.

        end: 
        Defines the end point of the data returned as a timestamp, 
        e.g. 2010-05-21T11:01:46Z. The default value is set to the current timestamp.

        duration:
            Specifies the duration of the query.
            If used in conjunction with end it will request the data prior to the end date.
            If used in conjunction with start it will request the data after the start date.
            If used by itself it will give the most recent data for the duration specified.
            It is incorrect to specify start, end and duration

            The format is <number><time unit> e.g. 10minutes, 6hours

            The valid time units are:
            seconds
            minute(s)
            hour(s)
            day(s)
            week(s)
            month(s)
            year(s)

        page: 
            Defines which page we are looking at of the matching results. 
            If not set, the default value is 1

        per_page: 
            Defines how many results are returned per page. 
            If not set this value defaults to 100. Maximum value is 1000

        time: 
            Returns the feed with the values as they were at the specified timestamp. 
            There are a few points to note about this functionality:
                Only the values of the datastream and their timestamps are changed, 
                all other metadata reflects the current state of the feed and its datastreams
                If a datastream had no values at the time specified (either because it didn't
                exist or because it hadn't been updated) it will be excluded from the output
        
        find_previous:
            Will also return the previous value to the date range being requested. 
            Note that this is useful for any graphing because if you want to draw a graph of 
            the date range you specified you would end up with a small gap until the first value.

        interval_type:
            If set to "discrete" the data will be returned in fixed time interval format 
            according to the inverval value supplied. If this is not set, the raw datapoints
            will be returned.

        interval: 
            Determines what interval of data is requested and is defined in seconds between
            the datapoints. If a value is passed in which does not match one of these values, 
            it is rounded up to the next value. 
            The acceptable values are currently:
                Value    Description                     Maximum range in one query
                0        Every snapshot stored            6 hours
                30       30 second interval data          12 hours
                60       One snapshot every minute        24 hours
                300      One snapshot every 5 minutes     5 days
                900      One snapshot every 15 minutes    14 days
                3600     One snapshot per hour            31 days
                10800    One snapshot per three hours     90 days
                21600    One snapshot per six hours       180 days
                43200    One snapshot per twelve hours    1 year
                86400    One snapshot per day             1 year


        This request can also make use of the PNG format.
        
        Requesting the datastram as a PNG image will generate a graph. The time 
        period that is shown is controlled by the history parameters passed to 
        the request and the look and feel of this graph can be controlled by the
        following parameters:
        
        Parameter    Description    Example
        w    width in pixels         600
        h    height in pixels        400
        c    colour in hex           FFCC33
        t    title                   My Favourite Graph
        l    legend                  Legend For My Graph
        s    strokesize in pixels    4
        b    show axis labels        true / false
        g    show detailed grid      true / false
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s.%s" % (self.api_url, feed_id, datastream_id, format)
        
        if parameters:
            params = urllib.urlencode(parameters)
            url = "%s?%s" % (url, params)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_Datastream_Msg)
        return d
         
        
    def update_datastream(self, api_key=None, feed_id=None, datastream_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Update a single datastream

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param data: A representation of the datastream in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.        
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s.%s" % (self.api_url, feed_id, datastream_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._put(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d        
        
        
    def delete_datastream(self, api_key=None, feed_id=None, datastream_id=None): 
        """
        The DELETE request does not require a format to be used. A request made to 
        this URL will delete the object referred to by the ID. 
        WARNING: This is final and cannot be undone.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        
        @return: A deferred that returns the success of the delete based on
                 the response header data. 
        @rtype: boolean

        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.       
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s" % (self.api_url, feed_id, datastream_id)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    #    
    # Datapoints
    #
    
    
    def create_datapoints(self, api_key=None, feed_id=None, datastream_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Creates new datapoints for datastream. The body of the request 
        should contain a JSON, XML or CSV representation of the datastream to be created.

        This enables you to insert datapoints into the history of the datastream. 
        Datapoints should have a unique timestamp, which can to be specified down to
        the sub-second level. Sending new datapoints with the same timestamp as 
        existing ones will overwrite the old data with the new. If a single update 
        contains multiple values with the same timestamp (along with other records), 
        then the result will be datapoints recorded for all unique timestamps, but for
        any duplicated ones, we will only record the last record processed.

        Currently you can only send a maximum of 500 datapoints in a single update. 
        Attempting to send more than that will result in an error, and in that case none
        of your datapoints will be stored.
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param format: The format to request the results in [json|xml|csv]
        @type format: string
        @param data: A representation of the datastream in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """       
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s/datapoints.%s" % (self.api_url, feed_id, datastream_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._post(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    def read_datapoint(self, api_key=None, feed_id=None, datastream_id=None, format=txpachube.DataFormats.JSON, timestamp=None): 
        """
        Read a specific datapoint from the specified timestamp.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param timestamp: An ISO8601 formatted datapoint timestamp
        @type timestamp: string

        @return: A deferred that returns the response body which is the datapoint
                 details at the specified timestamp
        @rtype: string (in the format specified by the format argument)
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s/datapoints/%s.%s" % (self.api_url, feed_id, datastream_id, timestamp, format)

        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_Datapoint_Msg)
        return d
    
    
    def update_datapoint(self, api_key=None, feed_id=None, datastream_id=None, format=txpachube.DataFormats.JSON, timestamp=None, data=None):
        """
        Modify the value of a datapoint at the specified timestamp

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param timestamp: An ISO8601 formatted datapoint timestamp
        @type timestamp: string
        @param data: A representation of the updated datapoint in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.        
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s/datapoints/%s.%s" % (self.api_url, feed_id, datastream_id, timestamp, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._put(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d        
    

    def delete_datapoint(self, api_key=None, feed_id=None, datastream_id=None, timestamp=None):
        """
        Delete a single datapoint at the specified timestamp.
        This request does not require a format to be used.
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param timestamp: An ISO8601 formatted datapoint timestamp
        @type parameters: string

        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.        
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s/datapoints/%s" % (self.api_url, feed_id, datastream_id, timestamp)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
        
    def delete_datapoints(self, api_key=None, feed_id=None, datastream_id=None, parameters=None): 
        """
        Remove a range of datapoints for this datastream.
        This request does not require a format to be used
        
        By providing a start and end timestamp as query parameters, you may remove a all 
        datapoints that lie between those dates. 
        If you send your request with only a start timestamp, all datapoints after the 
        value will be removed. 
        Likewise, providing an end timestamp will remove all datapoints prior to the 
        supplied value. 
        Additionally this endpoint supports a duration parameter (e.g. "duration=3hours") 
        that will delete all datapoints from a start timestamp to the start timestamps + 
        duration if a start parameter is provided, or from an end timestamp to the end 
        timestamp - duration if an end parameter is provided.
        
        Available settings for parameters:
        start
            Define the start time (in ISO8601 format) from which to begin deleting
            datapoints.
            http://api.pachube.com/v2/feeds/1977/datastreams?start=2010-05-20T11:01:46.000000Z
            
        end
            Define the end time (in ISO8601 format) at which to stop deleting
            datapoints.
            http://api.pachube.com/v2/feeds/1977/datastreams?end=2011-05-20T11:01:46.000000Z
            http://api.pachube.com/v2/feeds/1977/datastreams?start=2010-05-20T11:01:46.000000Zend=2011-05-20T11:01:46.000000Z
            
        duration
            Define a duration across which to delete datapoints. 
            When used with a start time then datapoints from the start timestamp to the 
            start timestamps + duration will be deleted.
            When used with an end time then datapoints from the end timestamp to the 
            end timestamp - duration will be deleted.
            http://api.pachube.com/v2/feeds/1977/datastreams?start=2010-05-20T11:01:46.000000Z&duration=3days
            
                        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param feed_id: The feed identifier
        @type feed_id: string
        @param datastream_id: A datastream identifier
        @type datastream_id: string
        @param parameters: Additional parameters to configure the png output.
        @type parameters: dict
        
        @return: A deferred that returns the success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """
        if feed_id is None:
            feed_id = self.feed_id
                    
        url = "%s/feeds/%s/datastreams/%s/datapoints" % (self.api_url, feed_id, datastream_id)

        if parameters:
            params = urllib.urlencode(parameters)
            url = "%s?%s" % (url, params)
                    
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
           
    #
    # Triggers
    #
    
    
    def list_triggers(self, api_key=None, format=txpachube.DataFormats.JSON):
        """ 
        Retrieve a list of all triggers for the authenticated account

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        
        @return: A deferred that returns a list of triggers success of the create based on
                 the response header data. 
        @rtype: boolean
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """     
        url = "%s/triggers.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.List_Triggers_Msg)
        return d        
            
        
    def create_trigger(self, api_key=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Create a trigger

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param data: Trigger definition in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the trigger_id of the newly created trigger. 
        @rtype: string
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.        
        
        """
        def getTriggerIdFromLocation(location):
            """
            Extract and return the new trigger id from the 'Location' field in the response header.
            """
            trigger_id = location.split("/")[-1]
            return trigger_id
                    
        url = "%s/triggers.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
               
        d = self._post(url, headers, data)
        d.addCallback(self._getLocationFromHeader)
        d.addCallback(getTriggerIdFromLocation)
        return d        
        
        
    def read_trigger(self, api_key=None, trigger_id=None, format=txpachube.DataFormats.JSON):
        """ 
        Returns a representation of a trigger 
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param trigger_id: The trigger identifier
        @type trigger_id: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        @param parameters: Additional parameters to configure the search query.
        @type parameters: dict
        
        @return: A deferred that returns the response body which contains
                 the representation of a trigger in the format specified 
                 by the format argument.
        @rtype: string
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """      
        url = "%s/triggers/%s.%s" % (self.api_url, trigger_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_Trigger_Msg)
        return d        
        
        
    def update_trigger(self, api_key=None, trigger_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Updates an existing trigger object. 

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param trigger_id: The trigger identifier
        @type trigger_id: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        @param data: A representation of the trigger in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the update based on
                 the response header data. 
        @rtype: boolean

        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.                
        """
        url = "%s/triggers/%s.%s" % (self.api_url, trigger_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._put(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    def delete_trigger(self, api_key=None, trigger_id=None):
        """
        Delete a trigger.
        WARNING: This is final and cannot be undone.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param trigger_id: The trigger identifier
        @type trigger_id: string
        
        @return: A deferred that returns the success of the delete based on
                 the response header data. 
        @rtype: boolean

        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.      
        """

                    
        url = "%s/triggers/%s.%s" % (self.api_url, trigger_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d    
    
    
    #
    # Users
    #
    
    
    def list_users(self, api_key=None, format=txpachube.DataFormats.JSON):
        """ 
        Retrieve a list of all users for the authenticated account

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        
        @return: A deferred that returns a list of users in the format specified 
                 by the format argument. 
        @rtype: boolean
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """     
        url = "%s/users.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.List_Users_Msg)
        return d 
    
    
    def create_user(self, api_key=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Create a user

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param data: User definition in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the create user based on
                 the response header data. 
        @rtype: boolean
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.        
        
        """
        def getTriggerIdFromLocation(location):
            """
            Extract and return the new trigger id from the 'Location' field in the response header.
            """
            trigger_id = location.split("/")[-1]
            return trigger_id
                    
        url = "%s/users.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
               
        d = self._post(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    def read_user(self, api_key=None, user_id=None, format=txpachube.DataFormats.JSON):
        """ 
        Returns the details of a specific user 
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param user_id: The user identifier
        @type user_id: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        
        @return: A deferred that returns the response body which contains
                 the details of a user in the format specified 
                 by the format argument.
        @rtype: string
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """      
        url = "%s/users/%s.%s" % (self.api_url, user_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_User_Msg)
        return d 
    
    
    def update_user(self, api_key=None, user_id=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Updates details of an existing user object. 

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param user_id: The user identifier
        @type user_id: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        @param data: Details of the user in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the success of the update based on
                 the response header data. 
        @rtype: boolean

        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.                
        """
        url = "%s/users/%s.%s" % (self.api_url, user_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._put(url, headers, data)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    def delete_user(self, api_key=None, user_id=None):
        """
        Delete a user.
        WARNING: This is final and cannot be undone.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param user_id: The user identifier
        @type user_id: string
        
        @return: A deferred that returns the success of the delete based on
                 the response header data. 
        @rtype: boolean

        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.      
        """
        url = "%s/users/%s.%s" % (self.api_url, user_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    
    #    
    # API Keys
    #
    
    
    def list_api_keys(self, api_key=None, format=txpachube.DataFormats.JSON):
        """ 
        Retrieve a list of all keys for the authenticated account.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        
        @return: A deferred that returns a keys the response header data. 
        @rtype: boolean
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """     
        url = "%s/keys.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        if format == txpachube.DataFormats.JSON:
            d.addCallback(self._convertJsonToDict)
        return d
    
    
    def create_api_key(self, api_key=None, format=txpachube.DataFormats.JSON, data=None):
        """
        Create a new API key

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param format: The format to request the results in [json|xml|csv|png]
        @type format: string
        @param data: key definition in the appropriate format.
        @type data: string
        
        @return: A deferred that returns the API Key of the created key. 
        @rtype: string
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.        
        
        """
        def getApiKey(d):
            """
            Extract and return the new api_key from the response body.
            """
            return d[Pachube.Key][Pachube.Api_Key]
                    
        url = "%s/keys.%s" % (self.api_url, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
               
        d = self._post(url, headers, data)
        d.addCallback(self._getResponseBody)
        if format == txpachube.DataFormats.JSON:
            d.addCallback(self._convertJsonToDict)
        return d
    
    
    def read_api_key(self, api_key=None, key_id=None, format=txpachube.DataFormats.JSON):
        """ 
        Returns the details of a specific API Key 
        
        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param key_id: The API key identifier
        @type key_id: string
        @param format: The format to request the results in [json|xml]
        @type format: string
        
        @return: A deferred that returns the response body which contains
                 the details of a API key in the format specified 
                 by the format argument.
        @rtype: string
        
        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.
        """      
        url = "%s/keys/%s.%s" % (self.api_url, key_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}
        
        d = self._get(url, headers)
        d.addCallback(self._getResponseBody)
        if format == txpachube.DataFormats.JSON:
            d.addCallback(self._convertJsonToDict)
        return d 
    
    
    def delete_api_key(self, api_key=None, key_id=None):
        """
        Delete a API key.
        WARNING: This is final and cannot be undone.

        @param api_key: An api key with authorization settings allowing this action to be performed
        @type api_key: string
        @param key_id: The API key identifier
        @type key_id: string
        
        @return: A deferred that returns the success of the delete key action.
        @rtype: boolean

        If api_key argument is not set when calling this method then the default value
        set during this object's instantiation (ie. in __init__) is used.      
        """
        url = "%s/keys/%s.%s" % (self.api_url, key_id, format)
        
        if api_key is None:
            api_key = self.api_key
            
        headers = {'X-PachubeApiKey': api_key}

        d = self._delete(url, headers)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d




################################################################################
################################################################################
#
#       Pachube Advanced Web-scale Socket server (PAWS) Client
#
#
################################################################################
################################################################################


class PAWSProtocol(Protocol):
    """
    A instance of this protocol communications with the Pachube PAWS service
    """
    
    delimiter = '\n'
    
    def __init__(self):
        self.buffer = ""
    
    def connectionMade(self):
        # register this protocol with the factory so it can be
        # disconnected later if necessary.
        peer = self.transport.getPeer()
        addr = "%s:%s" % (peer.host, peer.port)
        self.factory.registerConnection(self)


    def disconnect(self):
        self.transport.loseConnection()
        
        
    def dataReceived(self, data):
        """
        Store data received from PAWS service in a buffer until a
        message delimiter is encountered then pass any messages
        back to the client through the factory's messageHandler.
        """
        self.buffer += data
        if PAWSProtocol.delimiter in self.buffer:
            msgs = self.buffer.split(PAWSProtocol.delimiter)
            for msg in msgs[:-1]:
                self.factory.messageHandler(msg)
            self.buffer = msgs[-1]
        else:
            logging.debug("No message delimiter found yet.")
            
    def send(self, data):
        """
        Send data to the PAWS service
        """
        self.transport.write(data)

            
            
class PAWSProtocolFactory(ReconnectingClientFactory):
    """
    This factory is responsible for managing the connection to the PAWS
    service. Only one protocol instance is required per client. This 
    factory will also attempt to automatically reconnect if an exisitng
    connection is lost.
    """
    
    port = 8081
    host = 'beta.pachube.com'
    
    def __init__(self, messageHandler):
        self.connection = None
        self.connected = False
        self.messageHandler = messageHandler
        
        # These attributes are used during the connect/disconnect sequence
        # to inform caller that the sequence has completed and to provide
        # the state of the connect/disconnect request.
        self._connectDeferred = None
        self._disconnectDeferred = None
        

    def _connectionStateHandler(self, state):
        """
        Store internal connected-ness state and fire any pending deferred's
        waiting on notification of requested connect/disconnect actions.
        """
        self.connected = state
        
        # call any pending connection state notifiers
        if self._connectDeferred:
            self._connectDeferred.callback(state)
            self._connectDeferred = None
            
        if self._disconnectDeferred:
            # Invert the connection state to obtain the success state
            # of a disconnection request.
            disconnectedState = not state
            self._disconnectDeferred.callback(disconnectedState)
            self._disconnectDeferred = None

        
    def connect(self):
        """
        Establish a connection to the Pachube PAWS service if there
        is no current connection established.
        
        @return: A deferred which fires with a boolean representing the
                 success of the connection request.
        @rtype: defer.Deferred
        """
        if self.connection is None:
            reactor.connectTCP(PAWSProtocolFactory.host, 
                               PAWSProtocolFactory.port, 
                               self)
            self._connectDeferred = defer.Deferred()
            return self._connectDeferred
        else:
            logging.warning("Already connected, ignoring connect request")
            return defer.succeed(True)
    

    def disconnect(self):
        """
        Break the connection to the Pachube PAWS service.
        
        @return: A deferred which fires with a boolean representing the
                 success of the disconnection request.
        @rtype: defer.Deferred
        """
        if self.connection:
            self.connection.disconnect()
            self.continueTrying = False # disable automatic reconnection attempts
            self._disconnectDeferred = defer.Deferred()
            return self._disconnectDeferred
        else:
            logging.warning("Already disconnected, ignoring disconnect request")
            return defer.succeed(True)

                       
#    def startedConnecting(self, connector):
#        logging.debug('Started to connect to PAWS service.')

    def registerConnection(self, proto):
        """
        Called from the protocol to inform the factory that a connection
        has been made tothe PAWS service.
        
        @param proto: The protocol connected to the PAWS service
        @type proto: a PAWSProtocol instance
        """
        self.connection = proto
        self._connectionStateHandler(True)
        
        
    def buildProtocol(self, addr):
        """
        Builds an instance of the PAWSProtocol. Called from witihin the 
        reactor.connectTCP method.
        """
        # allow automatic reconneciton attempts, that might have been 
        # diabled through the disconnect method.
        self.continueTrying = True
        # initialise reconnection attempt delay
        self.resetDelay()
        p = PAWSProtocol()
        p.factory = self
        return p


    def clientConnectionLost(self, connector, reason):
        logging.debug('PAWS connection lost.  Reason: %s' %  reason)
        self._connectionStateHandler(False)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
        
    def clientConnectionFailed(self, connector, reason):
        logging.error('PAWS connection failed. Reason: %s' % reason)
        self._connectionStateHandler(False)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


    def send(self, data):
        """
        Send a string of data to the PAWS service through the single connection.
        This is a convenience wrapper around the protocol.
        """
        self.connection.send(data)




class PAWSClient(object):
    """ 
    A Pachube Advanced Web-scale Socket-server (PAWS) client.
    
    This class does everything the normal client does and more.
    
    The main feature of this class is its ability to subscribe to
    resource paths (e.g. feeds, datastreams) and get notified of
    updates when they occur.
    """
    
    def __init__(self, api_key=None, feed_id=None):
        """
        @param api_key: The api key, with appropriate authorization privileges to use.
        @type api_key: string
        @param feed_id: The default feed identifier to use
        @type feed_id: string
        """
        self.api_key = api_key
        self.feed_id = feed_id

        # Store the response callback processing chains associated with each request.
        # Responses can be associated to the originating requests through the token.
        # the token forms the key in this dict.
        self.pendingResponses = dict()
        
        # Subscriptions use the same token approach to map the message data to the 
        # originating request. The values of each dict item is a tuple of the 
        # callback handler function to pass the response data to and a txpachube
        # data structure class that is used to decode the data upon its receipt.
        self.subscriptionHandlers = dict()
        
        self.headers = {'X-PachubeApiKey': self.api_key}
        
        self.factory = PAWSProtocolFactory(self._messageHandler)
    
        
    def connect(self):
        """
        Establish a connection to the Pachube PAWS service.
        
        @return: Returns a deferred that fires when the connection
                 is completed. 
        @rtype: defer.Deferred
        """
        return self.factory.connect()
    

    def disconnect(self):
        """
        Break a connection to the Pachube PAWS service
        
        @return: Returns a deferred that fires when the disconnection
                 is completed.
        @rtype: defer.Deferred
        """
        return self.factory.disconnect()
    
    
    @property
    def connected(self):
        """
        A convenience property to check the connection state.
        
        @return: The connection state of the PAWSClient
        @rtype: boolean 
        """
        return self.factory.connected


    def _messageHandler(self, msg):
        """
        Receive a message from the PAWS service. Use the token found in the response
        to find the correct pending response deferred so the response processing
        chain can process the message and return it to the caller.
        """
        logging.debug("PAWSClient has received a message:\n%s\n" % msg)
        data = json.loads(msg)
        token = data['token']

        if token in self.pendingResponses:
            self.pendingResponses[token].callback(data)
            del self.pendingResponses[token]

        elif token in self.subscriptionHandlers:
            body = self._getResponseBody(data)
            handler, dataStructureClass = self.subscriptionHandlers[token]
            dataStructure = dataStructureClass(**body)
            handler(dataStructure)            
            
        else:
            logging.error("Unrecognised message with token %s not in pendingResponses or subscriptionHandlers" % token)
            logging.error("pendingResponses tokens = %s" % str(self.pendingResponses.keys()))
            logging.error("subscriptionHandlers tokens = %s" % str(self.subscriptionHandlers.keys()))
            logging.error("No handler to process:\n%s\n" % json.dumps(data, sort_keys=True, indent=2))
  
  
    def _generateToken(self):
        """
        Make a unique token that can be used to match requests with the response.
        """
        return str(uuid.uuid1())
    

    #
    # Callbacks
    #
            
                        
    def _getResponseBody(self, response):
        """
        Most responses need to deliver the response body data. Some need
        to return data from the header only. This method provides the 
        ability to return only the response body data.
        """
        return response['body']
    
    
    def _convertToPachubeStructure(self, data, kind):
        """
        Convert the data into a DataStructure object
        """
        dataStructureClass = txpachube.getDataStructure(kind)
        dataStructure = dataStructureClass()
        dataStructure.decode(data)
        return dataStructure



    def _getResponseCodeStatusFromHeader(self, response):
        """
        Most responses need to deliver the response body data. Some need
        to return data from the header only. This method provides the 
        ability to return a success/fail criteria based on the response
        header code received.
        """
        responseCode = response['status']
        success = responseCode == 200
        if not success:
            logging.error("Expected status response code 200, received %s" % (responseCode))
        return success


    def _getLocationFromHeader(self, response):
        """
        Extract and return the location of the created item 
        from the 'Location' field in the response header.
        """
        json_data = json.loads(response)
        if json_data['status'] == 201:
            # created ok
            if 'LOCATION' in json_data['headers']:
                location = json_data['headers']["LOCATION"]
                return location
            else:
                err_str = "No response header \'Location\' field found"
                logging.error(err_str)
                raise Exception(err_str)
        else:
            err_str = "Unexpected response => %s:%s" % (response.code, response.phrase)
            logging.error(err_str)
            raise Exception(err_str)
        
            
    #
    # 
    #
    

    
    def _sendRequest(self, method, resource, body=None, token=None):
        """
        Send a request to the url, where the method argument defines the kind of request.
        Returns a deferred that returns a tuple containing the response header and the
        response body.
        
        @param method: The kind of request to make. [get|put|post|delete]
        @type method: string
        @param resource: The resource used during the request
        @type resource: string
        @param headers: A dict of header key value pairs to be used in the request
        @type headers: dict
        @param body: THe content used for the request body data.
        
        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred        
        """

        message = dict()
        message['method'] = method
        message['resource'] = resource
        message['headers'] = self.headers
        if body:
            message['body'] = body
        if token is None:
            token = self._generateToken()
        message['token'] = token
        
        logging.debug("About to send:\n%s\n" % json.dumps(message, sort_keys=True, indent=2))
        
        if self.connected:
            self.factory.send(json.dumps(message))
            d = defer.Deferred()
            self.pendingResponses[token] = d
            return d
        else:
            logging.error("Send failed, no connection exists")


    def _get(self, resource, headers):
        """ 
        Perform a get at the specified url 
        
        @param resource: The resource used during the request
        @type resource: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("get", resource, None)
        
        
    def _put(self, resource, headers, data):
        """ 
        Perform a put at the specified resource 
        
        @param resource: The resource used during the request
        @type resource: string
        @param body: The content that forms the body of the request.
        @type body: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("put", resource, body)
    
    
    def _post(self, resource, headers, data):
        """ 
        Perform a post at the specified resource 
        
        @param resource: The resource used during the request
        @type resource: string
        @param body: The content that forms the body of the request.
        @type body: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("post", resource, body)       
    
    
    def _delete(self, resource, headers):
        """ 
        Perform a delete at the specified url
        
        @param resource: The resource used during the request
        @type resource: string

        @return:  A deferred that returns a result tuple containing the response,
        and the response body.
        @rtype: twisted.internet.defer.Deferred
        """
        return self._sendRequest("delete", resource, None)        
        
        
    def _subscribe(self, resource):
        """ 
        Perform a subscribe at the specified url
        
        @param resource: The resource used during the request
        @type resource: string

        @return: A tuple contains the token used for subscription and
                 a deferred that returns a result of the subscribe
                 response. The token is needed later to unsubscribe.
        @rtype: string
        """
        token = self._generateToken()
        d = self._sendRequest("subscribe", resource, None, token)
        # _sendRequest returns a deferred allowing the caller to chain
        # up processing actions to be called when the resposne arrives.
        # By default _sendRequest add this deferred to a pendingResponses 
        # dict using the message token as the dict key. As responses are
        # processed, the normal action is to remove the token from the dict
        # as they are only used by the req/reply pair.
        # Subscription responses use the same token forever. This means 
        # we can't simply remove the matching token item from the dict and
        # continue to be able to process the messages.
        # So a separate dict is used to store the token and associated
        # callback handlers for subscrription messages.
        # However, by default we still end up with an entry in the 
        # pendingResponses dict. Conveniently each subscribe/unsubscribe 
        # request is responded to with an acknomlwedge response. Processing
        # this message results in the identical token in the pendingResponses
        # being removed. All good.
        return (token, d)
    

    def _unsubscribe(self, resource, token):
        """ 
        Perform a subscribe at the specified url
        
        @param resource: The resource used during the request
        @type resource: string
        @param token: : The token generated from the initial subscription.
        @type token: string        

        @return: A deferred that returns a result of the subscribe
                 response.
        @rtype: string
        """
        return self._sendRequest("unsubscribe", resource, None, token)

        
    #
    # Environments (Feeds)
    #
    
    
    def list_feeds(self, parameters=None):
        """ 
        Returns a paged list of Pachube's feeds that are viewable by 
        the authenticated account with a default page size of 50 feeds.
        
        @param parameters: Additional parameters to configure the search query.
        @type parameters: dict
        
        @return: A deferred that returns the response body which is a paged
                 list of feeds (default 50 per page) viewable by the api_key 
                 provided.
        @rtype: string (in the format specified by the format argument)
        
        
        Available settings for parameters:
        
        page
            Integer indicating which page of results you are requesting. Starts from 1.
            http://api.pachube.com/v2/feeds?page=2
        
        per_page
            Integer defining how many results to return per page (1 to 1000).
            http://api.pachube.com/v2/feeds?per_page=5
        
        content
            String parameter ('full' or 'summary') describing whether we 
            want full or summary results. Full results means all datastream
            values are returned, summary just returns the environment meta 
            data for each feed.
            http://api.pachube.com/v2/feeds?content=summary
        
        q
            Full text search parameter. Should return any feeds matching this string.
            http://api.pachube.com/v2/feeds?q=arduino
        
        tag
            Returns feeds containing datastreams tagged with the search query.
            http://api.pachube.com/v2/feeds?tag=temperature
        
        user
            Returns feeds created by the user specified.
            http://api.pachube.com/v2/feeds.xml?user=pachube
        
        units
            Returns feeds containing datastreams with units specified by the 
            search query.
            http://api.pachube.com/v2/feeds.xml?units=celsius
        
        status
            Possible values ('live', 'frozen', or 'all'). Whether to search 
            for only live feeds, only frozen feeds, or all feeds. Defaults to all.
            http://api.pachube.com/v2/feeds.xml?status=frozen
        
        order
            Order of returned feeds. Possible values ('created_at', 'retrieved_at',
            or 'relevance').
            http://api.pachube.com/v2/feeds.xml?order=created_at
        
        show_user
            Include user login and user level for each feed. 
            Possible values: true, false (default).
            http://api.pachube.com/v2/feeds.xml?show_user=true
        
        
        The following additional advanced parameters are more intensive 
        queries that are restricted to particular account types:
        
        lat    
            Used to find feeds located around this latitude. 
            Used if ids/_datastreams_ are not specified.
            lat=51.5235375648154
        
        lon
            Used to find feeds located around this longitude. 
            Used if ids/_datastreams_ are not specified.
            lon=-0.0807666778564453
        
        distance
            search radius
            distance=5.0
        
        distance_units
            miles or kms (default).
            distance_units=miles        

        If api_key argument is not set when calling this method then the
        value set during this object's instantiation (ie. in __init__) is used.        
        """
        d = self._get("/feeds", parameters)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, txpachube.List_Feeds_Msg)
        return d
    

    def create_feed(self, data=None):
        """ 
        Creates a new feed.
        
        @param data: A string detailing the environment to be created.
        @type data: string
        
        @return: A deferred that returns the feed_id of the newly created feed. 
        @rtype: string

        """
        
        def getFeedIdFromLocation(location):
            """
            Extract and return the new feed id from the 'Location' field in the response header.
            """
            feed_id = location.split("/")[-1]
            return feed_id


        d = self._post('/feeds', data)
        d.addCallback(self._getLocationFromHeader)
        d.addCallback(getFeedIdFromLocation)
        return d
    
    
    def read_feed(self, feed_id, parameters=None):
        """ 
        Returns the most recent datastreams for environment [feed_id], viewable by the api_key provided
        
        @param feed_id: The feed identifier
        @type feed_id: string
        @param parameters: Additional parameters to configure the search query.
        @type parameters: dict
        
        @return: A deferred that returns a txpachube.Environment object populated
                 from the body of the response.
        @rtype: txpachube.Environment
        
        
        Available settings for parameters:
        datastream
            Filter the returned datastreams. Comma separated datastream IDs.
            http://api.pachube.com/v2/feeds/123.json?datastreams=energy,power

        show_user
            Include user login and user level for each feed. 
            Possible values: true, false (default).
            http://api.pachube.com/v2/feeds/123.xml?show_user=true (json/xml only)        


        Available settings for parameters supporting historical queries:  
        start: 
            Defines the starting point of the query as a timestamp, 
            e.g. 2010-05-20T11:01:46Z. The default value is blank.

        end: 
        Defines the end point of the data returned as a timestamp, 
        e.g. 2010-05-21T11:01:46Z. The default value is set to the current timestamp.

        duration:
            Specifies the duration of the query.
            If used in conjunction with end it will request the data prior to the end date.
            If used in conjunction with start it will request the data after the start date.
            If used by itself it will give the most recent data for the duration specified.
            It is incorrect to specify start, end and duration

            The format is <number><time unit> e.g. 10minutes, 6hours

            The valid time units are:
            seconds
            minute(s)
            hour(s)
            day(s)
            week(s)
            month(s)
            year(s)

        page: 
            Defines which page we are looking at of the matching results. 
            If not set, the default value is 1

        per_page: 
            Defines how many results are returned per page. 
            If not set this value defaults to 100. Maximum value is 1000

        time: 
            Returns the feed with the values as they were at the specified timestamp. 
            There are a few points to note about this functionality:
                Only the values of the datastream and their timestamps are changed, 
                all other metadata reflects the current state of the feed and its datastreams
                If a datastream had no values at the time specified (either because it didn't
                exist or because it hadn't been updated) it will be excluded from the output
        
        find_previous:
            Will also return the previous value to the date range being requested. 
            Note that this is useful for any graphing because if you want to draw a graph of 
            the date range you specified you would end up with a small gap until the first value.

        interval_type:
            If set to "discrete" the data will be returned in fixed time interval format 
            according to the inverval value supplied. If this is not set, the raw datapoints
            will be returned.

        interval: 
            Determines what interval of data is requested and is defined in seconds between
            the datapoints. If a value is passed in which does not match one of these values, 
            it is rounded up to the next value. 
            The acceptable values are currently:
                Value    Description                     Maximum range in one query
                0        Every snapshot stored            6 hours
                30       30 second interval data          12 hours
                60       One snapshot every minute        24 hours
                300      One snapshot every 5 minutes     5 days
                900      One snapshot every 15 minutes    14 days
                3600     One snapshot per hour            31 days
                10800    One snapshot per three hours     90 days
                21600    One snapshot per six hours       180 days
                43200    One snapshot per twelve hours    1 year
                86400    One snapshot per day             1 year
                
        If api_key or feed_id arguments are not set when calling this method then the
        values set during this object's instantiation (ie. in __init__) are used.
        """
        resource = '/feeds/%s' % feed_id
        d = self._get(resource, parameters)
        d.addCallback(self._getResponseBody)
        d.addCallback(self._convertToPachubeStructure, format, txpachube.View_Feed_Msg)
        return d    
    

    def subscribe(self, resource, subscriptionHandler):
        """
        Subscribe to the resource for updates of changes.
        
        @param resource: The resource to access
        @type resource: string
        @param subscriptionHandler: A callable that will receive the data structure
                                   returned periodically as a result of the subscription.
        @type subscriptionHandler: callable
        
        @return: A tuple containing the token used for subscription and a deferred 
                that returns the state of the subscription request. The token is 
                needed to unsubscribe later.
        @rtype: string
        """
        # determine the expected response object kind based on
        # the resource being subscribed to.
        if 'datastreams' in resource:
            dataStructureClass = txpachube.Datastream
        else:
            dataStructureClass = txpachube.Environment
        
        token, d = self._subscribe(resource)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        self.subscriptionHandlers[token] = (subscriptionHandler, dataStructureClass)
        return token, d
        
    
    
    def unsubscribe(self, resource, token):
        """
        Unsubscribe from receiving update from the specified resource.
        
        @param resource: The resource to access
        @type resource: string
        @param token: : The token generated from the initial subscription.
        @type token: string
                
        @return: A deferred that returns the state of the unsubscription request 
        @rtype: boolean
        """
        if token in self.subscriptionHandlers:
            del self.subscriptionHandlers[token]
            
        d = self._unsubscribe(resource, token)
        d.addCallback(self._getResponseCodeStatusFromHeader)
        return d
    
    