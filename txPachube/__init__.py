#!/usr/bin/env python

"""
This package implements the Pachube API in Python. It is built on top of the 
Twisted event driven networking framework.

This implementation closely follows the documented Pachube API
located at: http://api.pachube.com/v2/
Much of the API documentation has been shamelessly duplicated within the
method docstrings. The documentation on the Pachube API seems quite clear.
Embedding the documentation within the docstrings means that the Python
help(txPachube) output will be useful.
Always refer back to the Pachube site for the most recent, up to date, API
documentation.

The Pachube API allows users to request data in a variety of formats.
This implementation performs the following:
1. If JSON (default) format is requested, and the request is expected to
   return a response body then the result returned to the user of this
   module is a dict produced from json decoding the body string. This should 
   make the result object easier to use.
2. Any other format will return a string and you are free to manipulate
   it as you see fit. For example if XML format is requested then you 
   may choose to parse this with ElementTree, minidom, etc. PNG is a 
   valid response in a once circumstance.
   
Dependencies (other than Python):
twisted 11.0.0
pyOpenSSL

"""
import datetime
try:
    from xml.etree import cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
import json
import logging
import urllib



version = (0, 0, 2)



# store the detected XML (EEML) namespace as it is need when search elements
Namespace = None

EEML_NAMESPACE = 'eeml'
OPENSEARCH_NAMESPACE = 'opensearch'
namespace_map = {EEML_NAMESPACE : 'http://www.eeml.org/xsd/0.5.1',
                 OPENSEARCH_NAMESPACE : 'http://a9.com/-/spec/opensearch/1.1/'}
for namespace in namespace_map:
    etree.register_namespace(namespace, namespace_map[namespace])

        

class DataFormats(object):
    """
    Define the data formats that can be sent and received
    """
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PNG = "png"



class DataFields(object):
    """
    Define the field names used within the data passed between the client
    and Pachube.
    """
    # A selection of common environment field keys that are useful when
    # building/inspecting json format objects to be sent to pachube.
    About = 'about'
    Access_Method = 'access_method'
    Access_Methods = 'access_methods'
    Api_Key = 'api_key'
    At = 'at'
    Creatable_Role = 'creatable_role'
    Creatable_Roles = 'creatable_roles'
    Creator = 'creator'
    Current_Value = 'current_value'
    Data = 'data'
    Datapoints = 'datapoints'
    Datastream_Id = 'datastream_id'
    Datastream_Trigger = 'datastream-trigger'
    Datastream_Triggers = 'datastream-triggers'
    Datastreams = 'datastreams'
    Datastreams_Allowed = 'datastreams_allowed'
    Datastreams_Count = 'datastreams_count'
    Deliver_Email = 'deliver_email'
    Description = 'description'
    Display_Activity = 'display_activity'
    Display_Information = 'display_information'
    Display_Stats = 'display_stats'
    Disposition = 'disposition'
    Domain = 'domain'
    Elevation = 'ele'
    Email = 'email'
    Environment = 'environment'
    Environment_Id = 'environment_id'
    Exposure = 'exposure'
    Feed = 'feed'
    Feed_Id = 'feed_id'
    First_Name = 'first_name'
    Full_Name = 'full_name'
    Icon = 'icon'
    Id = 'id'
    Key = 'key'
    Keys = 'keys'
    Label = 'label'  # unit label
    Last_Name = 'last_name'
    Latitude = 'lat'
    Location = 'location'
    Login = 'login'
    Longitude = 'lon'
    Maximum_Value = 'max_value'
    Minimum_Value = 'min_value'
    Name = 'name'
    Notified_At = 'notified_at'
    Organisation = 'organisation'
    Permission = 'permission'
    Permissions = 'permissions'
    Private = 'private'
    Private_Access = 'private_access'
    Receive_Forum_Notifications = 'receive_formum_notifications'
    Referer = 'referer'
    Resources = 'resources'
    Results = 'results'
    Role = 'role'
    Roles = 'roles'
    Source_Ip = 'source_ip'
    Status = 'status'
    Stream_Id = 'stream_id'
    Subscribed_To_Mailings = 'subscribed_to_mailings'
    Symbol = 'symbol'  # unit symbol
    Tag = 'tag'
    Tags = 'tags'
    Threshold_Value = 'threshold_value'
    Title = 'title'
    Timestamp = 'timestamp'
    Timezone = 'timezone'
    Total_Api_Access_Count = 'total_api_access_count'
    Total_Results = 'totalResults'
    Triggering_Datastream = 'triggering_datastream'
    Trigger_Type = 'trigger_type'
    Type = 'type'  # unit type
    Unit = 'unit'
    User = 'user'
    Users = 'users'
    Updated = 'Updated'
    Url = 'url'
    Value = 'value'
    Version = 'version'
    Website = 'website'



class DataStructure(object):
    """
    Base class for Pachube data structure objects
    
    Serialized versions of objects deriving from this class are passed between
    the Pachube API and the txPachube client. These structures are designed in
    such a way that they can be used for JSON or XML (EEML).
    """
    

            
    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        raise NotImplementedError
    

    def toXml(self):
        """ 
        Return the object as an xml ElementTree
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        raise NotImplementedError
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        raise NotImplementedError
    
        
    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        raise NotImplementedError
          

    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            eeml = etree.Element('eeml')
            eeml.attrib['xmlns'] = 'http://www.eeml.org/xsd/0.5.1'
            eeml.attrib['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
            eeml.attrib['version'] = '0.5.1'
            eeml.attrib['xsi:schemaLocation'] = 'http://www.eeml.org/xsd/005 http://www.eeml.org/xsd/005/005.xsd'
            eeml.append(self.toXml())
            return etree.tostring(eeml, 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))
    
    
    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # parse xml string, rip off the eeml wrapper and process
            # xml elements by handing off to fromXml method. All
            # viewable (feed, datastream, datapoint) XML items come 
            # wrapped in the eeml, environment tags. 
            element = etree.fromstring(data)
            environment = element.find("{%s}%s" % (namespace_map[EEML_NAMESPACE], DataFields.Environment))
            if environment is not None:
                self.fromXml(environment)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))

              
    def __str__(self):
        """ Return a string representation of this datapoint """
        return json.dumps(self.toDict(), sort_keys=True, indent=2)
        

class Unit(DataStructure):
    """ Models a Unit item within a Pachube data structure """
    
    # See http://www.eeml.org/#units
    Basic_Si = 'basicSI'                               # m, kg, etc
    Derived_Si = 'derivedSI'                           # newtons, ohms, hertz, etc
    Conversion_Based_Units = 'conversionBasedUnits'    # inches
    Derived_Units = 'derivedUnits'                     # miles per hour
    Context_Dependent_Units = 'contextDependentUnits'  # heartbeats per minute
    Valid_Unit_Types = [Basic_Si,
                        Derived_Si,
                        Conversion_Based_Units,
                        Derived_Units,
                        Context_Dependent_Units]
    
    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.Label,
                            DataFields.Type,
                            DataFields.Symbol]
        self.label = None
        self.type = None
        self.symbol = None

        # initialise Unit attributes to specified values or None.
        self.fromDict(kwargs)


    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        unitDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                unitDict[attribute] = str(attribute_value)
        return unitDict
    

    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:
                if attribute == DataFields.Type:
                    if attribute_value not in Unit.Valid_Unit_Types:
                        raise Exception("Invalid unit type \'%s\' not in %s" % (attribute_value,
                                                                                Unit.Valid_Unit_Types))
                setattr(self, attribute, attribute_value)        
        
            
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        unit = etree.Element(DataFields.Unit)
        if self.type:
            unit.attrib[DataFields.Type] = self.type
        if self.symbol:
            unit.attrib[DataFields.Symbol] = self.symbol
        unit.text = self.label            

        return unit


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        unit = element.find(DataFields.Unit)
        if unit is not None:
            unit_type = unit.attrib.get(DataFields.Type, None)
            if unit_type:
                self.type = unit_type
            unit_symbol = unit.attrib.get(DataFields.Symbol, None)
            if unit_symbol:
                self.symbol = unit_symbol
            self.label = unit.text
    
    

class Datapoint(DataStructure):
    """ Models a Datapoint item within a datastream """
    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.At,
                            DataFields.Value]
        self.at = None
        self.value = None

        # initialise Datapoint attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        datapointDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                datapointDict[attribute] = str(attribute_value)
        return datapointDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:
                setattr(self, attribute, attribute_value)
    
    
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        value = etree.Element(DataFields.Value)
        value.attrib[DataFields.At] = self.at
        value.text = self.value
        return value


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        datapoint = element.find(DataFields.Value)
        if datapoint is not None:
            at_time = datapoint.attrib.get(DataFields.At, None)
            if at_time:
                self.at = at_time
            value = datapoint.text
            if value:
                self.value = value       
  
    
    
class Location(DataStructure):

    # Exposure kinds
    Indoor = "indoor"
    Outdoor = "outdoor"
    Valid_Exposure_Kinds = [Indoor, Outdoor]
    
    # Domina kinds
    Physical = 'physical'
    Virtual = 'virtual'
    Valid_Domain_Kinds = [Physical, Virtual]
    
    # Disposition kinds
    Fixed = 'fixed'
    Mobile = 'mobile'
    Valid_Disposition_Kinds = [Fixed, Mobile]
    
    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.Disposition,
                            DataFields.Domain,
                            DataFields.Elevation,
                            DataFields.Exposure,
                            DataFields.Latitude,
                            DataFields.Longitude,
                            DataFields.Name]
        self.disposition = None
        self.domain = None
        self.ele = None
        self.exposure = None
        self.lat = None
        self.lon = None
        self.name = None
        
        # initialise attributes to specified values.
        self.fromDict(kwargs)
        
            
    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        locationDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                locationDict[attribute] = str(attribute_value)
        return locationDict


    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:
                if attribute == DataFields.Disposition:
                    if attribute_value not in Location.Valid_Disposition_Kinds:
                        raise Exception("Invalid disposition \'%s\' not in %s" % (attribute_value,
                                                                                  Location.Valid_Disposition_Kinds))
                if attribute == DataFields.Domain:
                    if attribute_value not in Location.Valid_Domain_Kinds:
                        raise Exception("Invalid domain \'%s\' not in %s" % (attribute_value,
                                                                             Location.Valid_Domain_Kinds))
                        
                if attribute == DataFields.Exposure:
                    if attribute_value not in Location.Valid_Exposure_Kinds:
                        raise Exception("Invalid exposure \'%s\' not in %s" % (attribute_value,
                                                                               Location.Valid_Exposure_Kinds))
                        
                setattr(self, attribute, attribute_value)
        

    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        location = etree.Element(DataFields.Location)
        if self.domain:
            location.attrib[DataFields.Domain] = self.domain
        if self.exposure:
            location.attrib[DataFields.Exposure] = self.exposure
        if self.disposition:
            location.attrib[DataFields.Disposition] = self.disposition                
        
        if self.name:
            name = etree.SubElement(location, DataFields.Name)
            name.text = self.name
        if self.lat:
            lat = etree.SubElement(location, DataFields.Latitude)
            lat.text = str(self.lat)                
        if self.lon:
            lon = etree.SubElement(location, DataFields.Longitude)
            lon.text = str(self.lon)
        if self.ele:
            ele = etree.SubElement(location, DataFields.Elevation)
            ele.text = str(self.ele)
                            
        return location      

    
        
    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        location = element.find(DataFields.Location)
        if location is not None:
            domain = location.attrib.get(DataFields.Domain, None)
            if domain:
                self.domain = domain
            exposure = location.attrib.get(DataFields.Exposure, None)
            if exposure:
                self.exposure = exposure
            disposition = location.attrib.get(DataFields.Disposition, None)
            if disposition:
                self.disposition = disposition
            
            name = location.find(DataFields.Name)
            if name is not None:
                self.name = name.text
                
            latitude = location.find(DataFields.Latitude)
            if latitude is not None:
                self.lat = float(latitude.text)
                
            logitude = location.find(DataFields.Longitude)
            if logitude is not None:
                self.lon = float(logitude.text)
                
            elevaltion = location.find(DataFields.Elevation)
            if elevaltion is not None:
                self.ele = elevaltion.text                
   
    
    
class Datastream(DataStructure):
    """ Models a datastream structure within an environment """
    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.At,
                            DataFields.Current_Value,
                            DataFields.Datapoints,
                            DataFields.Id,
                            DataFields.Maximum_Value,
                            DataFields.Minimum_Value,
                            DataFields.Tags,
                            DataFields.Unit]
        self.at = None
        self.current_value = None
        self.datapoints = []
        self.id = None
        self.max_value = None
        self.min_value = None
        self.tags = []
        self.unit = None

        # initialise attributes to specified values.
        self.fromDict(kwargs)


    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        datastreamDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:                    
                if attribute == DataFields.Datapoints:
                    datapoints = attribute_value
                    datastreamDict[attribute] = list()
                    for datapoint in datapoints:
                        datastreamDict[attribute].append(datapoint.toDict())
                
                elif attribute == DataFields.Unit:
                    unit = attribute_value
                    datastreamDict[attribute] = unit.toDict()
                else:
                    datastreamDict[attribute] = str(attribute_value)
        return datastreamDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:
                if attribute == DataFields.Datapoints:
                    if not hasattr(self, DataFields.Datapoints):
                        setattr(self, attribute, list())
                    datapoints = getattr(self, DataFields.Datapoints)
                    datapoints_list = attribute_value
                    for datapointsKwargs in datapoints_list:
                        datapoints.append(Datapoint(**datapointsKwargs))
                    setattr(self, attribute, datapoints)
                    
                elif attribute == DataFields.Unit:
                    unitKwargs = attribute_value
                    setattr(self, attribute, Unit(**unitKwargs))
                else:
                    setattr(self, attribute, attribute_value)
    
    
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        data = etree.Element(DataFields.Data)
        data.attrib[DataFields.Datastream_Id] = str(self.id)
        
        if self.tags:
            for tag_label in self.tags:
                tag = etree.SubElement(data, DataFields.Tag)
                tag.text = tag_label
                
        if self.current_value:
            current_value = etree.SubElement(data, DataFields.Current_Value)
            current_value.text = str(self.current_value)
            
        if self.max_value:
            max_value = etree.SubElement(data, DataFields.Maximum_Value)
            max_value.text = str(self.max_value)
        
        if self.min_value:
            min_value = etree.SubElement(data, DataFields.Minimum_Value)
            min_value.text = str(self.min_value)
                        
        if self.unit:
            data.append(self.unit.toXml())
            
        if self.datapoints:
            datapoints = etree.SubElement(data, DataFields.Datapoints)
            for datapoint in self.datapoints:
                datapoints.append(datapoint.toXml())
                                  
        return data
    
        
    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        data = element.find(DataFields.Data)
        if data is not None:
            id = data.attrib.get(DataFields.Datastream_Id, None)
            if id:
                self.id = id
            
            if data.find(DataFields.Tag) is not None:
                self.tags = []
                for tag in data.findall(DataFields.Tag):
                    self.tags.append(tag.text)
                    
            current_value = data.find(DataFields.Current_Value)
            if current_value is not None:
                self.current_value = current_value
                at_time = current_value.attrib.get(DataFields.At, None)
                if at_time:
                    self.at = at_time
                
            max_value = data.find(DataFields.Maximum_Value)
            if max_value is not None:
                self.max_value = max_value           

            min_value = data.find(DataFields.Minimum_Value)
            if min_value is not None:
                self.min_value = min_value
            
            unit = data.find(DataFields.Unit)
            if unit is not None:
                self.unit = Unit()
                self.unit.fromXml(unit)
                
                
            datapoints = data.find(DataFields.Datapoints)
            if datapoints is not None:
                self.datapoints = []
                for value in datapoints.findall(DataFields.Value):
                    d = Datapoint()
                    d.fromXml(value)
                    self.datapoints.append(datapoint)            


    def setCurrentValue(self, value):
        """
        Set the current value of the datastream.
        
        @param value: the current value for the datastream
        @type value: string
        """
        self.current_value = value



    def addDatapoint(self, timestamp, value):
        """
        Add a historical datapoint to the datastream.

        @param timestamp: An timestamp in ISO8601 format
        @type timestamp: string
        @param value: the current value for the datastream
        @type value: string
        """
        inDict = {DataFields.At : timestamp, DataFields.Value : value}
        self.datapoints.append(Datapoint(**inDict))
          
        
    def clear(self):
        """
        Clear current value and datapoints. This method is called
        after Pachube has been updated with the current contents.
        """
        self.current_value = None
        del self.datapoints[:]
        
        
                              
class Environment(DataStructure):
    """ Models a Pachube Environment (feed) object """


    def __init__(self, **kwargs):
        self._attributes = [DataFields.Creator,
                            DataFields.Datastreams,
                            DataFields.Description,
                            DataFields.Feed,
                            DataFields.Icon,
                            DataFields.Id,
                            DataFields.Location,
                            DataFields.Private,
                            DataFields.Status,
                            DataFields.Tags,
                            DataFields.Title,
                            DataFields.Updated,
                            DataFields.Version,
                            DataFields.Website]
        self.creator = None
        self.datastreams = {}
        self.description = None
        self.feed = None
        self.icon = None
        self.id = None
        self.location = None
        self.private = None
        self.status = None
        self.tags = None
        self.title = None
        self.updated = None
        self.version = version
        self.website = None

        # initialise attributes to specified values.
        self.fromDict(kwargs)



    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        environmentDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                if attribute == DataFields.Id:
                    environmentDict[attribute] = attribute_value
                    
                elif attribute == DataFields.Location:
                    environmentDict[attribute] = self.location.toDict()
                
                elif attribute == DataFields.Datastreams:
                    datastreams = []
                    for datastream_id, datastream in self.datastreams.items():
                        datastreams.append(datastream.toDict())
                        environmentDict[DataFields.Datastreams] = datastreams
                else:
                    environmentDict[attribute] = str(attribute_value)
        return environmentDict
    

    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:

                if attribute == DataFields.Location:
                    locationKwargs = attribute_value
                    setattr(self, attribute, Location(**locationKwargs))
                    
                elif attribute == DataFields.Datastreams:
                    if not hasattr(self, DataFields.Datastreams):
                        setattr(self, attribute, dict())
                    datastreams = getattr(self, DataFields.Datastreams)
                    datastreamsKwargs = attribute_value
                    for datastreamKwargs in datastreamsKwargs:
                        datastream = Datastream(**datastreamKwargs)
                        datastreams[datastream.id] = datastream
    
                else:
                    setattr(self, attribute, attribute_value)
    
    
    def toXml(self):
        """ 
        Return the object as an xml ElementTree
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        env = etree.Element(DataFields.Environment)
        if self.creator:
            env.attrib[DataFields.Creator] = str(self.creator)
        if self.id:
            env.attrib[DataFields.Id] = str(self.id)
        if self.updated: 
            env.attrib[DataFields.Updated] = str(self.updated)
            
        if self.description:
            desc = etree.SubElement(env, DataFields.Description)
            desc.text = str(self.description)
        if self.feed:
            feed = etree.SubElement(env, DataFields.Feed)
            feed.text = str(self.feed)
        if self.icon:
            icon = etree.SubElement(env, DataFields.Icon)
            icon.text = str(self.icon)
        if self.private:
            private = etree.SubElement(env, DataFields.Private)
            private.text = str(self.private)
        if self.status:
            status = etree.SubElement(env, DataFields.Status)
            status.text = str(self.status)
        if self.tags:
            for tag_text in self.tags:
                tag = etree.SubElement(env, DataFields.Tag)
                desc.text = str(tag_text)
        if self.title:
            title = etree.SubElement(env, DataFields.Title)
            title.text = str(self.title)
        if self.version:
            version = etree.SubElement(env, DataFields.Version)
            version.text = str(self.version)                
        if self.website:
            website = etree.SubElement(env, DataFields.Website)
            website.text = str(self.website) 
                            
        if self.location:
            env.append(self.location.toXml())
         
        if self.datastreams:
            for datastream_id, datastream in self.datastreams.items():
                env.append(datastream.toXml())
                
        return env
                    

    
        
    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        environment = element.find(DataFields.Environment)
        if environment is not None:
            creator = environment.attrib.get(DataFields.Creator, None)
            if creator:
                self.creator = creator
            id = environment.attrib.get(DataFields.Id, None)
            if id:
                self.id = id
            updated = environment.attrib.get(DataFields.Updated, None)
            if updated:
                self.updated = updated 
                
            description = environment.find(DataFields.Description, None)
            if description is not None:
                self.description = description
            feed = environment.find(DataFields.Feed, None)
            if feed is not None:
                self.feed = feed.text
            icon = environment.find(DataFields.Icon, None)
            if icon is not None:
                self.icon = icon.text
            private = environment.find(DataFields.Private, None)
            if private is not None:
                self.private = private.text
            status = environment.find(DataFields.Status, None)
            if status is not None:
                self.status = status.text
            tag = environment.find(DataFields.Tag, None)
            if tag is not None:
                self.tags = []
                for tag in environment.findall(DataFields.Tag):
                    self.tags.append(tag.text)
            title = environment.find(DataFields.Title, None)
            if title is not None:
                self.title = title.text
            version = environment.find(DataFields.Version, None)
            if version is not None:
                self.version = version.text
            website = environment.find(DataFields.Website, None)
            if website is not None:
                self.website = website.text
                
            location = environment.find(DataFields.Location)
            if location is not None:
                loc = Location()
                loc.fromXml(location)
                self.location = loc
            
            data_element = environment.find(DataFields.Data)
            if data_element is not None:
                self.datastreams = []
                for datastream in environment.findall(DataFields.Data):
                    ds = Datastream()
                    ds.fromXml(datastream)
                    self.datastreams.append(ds)
                    


    def setCurrentValue(self, datastream_id, value):
        """
        Set the current value for a datastream.
        
        @param datastream_id: The identifier of the datastream to be updated
        @type datastream_id: string
        @param value: The current value for the datastream
        @type value: string
        """
        if datastream_id not in self.datastreams:
            inDict = {DataFields.Id : datastream_id}
            self.datastreams[datastream_id] = Datastream(**inDict)
        datastream = self.datastreams[datastream_id]
        datastream.setCurrentValue(value)

    def addDatapoint(self, datastream_id, at_time, value):
        """
        Set a datepoint in a datastream.
        
        @param datastream_id: The identifier of the datastream to be updated
        @type datastream_id: string
        @param at_time: The timestamp for the datapoint, in ISO8601 format
        @type at_time: string
        @param value: The current value for the datastream
        @type value: string
        """
        if datastream_id not in self.datastreams:
            inDict = {DataFields.Id : datastream_id}
            self.datastreams[datastream_id] = Datastream(**inDict)
        datastream = self.datastreams[datastream_id]
        datastream.addDatapoint(at_time, value)
        
    
    def setLocation(self, name=None, exposure=None, domain=None, disposition=None,
                    latitude=None, longitude=None, elevation=None):
        """
        Set the location data for this environment
        
        @param name: The name of the location
        @type name: string
        @param exposure: Defines the exposure of the environment. Use 
                         constants from the Location data structure:
                         eg. Location.Outdoor | lLocation.Indoor
        @type exposure: string
        @param domain: Defines the domain of the enviromnment. Use  
                       constants from the Location data structure:
                       Location.Physical | Location.Virtual
        @type domain: string
        @param disposition: Defines the disposition of the enviromnment. Use
                            constants from the Location data structure:
                            Location.Fixed | Location.Mobile
        @type name: string
        @param latitude: The latitude of the environment
        @type latitude: float
        @param longitude: The longitude of the environment
        @type longitude: float
        @param elevation: The elevation of the environment
        @type elevation: float 
        """
        locationKwargs = dict()
        if name:
            locationKwargs[DataFields.Name] = name
        if exposure:
            locationKwargs[DataFields.Exposure] = exposure
        if domain:
            locationKwargs[DataFields.Domain] = domain
        if disposition:
            locationKwargs[DataFields.Disposition] = disposition
        if latitude:
            locationKwargs[DataFields.Latitude] = latitude
        if longitude:
            locationKwargs[DataFields.Longitude] = longitude
        if elevation:
            # elevation is stored internally as a string
            locationKwargs[DataFields.Elevation] = "%.1f" % elevation
        self.location = Locaiton(**locationKwargs)



class EnvironmentList(DataStructure):
    """ Models a Pachube Environment (feed) list object """
    
    def __init__(self, **kwargs):
        
        self.total_results = None
        self.feeds = []

        # initialise attributes to specified values.
        self.fromDict(kwargs)        
        
          
    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        environmentListDict = dict()
        environmentListDict[DataFields.Total_Results] = self.total_results
        results = []
        for feed in self.feeds:
            results.append(feed.toDict())
        environmentListDict[DataFields.Results] = results
        
        return environmentListDict
        
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        total_results = inDict.get(DataFields.Total_Results, None)
        if total_results:
            self.total_results = total_results
        
        results = inDict.get(DataFields.Results, None)
        if results:
            self.feeds = []
            for result in results:
                self.feeds.append(Environment(**result))
    

    # The txPachube implementation never sends this structure to Pachube.
    # It only ever receives environment lists from Pachube.
    # Therefore toXml and encode methods are not required    
    def toXml(self):
        """ 
        Return the object as an xml ElementTree
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        return None
    

    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        total_results = element.find('{%s}%s' % (namespace_map[OPENSEARCH_NAMESPACE], DataFields.Total_Results))
        if total_results is not None:
            self.total_results = total_results.text
            
        environment = element.find(DataFields.Environment)
        if environment is not None:
            self.feeds = []
            for environment in element.findall(DataFields.Environment):
                env = Environment()
                env.fromXml(environment)
                self.feeds.append(env)
                
            
        
    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        # the txPachube implementation only ever receives environment lists from Pachube.
        # It never sends them, hence this method is never used.
        pass

    
    
    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """
        # The EnvironmentList object must specialise the decode method because it
        # needs to obtain data from the eeml header which is stripped off in the 
        # inherited implementation.
        #
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # parse xml string, rip off the eeml wrapper and process
            # xml elements by handing off to fromXml method. All
            # viewable (feed, datastream, datapoint) XML items come 
            # wrapped in the eeml, environment    
            element = etree.fromstring(data)
            self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format)) 

class Trigger(DataStructure):
    """ Models a Trigger item """
    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.Threshold_Value,
                            DataFields.User,
                            DataFields.Notified_At,
                            DataFields.Url,
                            DataFields.Trigger_Type,
                            DataFields.Id,
                            DataFields.Environment_Id,
                            DataFields.Stream_Id]
        self.threshold_value = None
        self.user = None
        self.notified_at = None
        self.url = None
        self.trigger_type = None
        self.id = None
        self.environment_id = None
        self.stream_id = None

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        triggerDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                if attribute in [DataFields.Id, DataFields.Environment_Id]:
                    triggerDict[attribute] = attribute_value
                else:
                    triggerDict[attribute] = str(attribute_value)
        return triggerDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        for attribute in self._attributes:
            attribute_value = inDict.get(attribute, None)
            if attribute_value:
                if attribute in [DataFields.Id, DataFields.Environment_Id]:
                    int_value = int(attribute_value)
                    setattr(self, attribute, attribute_value)
                else:
                    setattr(self, attribute, attribute_value)
    
    
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        datastream_trigger = etree.Element(DataFields.Datastream_Trigger)
        id = etree.SubElement(datastream_trigger, DataFields.Id)
        id.attrib['type'] = 'integer'
        id.text = str(self.id)
        
        if self.url:
            url = etree.SubElement(datastream_trigger, DataFields.Url)
            url.text = self.url
        if self.trigger_type:
            trigger_type = etree.SubElement(datastream_trigger, DataFields.Trigger_Type.replace("_", "-"))
            trigger_type.text = self.trigger_type            
        if self.threshold_value:
            threshold_value = etree.SubElement(datastream_trigger, DataFields.Threshold_Value.replace("_", "-"))
            threshold_value.attrib['type'] = 'float'
            threshold_value.text = self.threshold_value 
        if self.notified_at:
            notified_at = etree.SubElement(datastream_trigger, DataFields.Notified_At.replace("_", "-"))
            notified_at.attrib['type'] = 'datetime'
            notified_at.text = self.notified_at 
        if self.user:
            user = etree.SubElement(datastream_trigger, DataFields.User)
            user.text = self.user
        if self.environment_id:
            environment_id = etree.SubElement(datastream_trigger, DataFields.Environment_Id.replace("_", "-"))
            environment_id.attrib['type'] = 'integer'
            environment_id.text = str(self.environment_id)
        if self.stream_id:
            stream_id = etree.SubElement(datastream_trigger, DataFields.Stream_Id)
            stream_id.text = self.stream_id

        return datastream_trigger


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        datastream_trigger = element.find(DataFields.Datastream_Trigger)
        if datastream_trigger is not None:
            id = datastream_trigger.find(DataFields.Id)
            if id is not None:
                self.id = int(id.text)
            url = datastream_trigger.find(DataFields.Url)
            if url is not None:
                self.url = url.text                
            trigger_type = datastream_trigger.find(DataFields.Trigger_Type.replace("_", "-"))
            if trigger_type is not None:
                self.trigger_type = trigger_type.text
            threshhold_value = datastream_trigger.find(DataFields.Threshold_Value.replace("_", "-"))
            if threshhold_value is not None:
                self.threshhold_value = float(threshhold_value.text)            
            notified_at = datastream_trigger.find(DataFields.Notified_At.replace("_", "-"))
            if notified_at is not None:
                self.notified_at = notified_at.text
            user = datastream_trigger.find(DataFields.User)
            if user is not None:
                self.user = user.text                          
            environment_id = datastream_trigger.find(DataFields.Environment_Id.replace("_", "-"))
            if environment_id is not None:
                self.environment_id = int(environment_id.text)           
            stream_id = datastream_trigger.find(DataFields.Stream_Id)
            if stream_id is not None:
                self.stream_id = stream_id.text  


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))                            

class TriggerList(DataStructure):
    """
    Models a Trigger list item
    
    The json structure of this object is actually a list while all
    the others are a dict. To allow object initialisation using the
    normal **kwargs approach (and to allow decoding) we need to wrap
    the list in a dict. The wrapper dict uses the key DataFields.Datastream_Trigger.
    """
    
    def __init__(self, **kwargs):
        self.triggers = []

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        # This object is actually contained in a list
        triggers = []
        for trigger in self.triggers:
            triggers.append(trigger.toDict())
        return triggers
        
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        # The json structure of this object is actually a list. To allow
        # this object to be initialised and decoded, the list is wrapped
        # in a dict with a key identical to the XML verison which is
        # DataFields.Datastream_Trigger.
        # Remove the wrapper dict to access triggers list

        triggersList = inDict[DataFields.Datastream_Trigger]
        self.triggers = []
        for triggerDict in triggersList:
            self.triggers.append(Trigger(**triggerDict))
    
    
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        datastream_triggers = etree.Element(DataFields.Datastream_Triggers)
        datastream_triggers.attrib['type'] = 'array'
        for trigger in self.triggers:
            datastream_triggers.append(trigger.toXml())

        return datastream_triggers


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """
        datastream_triggers = element.find(DataFields.Datastream_Triggers)
        if datastream_triggers:
            self.triggers = []
            for datastream_trigger in datastream_triggers.findall(DataFields.Datastream_Trigger):
                trigger = Trigger()
                trigger.fromXml(datastream_trigger)
                self.triggers.append(trigger)


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            # The json structure of this object is actually a list.
            # wrap it in a dict for a consistent input to fromDict
            inDict = {DataFields.Datastream_Trigger : json.loads(data)}
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))  
    
    
# TODO: Define a Permisisons data structure and use it in Key structures. 
            
class Key(DataStructure):
    """ Models a API Key item """

    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.Id,
                            DataFields.Api_Key,
                            DataFields.Label,
                            DataFields.Permissions]
        self.id = None
        self.api_key = None
        self.label = None
        self.permissions = None

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        keyDict = dict()
        keyAttrsDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                if attribute == DataFields.Permissions:
                    access_methods = dict()
                    access_methods[DataFields.Access_Methods] = attribute_value
                    keyAttrsDict[attribute] = access_methods
                else:
                    keyAttrsDict[attribute] = str(attribute_value)
        keyDict[DataFields.Key] = keyAttrsDict
        return keyDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        keyDict = inDict.get(DataFields.Key, None)
        if keyDict:
            for attribute in self._attributes:
                attribute_value = keyDict.get(attribute, None)
                if attribute_value:
                    if attribute == DataFields.Permissions:
                        attribute_value = attribute_value[0][DataFields.Access_Methods]
                    setattr(self, attribute, attribute_value)

        
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        key = etree.Element(DataFields.Key)
        
        if self.id:
            id = etree.SubElement(key, DataFields.Id)
            id.text = self.id
        if self.api_key:
            api_key = etree.SubElement(key, DataFields.Api_Key)
            api_key.text = self.api_key
        if self.label:
            label = etree.SubElement(key, DataFields.Label)
            label.text = self.label
        if self.permissions:
            permissions = etree.SubElement(key, DataFields.Permissions)
            permission = etree.SubElement(permissions, DataFields.Permission)
            access_methods = etree.SubElement(permissions, DataFields.Access_Methods)
            for p in self.permissions:
                 access_method = etree.SubElement(access_methods, DataFields.Access_Method)
                 access_method.text = p
                 
        return key


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """

        key = element.find(DataFields.Key)
        if key is not None:
            id = key.find(DataFields.Id)
            if id is not None:
                self.id = id.text
            api_key = key.find(DataFields.Api_Key)
            if api_key is not None:
                self.api_key = api_key.text                
            label = key.find(DataFields.Label)
            if label is not None:
                self.label = label.text
            permissions = key.find(DataFields.Permissions)
            if permissions is not None:
                permission = permissions.find(DataFields.Permission)
                if permisison is not None:
                    access_methods = permission.find(DataFields.Access_Methods)
                    if access_methods is not None:
                        self.permissions = []
                        for access_method in access_methods.findall(DataFields.Access_Method):
                            self.permissions.append(access_method.text) 


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))                            


class KeyList(DataStructure):
    """ Models a API key list item """
    
    def __init__(self, **kwargs):

        self.keys = []

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        keysDict = dict()
        keyList = []
        for key in self.keys:
            keyList.append(key.toDict())
        keysDict[DataFields.Keys] = keyList
        return keysDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        keysList = inDict.get(DataFields.Keys, None)
        if keysList is not None:
            self.keys = []
            for keyDict in keysList:
                key = Key(**keyDict)
                self.keys.append(key)

        
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        keys = etree.Element(DataFields.Keys)
        for key in self.keys:
            keys.append(key.toXml())
                 
        return keys


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """

        keys = element.find(DataFields.Keys)
        if keys is not None:
            self.keys = []
            for key_element in keys.findall(DataFields.Key):
                key = Key()
                key.fromXml(key_element)
                self.keys.append(key)


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))
            
            

class User(DataStructure):
    """ Models a User item """

    
    def __init__(self, **kwargs):
        self._attributes = [DataFields.About,
                            DataFields.Api_Key,
                            DataFields.Creatable_Roles,
                            DataFields.Datastreams_Allowed,
                            DataFields.Datastreams_Count,
                            DataFields.Deliver_Email,
                            DataFields.Display_Activity,
                            DataFields.Display_Information,
                            DataFields.Display_Stats,
                            DataFields.Email,
                            DataFields.First_Name,
                            DataFields.Full_Name,
                            DataFields.Last_Name,
                            DataFields.Login,
                            DataFields.Organisation,
                            DataFields.Receive_Forum_Notifications,
                            DataFields.Roles,
                            DataFields.Subscribed_To_Mailings,
                            DataFields.Timezone,
                            DataFields.Total_Api_Access_Count,
                            DataFields.Website]
        
        self.about = None
        self.api_key = None
        self.creatable_roles = None
        self.datastreams_allowed = None
        self.datastreams_count = None
        self.deliver_email = None
        self.display_activity = None
        self.display_information = None
        self.display_stats = None
        self.email = None
        self.first_name = None
        self.full_name = None
        self.last_name = None
        self.login = None
        self.organisation = None
        self.receive_forum_notifications = None
        self.roles = None
        self.subscribed_to_mailing = None
        self.timezone = None
        self.website = None

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        userDict = dict()
        for attribute in self._attributes:
            attribute_value = getattr(self, attribute, None)
            if attribute_value:
                userDict[attribute] = attribute_value
        
        topDict = dict()
        topDict[DataFields.User] = userDict
        return topDict
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        userDict = inDict.get(DataFields.User, None)
        if userDict:
            for attribute in self._attributes:
                attribute_value = userDict.get(attribute, None)
                if attribute_value:
                    setattr(self, attribute, attribute_value)

        
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        user = etree.Element(DataFields.User)

        if self.about:
            about = etree.SubElement(user, DataFields.About)
            about.text = self.about
        if self.api_key:
            api_key = etree.SubElement(user, DataFields.Api_Key)
            api_key.text = self.api_key
        if self.creatable_roles:
            creatable_roles = etree.SubElement(user, DataFields.Creatable_Roles)
            for role_text in self.creatable_roles:
                creatable_role = etree.SubElement(creatable_roles, DataFields.Creatable_Role)
                creatable_role.text = role_text
        if self.datastreams_allowed:
            datastreams_allowed = etree.SubElement(user, DataFields.Datastreams_Allowed)
            datastreams_allowed.text = str(self.datastreams_allowed)
        if self.datastreams_count:
            datastreams_count = etree.SubElement(user, DataFields.Datastreams_Count)
            datastreams_count.text = str(self.datastreams_count)
        if self.deliver_email:
            deliver_email = etree.SubElement(user, DataFields.Deliver_Email)
            deliver_email.text = self.deliver_email
        if self.display_activity:
            display_activity = etree.SubElement(user, DataFields.Display_Activity)
            display_activity.text = self.display_activity
        if self.display_information:
            display_information = etree.SubElement(user, DataFields.Display_Information)
            display_information.text = self.display_information            
        if self.display_stats:
            display_stats = etree.SubElement(user, DataFields.Display_Stats)
            display_stats.text = self.display_stats 
        if self.email:
            email = etree.SubElement(user, DataFields.Email)
            email.text = self.email 
        if self.first_name:
            first_name = etree.SubElement(user, DataFields.First_Name)
            first_name.text = self.first_name 
        if self.full_name:
            full_name = etree.SubElement(user, DataFields.Full_Name)
            full_name.text = self.full_name 
        if self.about:
            about = etree.SubElement(user, DataFields.About)
            about.text = self.about             
        if self.last_name:
            last_name = etree.SubElement(user, DataFields.Last_Name)
            last_name.text = self.last_name 
        if self.login:
            login = etree.SubElement(user, DataFields.Login)
            login.text = self.login 
        if self.organisation:
            organisation = etree.SubElement(user, DataFields.Organisation)
            organisation.text = self.organisation 
        if self.receive_forum_notifications:
            receive_forum_notifications = etree.SubElement(user, DataFields.Receive_Forum_Notifications)
            receive_forum_notifications.text = self.receive_forum_notifications 
        if self.roles:
            roles = etree.SubElement(user, DataFields.Roles)
            for role_text in self.roles:
                role = etree.SubElement(roles, DataFields.Role)
                role.text = role_text
        if self.subscribed_to_mailing:
            subscribed_to_mailing = etree.SubElement(user, DataFields.Subscribed_To_Mailings)
            subscribed_to_mailing.text = self.subscribed_to_mailing                 
        if self.timezone:
            timezone = etree.SubElement(user, DataFields.Timezone)
            timezone.text = self.timezone 
        if self.website:
            website = etree.SubElement(user, DataFields.Website)
            website.text = self.website 

        return user


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """

        user = element.find(DataFields.User)
        if user is not None:
            about = user.find(DataFields.About)
            if about is not None:
                self.about = about.text
            api_key = user.find(DataFields.Api_Key)
            if api_key is not None:
                self.api_key = api_key.text
            creatable_roles = user.find(DataFields.Creatable_Roles)
            if creatable_roles is not None:
                self.creatable_roles = []
                for creatable_role in creatable_roles.findall(DataFields.Creatable_Role):
                    self.creatable_roles.append(creatable_role.text)
            datastreams_allowed = user.find(DataFields.Datastreams_Allowed)
            if datastreams_allowed is not None:
                self.datastreams_allowed = datastreams_allowed.text                
            datastreams_count = user.find(DataFields.Datastreams_Count)
            if datastreams_count is not None:
                self.datastreams_count = datastreams_count.text                
            deliver_email = user.find(DataFields.Deliver_Email)
            if deliver_email is not None:
                self.deliver_email = deliver_email.text                
            display_activity = user.find(DataFields.Display_Activity)
            if display_activity is not None:
                self.display_activity = display_activity.text
            display_information = user.find(DataFields.Display_Information)
            if display_information is not None:
                self.display_information = display_information.text                
            display_stats = user.find(DataFields.Display_Stats)
            if display_stats is not None:
                self.display_stats = display_stats.text
            email = user.find(DataFields.Email)
            if email is not None:
                self.email = email.text
            first_name = user.find(DataFields.First_Name)
            if first_name is not None:
                self.first_name = first_name.text
            full_name = user.find(DataFields.Full_Name)
            if full_name is not None:
                self.full_name = full_name.text
            last_name = user.find(DataFields.Last_Name)
            if last_name is not None:
                self.last_name = last_name.text
            login = user.find(DataFields.Login)
            if login is not None:
                self.login = login.text                                
            organisation = user.find(DataFields.Organization)
            if organisation is not None:
                self.organisation = organisation.text
            receive_forum_notifications = user.find(DataFields.Receive_Forum_Notifications)
            if receive_forum_notifications is not None:
                self.receive_forum_notifications = receive_forum_notifications.text
            roles = user.find(DataFields.Roles)
            if roles is not None:
                self.roles = []
                for role in roles.findall(DataFields.Role):
                    self.roles.append(role.text)
            subscribed_to_mailing = user.find(DataFields.Subscribed_To_Mailings)
            if subscribed_to_mailing is not None:
                self.subscribed_to_mailing = subscribed_to_mailing.text
            timezone = user.find(DataFields.Timezone)
            if timezone is not None:
                self.timezone = timezone.text
            website = user.find(DataFields.Website)
            if website is not None:
                self.website = website.text 


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            inDict = json.loads(data)
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))                            


    
class UserList(DataStructure):
    """ Models a User list item """
    
    def __init__(self, **kwargs):

        self.users = []

        # initialise attributes to specified values or None.
        self.fromDict(kwargs)
        

    def toDict(self):
        """ 
        Return the data structure object as a dict. This method is used as 
        a helper function for JSON serialization/deserialization.
        """
        # this item is actually a list
        usersList = list()
        for user in self.users:
            usersList.append(user.toDict())
        return usersList
    
    
    def fromDict(self, inDict):
        """
        Populate attributes from a dict
        """
        # The json structure of this object is actually a list. To allow
        # this object to be initialised and decoded, the list is wrapped
        # in a dict with a key identical to the XML verison which is
        # DataFields.Users.
        # Remove the wrapper dict to access triggers list
        usersList = inDict[DataFields.Users]
        if usersList:
            self.users = []
            for userDict in usersList:
                user = User(**userDict)
                self.users.append(user)

        
    def toXml(self, parent=None):
        """ 
        Return the object as an xml ElementTree 
        
        @param parent: The parent element
        @type parent: etree.Element
        
        @return: XML representation of the object
        @rtype: etree.Element
        """
        users = etree.Element(DataFields.Keys)
        users.attrib['type'] = 'array'
        for user in self.users:
            users.append(user.toXml())
        return users


    def fromXml(self, element):
        """
        Populate attributes from a XML etree
        
        @param xml: an xml element tree
        @type xml: etree.Element
        """

        users = element.find(DataFields.Users)
        if users is not None:
            self.users = []
            for user_element in users.findall(DataFields.User):
                user = User()
                user.fromXml(user_element)
                self.users.append(user)


    def encode(self, format=DataFormats.JSON):
        """ 
        Return a string representation of the object encoded in the specified format
        """
        if format == DataFormats.JSON:
            return json.dumps(self.toDict())
        
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers
            return etree.tostring(self.toXml(), 'utf-8')            

        else:
            raise Exception("Don't know how to encode %s using format %s" % (self.__class__.__name__,
                                                                             format))


    def decode(self, data, format=DataFormats.JSON):
        """ 
        Decode data, in the specified format, into local attributes
        """ 
        if format == DataFormats.JSON:
            # The json structure of this object is actually a list.
            # wrap it in a dict for a consistent input to fromDict
            inDict = {DataFields.Users : json.loads(data)}
            self.fromDict(inDict)
                    
        elif format == DataFormats.XML:
            # This XML structure is not wrapped in EEML headers 
            element = etree.fromstring(data)
            if element is not None:
                self.fromXml(element)

        else:
            raise Exception("Don't know how to decode %s using format %s" % (self.__class__.__name__,
                                                                             format))

    
    
################################################################################

# Define a mapping of data structure label to object that
# can be used to resolve the appropriate data structure
# to create when parsing response data from Pachube.
List_Feeds_Msg = 'feeds_list'
View_Feed_Msg = 'feed'
View_Datastream_Msg = 'datastream'
View_Datapoint_Msg = 'datapoint'
List_Keys_Msg = 'keys_list'
View_Key_Msg = 'key'
List_Triggers_Msg = 'triggers_list'
View_Trigger_Msg = 'trigger'
List_Users_Msg = 'users_list'
View_User_Msg = 'user'
StructuresMap = {List_Feeds_Msg : EnvironmentList,
                 View_Feed_Msg : Environment,
                 View_Datastream_Msg : Datastream,
                 View_Datapoint_Msg : Datapoint,
                 List_Keys_Msg : KeyList,
                 View_Key_Msg : Key,
                 List_Triggers_Msg : TriggerList,
                 View_Trigger_Msg : Trigger,
                 List_Users_Msg : UserList,
                 View_User_Msg : User}


def getDataStructure(msg_kind):
    if msg_kind not in StructuresMap:
        err_str = "Invalid structure \'%s\', can't convert" % structure
        logging.error(err_str)
        raise Exception(err_str)
    return StructuresMap[msg_kind]
    