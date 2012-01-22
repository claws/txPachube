#!/usr/bin/env python

try:
    from xml.etree import cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
import json
import unittest
try:
    import txpachube
except ImportError:
    # cater for situation where txpachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import txpachube



# Test data obtained from the Pachube API documentation page.

TEST_FEEDS_LIST_JSON = """{
  "totalResults":4299,
  "results":[
    {
      "feed":"http://api.pachube.com/v2/feeds/5853.json",
      "title":"bridge19",
      "status":"live",
      "version":"1.0.0",
      "creator":"God",
      "url":"http://www.pachube.com/users/hdr",
      "location":{"domain":"physical"},
      "tags":["Tag1", "Tag2"],
      "datastreams":[
        {
          "max_value":"10000.0",
          "tags":["humidity"],
          "current_value":"435",
          "min_value":"-10.0",
          "at":"2010-07-02T10:21:57.101496Z",
          "id":"0"
        },
        {
          "max_value":"10000.0",
          "tags":["humidity"],
          "current_value":"hertz",
          "min_value":"-10.0",
          "at":"2010-07-02T10:21:57.176209Z",
          "id":"1"
        }
      ]
    }
  ]
}"""

TEST_FEEDS_LIST_XML = """<eeml xmlns="http://www.eeml.org/xsd/0.5.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" version="0.5.1" xsi:schemaLocation="http://www.eeml.org/xsd/0.5.1 http://www.eeml.org/xsd/0.5.1/0.5.1.xsd">
  <opensearch:totalResults>4299</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>50</opensearch:itemsPerPage>
  <environment updated="2010-06-08T09:30:21Z" id="5853" creator="http://www.pachube.com/users/hdr">
    <title>bridge19</title>
    <feed>http://api.pachube.com/v2/feeds/5853.xml</feed>
    <status>live</status>
    <tag>Tag1</tag>
    <tag>Tag2</tag>
    <location domain="physical">
      <lat/>
      <lon/>
    </location>
    <data id="0">
      <tag>watts</tag>
      <min_value>0.0</min_value>
      <max_value>4355.0</max_value>
      <current_value at="2010-06-30T13:36:34.830647Z">126</current_value>
    </data>
  </environment>
  ...
</eeml>"""


TEST_FEED_JSON = """{
"description" : "test of manual feed snapshotting",
"feed" : "http://api.pachube.com/v2/feeds/504.json",
"icon" : "http://www.haque.co.uk/favicon.png",
"id" : 7021,
"status" : "frozen",
"title" : "Pachube Office environment",
"website":"http://www.haque.co.uk/",
"updated" : "2010-06-25T11:54:17.463771Z",
"version" : "1.0.0",
"creator" : "http://www.pachube.com/users/hdr",
"private" : "False",
"tags":[
    "Tag1",
    "Tag2"
],
"location":
{
  "disposition":"fixed",
  "ele":"23.0",
  "name":"office",
  "lat":51.5235375648154,
  "exposure":"indoor",
  "lon":-0.0807666778564453,
  "domain":"physical"
},
"datastreams" : [ {
  "at" : "2010-06-25T11:54:17.454020Z",
  "current_value" : "999",
  "id" : "3",
  "max_value" : "999.0",
  "min_value" : "7.0"
  },
  {
  "at" : "2010-06-24T10:05:49.000000Z",
  "current_value" : "0000017",
  "id" : "4",
  "max_value" : "19.0",
  "min_value" : "7.0"
  } ]
}"""

TEST_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<eeml xmlns="http://www.eeml.org/xsd/0.5.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.5.1" xsi:schemaLocation="http://www.eeml.org/xsd/0.5.1 http://www.eeml.org/xsd/0.5.1/0.5.1.xsd">
  <environment updated="2010-06-08T09:30:11Z" id="504" creator="http://www.pachube.com/users/hdr">
    <title>Pachube Office environment</title>
    <feed>http://api.pachube.com/v2/feeds/504.xml</feed>
    <status>live</status>
    <website>http://www.haque.co.uk/</website>
    <private>false</private>
    <tag>Tag1</tag>
    <tag>Tag2</tag>
    <location domain="physical" exposure="indoor" disposition="fixed">
      <name>office</name>
      <lat>51.5235375648154</lat>
      <lon>-0.0807666778564453</lon>
      <ele>23.0</ele>
    </location>
    <data id="0">
      <tag>humidity</tag>
      <current_value at="2010-06-08T09:30:11.000000Z">311</current_value>
      <max_value>847.0</max_value>
      <min_value>0.0</min_value>
      <unit type="basicSI" symbol="symbol">label</unit>
      <datapoints>
        <value at="2009-07-05T09:24:03.339244Z">008</value>
        <value at="2009-07-05T09:24:03.339244Z">546</value>
        <value at="2009-07-05T09:24:03.339244Z">123</value>
      </datapoints>
    </data>
  </environment>
</eeml>"""


TEST_DATASTREAM_JSON = """{
  "current_value":"100",
  "max_value":"10000.0",
  "at":"2010-07-02T10:16:19.270708Z",
  "min_value":"-10.0",
  "tags":[
    "humidity"
  ],
  "id":"1"
}"""

TEST_DATASTREAM_XML = """<eeml xmlns="http://www.eeml.org/xsd/0.5.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.5.1" xsi:schemaLocation="http://www.eeml.org/xsd/0.5.1 http://www.eeml.org/xsd/0.5.1/0.5.1.xsd">
  <environment updated="2010-07-05T08:48:27.961661Z" id="2789" creator="http://www.pachube.com">
    <data id="1">
      <tag>humidity</tag>
      <current_value at="2010-07-02T10:16:19.270708Z">100</current_value>
      <max_value>10000.0</max_value>
      <min_value>-10.0</min_value>
    </data>
  </environment>
</eeml>"""


TEST_DATAPOINT_JSON = """{
  "value":"297",
  "at":"2010-05-20T11:01:46.000000Z"
}"""

TEST_DATAPOINT_XML = """<eeml xmlns="http://www.eeml.org/xsd/0.5.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.5.1" xsi:schemaLocation="http://www.eeml.org/xsd/0.5.1 http://www.eeml.org/xsd/0.5.1/0.5.1.xsd">
  <environment>
    <data>
      <datapoints>
        <value at="2010-05-20T11:01:46.000000Z">444</value>
      </datapoints>
    </data>
  </environment>
</eeml>"""


TEST_TRIGGER_JSON = """{
  "threshold_value":"15.0",
  "user":"pachube",
  "notified_at":"",
  "url":"http:\/\/www.postbin.org\/1ijyltn",
  "trigger_type":"lt",
  "id":14,
  "environment_id":8470,
  "stream_id":"0"
}"""

TEST_TRIGGER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<datastream-trigger>
  <id type="integer">14</id>
  <url>http:\/\/www.postbin.org/1ijyltn</url>
  <trigger-type>lt</trigger-type>
  <threshold-value type="float">15.0</threshold-value>
  <notified-at type="datetime">a date time string</notified-at>
  <user>pachube</user>
  <environment-id type="integer">1233</environment-id>
  <stream-id>0</stream-id>
</datastream-trigger>"""

TEST_TRIGGERS_LIST_JSON = """[
  {
    "trigger_type":"gt",
    "stream_id":"0",
    "url":"http:\/\/www.postbin.org\/1ijyltn",
    "environment_id":1233,
    "user":"pachube",
    "threshold_value":"20.0",
    "notified_at":"",
    "id":13
  }
  ,
  {
    "trigger_type":"lt",
    "stream_id":"0",
    "url":"http:\/\/www.postbin.org\/1ijyltn",
    "environment_id":1233,
    "user":"pachube",
    "threshold_value":"15.0",
    "notified_at":"",
    "id":14
  }
]"""

TEST_TRIGGERS_LIST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<datastream-triggers type="array">
  <datastream-trigger>
    <id type="integer">13</id>
    <url>http://www.postbin.org/1ijyltn</url>
    <trigger-type>gt</trigger-type>
    <threshold-value type="float">20.0</threshold-value>
    <notified-at type="datetime"></notified-at>
    <user>pachube</user>
    <environment-id type="integer">1233</environment-id>
    <stream-id>0</stream-id>
  </datastream-trigger>
  <datastream-trigger>
    <id type="integer">14</id>
    <url>http://www.postbin.org/1ijyltn</url>
    <trigger-type>lt</trigger-type>
    <threshold-value type="float">15.0</threshold-value>
    <notified-at type="datetime"></notified-at>
    <user>pachube</user>
    <environment-id type="integer">1233</environment-id>
    <stream-id>0</stream-id>
  </datastream-trigger>
</datastream-triggers>"""

TEST_API_KEY_JSON = """{
  "key":{
    "id":"1j2s8agjgksdjg",
    "api_key":"CeWzga_cNja15kjwSVN5x5Mut46qj5akqKPvFxKIec0",
    "label":"sharing key",
    "permissions":[
      {
        "access_methods":["get","put"]
      }
    ]
  }
}"""

TEST_API_KEY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<key>
  <id>1j2s8agjgksdjg</id>
  <api-key>1nAYR5W8jUqiZJXIMwu3923Qfuq_lnFCDOKtf3kyw4g</api-key>
  <label>sharing key</label>
  <permissions>
    <permission>
      <access-methods>
        <access-method>get</access-method>
        <access-method>put</access-method>
      </access-methods>
    </permission>
  </permissions>
</key>"""

TEST_API_KEYS_LIST_JSON = """{"keys":[
  {"key":{"id":"1j2s8agjgksdjg",
          "api_key":"CeWzga_cNja15kjwSVN5x5Mut46qj5akqKPvFxKIec0",
          "label": "sharing key 1",
          "permissions":[{"access_methods":["get"]}]
          }
  },
  {"key":{"id":"a9g8ajkdskjgd",
          "api_key":"zR9eEw3WfrSY1-abcdefghasdfaoisdj109usasdf0a9sf",
          "label": "sharing key 2",
          "permissions":[{"access_methods":["put"],
                          "source_ip":"123.12.123.123"}]}
  }
]}"""


TEST_API_KEYS_LIST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<keys>
  <key>
    <id>1j2s8agjgksdjg</id>
    <api-key>CeWzga_cNja15kjwSVN5x5Mut46qj5akqKPvFxKIec0</api-key>
    <label>sharing key 1</label>
    <permissions>
      <permission>
        <access-methods>
          <access-method>get</access-method>
        </access-methods>
      </permission>
    </permissions>
  </key>
  <key>
    <id>a9g8ajkdskjgd</id>
    <api-key>zR9eEw3WfrSY1-abcdefghasdfaoisdj109usasdf0a9sf</api-key>
    <label>sharing key 2</label>
    <permissions>
      <permission>
        <access-methods>
          <access-method>put</access-method>
        </access-methods>
        <source-ip>123.12.123.123</source-ip>
      </permission>
    </permissions>
  </key>
</keys>"""


TEST_USER_JSON = """{
  "user":{
    "api_key":"0000000000000000000000000000000000000000000000000000000000006002",
    "full_name":"full name",
    "login":"login2",
    "email":"20e13d578b8e@example.com",
    "roles":["default", "my_users"],
    "about":"user bio",
    "deliver_email":false,
    "display_activity":false,
    "display_information":false,
    "display_stats":false,
    "organisation":"Organisation Name",
    "receive_forum_notifications":true,
    "creatable_roles":[],
    "subscribed_to_mailings":true,
    "time_zone":"London",
    "website":"http://website.com"
  }
}"""

TEST_USER_XML = """<user>
  <about>user bio</about>
  <api_key>0000000000000000000000000000000000000000000000000000000000006002</api_key>
  <daily_api_access_count>103</daily_api_access_count>
  <deliver_email>true</deliver_email>
  <display_activity>false</display_activity>
  <display_information>true</display_information>
  <display_stats>false</display_stats>
  <email>20e13d578b8e@example.com</email>
  <full_name>a full name</full_name>
  <last_name>last</last_name>
  <login>login2</login>
  <organisation>Organisation</organisation>
  <time_zone>(GMT+00:00) UTC</time_zone>
  <total_api_access_count>123559</total_api_access_count>
  <website>http://example.com</website>
  <feeds_count>3</feeds_count>
  <datastreams_count>16</datastreams_count>
  <datastreams_allowed>135</datastreams_allowed>
  <subscribed_to_mailings>true</subscribed_to_mailings>
  <receive_forum_notifications>true</receive_forum_notifications>
  <roles>
    <role>default</role>
    <role>my_users</role>
  </roles>
  <creatable_roles>
    <role>device</role>
  </creatable_roles>
</user>"""


TEST_USERS_LIST_JSON = """[
  {
    "user":{
      "api_key":"0000000000000000000000000000000000000000000000000000000000006016",
      "full_name":"full name",
      "login":"login1",
      "email":"f28613747df7@example.com",
      "roles":["default", "my_users"],
      "about":"about",
      "deliver_email":false,
      "display_activity":false,
      "display_information":false,
      "display_stats":false,
      "organisation":"Organisation Name",
      "receive_forum_notifications":true,
      "creatable_roles":["device"],
      "subscribed_to_mailings":true,
      "time_zone":"Arizona",
      "website":"http://website.com"
    }
  },
  {
    "user":{
      "api_key":"0000000000000000000000000000000000000000000000000000000000006002",
      "full_name":"full name",
      "login":"login2",
      "email":"s9ud8jdkfd8g@example.com",
      "roles":["basic"],
      "about":"",
      "deliver_email":false,
      "display_activity":false,
      "display_information":false,
      "display_stats":false,
      "organisation":"Organisation Name",
      "receive_forum_notifications":true,
      "creatable_roles":[],
      "subscribed_to_mailings":true,
      "time_zone":"London",
      "website":"http://website.com"
    }
  }
]
"""

TEST_USERS_LIST_XML = """<users type="array">
  <user>
    <api_key>0000000000000000000000000000000000000000000000000000000000006016</api_key>
    <email>f28613747df7@example.com</email>
    <full_name>full name</full_name>
    <login>login1</login>
    <roles>
      <role>default</role>
      <role>my_users</role>
    </roles>
  </user>
  <user>
    <api_key>0000000000000000000000000000000000000000000000000000000000006002</api_key>
    <email>20e13d578b8e@example.com</email>
    <full_name>full name</full_name>
    <login>login2</login>
    <roles>
      <role>my_users</role>
    </roles>
  </user>
</users>"""




class DataStructureTestCase(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_Initialisation(self):
        """ Check data structure initialisation """
        
        # test no arguments
        
        unit = txpachube.Unit()
        location = txpachube.Location()
        datapoint = txpachube.Datapoint()
        datastream = txpachube.Datastream()
        environment = txpachube.Environment()
        environment_list = txpachube.EnvironmentList()
        trigger = txpachube.Trigger()
        trigger_list = txpachube.TriggerList()
        key = txpachube.Key()
        key_list = txpachube.KeyList()
        user = txpachube.User()
        user_list = txpachube.UserList()
       
        
        # test expected keyword arguments
        
        unit_kwargs = {txpachube.DataFields.Label : 'Celcius',
                       txpachube.DataFields.Type : txpachube.Unit.Basic_Si,
                       txpachube.DataFields.Symbol : "C"}
        unit = txpachube.Unit(**unit_kwargs)
        self.assertEqual(unit.label, unit_kwargs[txpachube.DataFields.Label], "Unit label mismatch")
        self.assertEqual(unit.type, unit_kwargs[txpachube.DataFields.Type], "Unit type mismatch")
        self.assertEqual(unit.symbol, unit_kwargs[txpachube.DataFields.Symbol], "Unit symbol mismatch")


        location_kwargs = {txpachube.DataFields.Disposition : txpachube.Location.Fixed,
                           txpachube.DataFields.Domain : txpachube.Location.Physical,
                           txpachube.DataFields.Elevation : "40",
                           txpachube.DataFields.Exposure : txpachube.Location.Indoor,
                           txpachube.DataFields.Latitude : 51.5235375648154,
                           txpachube.DataFields.Longitude : -0.0807666778564453,
                           txpachube.DataFields.Name : 'temp'}
        location = txpachube.Location(**location_kwargs)
        self.assertEqual(location.disposition, location_kwargs[txpachube.DataFields.Disposition], "Location disposition mismatch")
        self.assertEqual(location.domain, location_kwargs[txpachube.DataFields.Domain], "Location domain mismatch")
        self.assertEqual(location.exposure, location_kwargs[txpachube.DataFields.Exposure], "Location exposure mismatch")
        self.assertEqual(location.ele, location_kwargs[txpachube.DataFields.Elevation], "Location elevation mismatch")
        self.assertEqual(location.lat, location_kwargs[txpachube.DataFields.Latitude], "Location latitude mismatch")
        self.assertEqual(location.lon, location_kwargs[txpachube.DataFields.Longitude], "Location longitude mismatch")
        self.assertEqual(location.name, location_kwargs[txpachube.DataFields.Name], "Location name mismatch")

        
        datapoint_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:51.133782Z", 
                            txpachube.DataFields.Value : "999"}
        datapoint = txpachube.Datapoint(**datapoint_kwargs)
        self.assertEqual(datapoint.at, datapoint_kwargs[txpachube.DataFields.At], "Datapoint at mismatch")
        self.assertEqual(datapoint.value, datapoint_kwargs[txpachube.DataFields.Value], "Datapoint value mismatch")
        

        datastream_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:52.133782Z",
                             txpachube.DataFields.Current_Value : "27.0",
                             txpachube.DataFields.Datapoints : [datapoint_kwargs],
                             txpachube.DataFields.Id : 7021,
                             txpachube.DataFields.Maximum_Value : "35.8",
                             txpachube.DataFields.Minimum_Value : "15.9",
                             txpachube.DataFields.Tags : ['temp', 'Temperature', 'C'],
                             txpachube.DataFields.Unit : unit_kwargs,
                             txpachube.DataFields.Updated : "2010-04-12T11:31:51.133782Z"}
        datastream = txpachube.Datastream(**datastream_kwargs)
        self.assertEqual(datastream.at, datastream_kwargs[txpachube.DataFields.At], "Datastream at mismatch")
        self.assertEqual(datastream.current_value, datastream_kwargs[txpachube.DataFields.Current_Value], "Datastream current value mismatch")
        
        self.assertEqual(len(datastream.datapoints), len(datastream_kwargs[txpachube.DataFields.Datapoints]), "Datastream datapoints count mismatch")
        self.assertEqual(datastream.datapoints[0].at, datastream_kwargs[txpachube.DataFields.Datapoints][0][txpachube.DataFields.At], "Datastream datapoints at mismatch")
        self.assertEqual(datastream.datapoints[0].value, datastream_kwargs[txpachube.DataFields.Datapoints][0][txpachube.DataFields.Value], "Datastream datapoints value mismatch")
        
        self.assertEqual(datastream.id, datastream_kwargs[txpachube.DataFields.Id], "Datastream id mismatch")
        self.assertEqual(datastream.max_value, datastream_kwargs[txpachube.DataFields.Maximum_Value], "Datastream maimum value mismatch")
        self.assertEqual(datastream.min_value, datastream_kwargs[txpachube.DataFields.Minimum_Value], "Datastream minimum value mismatch")
        
        self.assertEqual(datastream.unit.label, datastream_kwargs[txpachube.DataFields.Unit][txpachube.DataFields.Label], "Datastream Unit label mismatch")
        self.assertEqual(datastream.unit.type, datastream_kwargs[txpachube.DataFields.Unit][txpachube.DataFields.Type], "Datastream Unit type mismatch")
        self.assertEqual(datastream.unit.symbol, datastream_kwargs[txpachube.DataFields.Unit][txpachube.DataFields.Symbol], "Datastream Unit symbol mismatch")
        
        self.assertEqual(datastream.updated, datastream_kwargs[txpachube.DataFields.Updated], "Datastream updated mismatch")
        
        
        
        env_inDict = json.loads(TEST_FEED_JSON)
        environment = txpachube.Environment(**env_inDict)
        self.assertEqual(environment.creator, env_inDict[txpachube.DataFields.Creator], "Environment creator mismatch")
        
        self.assertEqual(len(environment.datastreams), len(env_inDict[txpachube.DataFields.Datastreams]), "Environment datastreams count mismatch")
        datastream_01 = env_inDict[txpachube.DataFields.Datastreams][0]
        datastream_01_key = datastream_01[txpachube.DataFields.Id]
        environment_datastream_01 = environment.datastreams[datastream_01_key]
        self.assertEqual(environment_datastream_01.at, datastream_01[txpachube.DataFields.At], "Environment datastreams[0].at mismatch")
        self.assertEqual(environment_datastream_01.current_value, datastream_01[txpachube.DataFields.Current_Value], "Environment datastreams[0].value mismatch")
        self.assertEqual(environment_datastream_01.id, datastream_01[txpachube.DataFields.Id], "Environment datastreams[0].id mismatch")
        self.assertEqual(environment_datastream_01.max_value, datastream_01[txpachube.DataFields.Maximum_Value], "Environment datastreams[0].max_value mismatch")
        self.assertEqual(environment_datastream_01.min_value, datastream_01[txpachube.DataFields.Minimum_Value], "Environment datastreams[0].min_value mismatch")
        datastream_02 = env_inDict[txpachube.DataFields.Datastreams][1]
        datastream_02_key = datastream_02[txpachube.DataFields.Id]
        environment_datastream_02 = environment.datastreams[datastream_02_key]
        self.assertEqual(environment_datastream_02.at, datastream_02[txpachube.DataFields.At], "Environment datastreams[1].at mismatch")
        self.assertEqual(environment_datastream_02.current_value, datastream_02[txpachube.DataFields.Current_Value], "Environment datastreams[1].value mismatch")
        self.assertEqual(environment_datastream_02.id, datastream_02[txpachube.DataFields.Id], "Environment datastreams[1].id mismatch")
        self.assertEqual(environment_datastream_02.max_value, datastream_02[txpachube.DataFields.Maximum_Value], "Environment datastreams[1].max_value mismatch")
        self.assertEqual(environment_datastream_02.min_value, datastream_02[txpachube.DataFields.Minimum_Value], "Environment datastreams[1].min_value mismatch")
        
        self.assertEqual(environment.description, env_inDict[txpachube.DataFields.Description], "Environment description mismatch")
        self.assertEqual(environment.feed, env_inDict[txpachube.DataFields.Feed], "Environment feed mismatch")
        self.assertEqual(environment.icon, env_inDict[txpachube.DataFields.Icon], "Environment icon mismatch")
        self.assertEqual(environment.id, env_inDict[txpachube.DataFields.Id], "Environment id mismatch")

        self.assertEqual(environment.location.disposition, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Disposition], "Environment Location disposition mismatch")
        self.assertEqual(environment.location.domain, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Domain], "Environment Location domain mismatch")
        self.assertEqual(environment.location.exposure, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Exposure], "Environment Location exposure mismatch")
        self.assertEqual(environment.location.ele, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Elevation], "Environment Location elevation mismatch")
        self.assertEqual(environment.location.lat, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Latitude], "Environment Location latitude mismatch")
        self.assertEqual(environment.location.lon, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Longitude], "Environment Location longitude mismatch")
        self.assertEqual(environment.location.name, env_inDict[txpachube.DataFields.Location][txpachube.DataFields.Name], "Environment Location name mismatch")        
        
        self.assertEqual(environment.private, env_inDict[txpachube.DataFields.Private], "Environment private mismatch")
        self.assertEqual(environment.status, env_inDict[txpachube.DataFields.Status], "Environment status mismatch")
        self.assertEqual(environment.tags, env_inDict[txpachube.DataFields.Tags], "Environment tags mismatch")
        self.assertEqual(environment.title, env_inDict[txpachube.DataFields.Title], "Environment title mismatch")
        self.assertEqual(environment.updated, env_inDict[txpachube.DataFields.Updated], "Environment updated mismatch")
        self.assertEqual(environment.version, env_inDict[txpachube.DataFields.Version], "Environment version mismatch")
        self.assertEqual(environment.website, env_inDict[txpachube.DataFields.Website], "Environment website mismatch")



        envList_inDict = json.loads(TEST_FEEDS_LIST_JSON)
        environment_list = txpachube.EnvironmentList(**envList_inDict)

        trigger_inDict = json.loads(TEST_TRIGGER_JSON)
        trigger = txpachube.Trigger(**trigger_inDict)

        trigger_list_inDict = {txpachube.DataFields.Datastream_Trigger : json.loads(TEST_TRIGGERS_LIST_JSON)}
        trigger_list = txpachube.TriggerList(**trigger_list_inDict)

        key_inDict = json.loads(TEST_API_KEY_JSON)
        key = txpachube.Key(**key_inDict)

        key_list_inDict = json.loads(TEST_API_KEYS_LIST_JSON)
        key_list = txpachube.KeyList(**key_list_inDict)

        user_inDict = json.loads(TEST_USER_JSON)
        user = txpachube.User(**user_inDict)

        user_list_inDict = {txpachube.DataFields.Users : json.loads(TEST_USERS_LIST_JSON)}
        user_list = txpachube.UserList(**user_list_inDict)


    def test_DecodeFromJson(self):
        """ Check decode from JSON format """
        # Unit is only ever part of another structure, never alone.
        # No need to explicitly test if Unit can be decoded from JSON

        # Location is only ever part of another structure, never alone.
        # No need to explicitly test if Unit can be decoded from JSON

        datapoint = txpachube.Datapoint()
        datapoint.decode(TEST_DATAPOINT_JSON, format=txpachube.DataFormats.JSON)
        
        datastream = txpachube.Datastream()
        datastream.decode(TEST_DATASTREAM_JSON, format=txpachube.DataFormats.JSON)

        environment = txpachube.Environment()
        environment.decode(TEST_FEED_JSON, format=txpachube.DataFormats.JSON)

        environment_list = txpachube.EnvironmentList()
        environment_list.decode(TEST_FEEDS_LIST_JSON, format=txpachube.DataFormats.JSON)
        
        trigger = txpachube.Trigger()
        trigger.decode(TEST_TRIGGER_JSON, format=txpachube.DataFormats.JSON)
        
        trigger_list = txpachube.TriggerList()
        trigger_list.decode(TEST_TRIGGERS_LIST_JSON, format=txpachube.DataFormats.JSON)

        key = txpachube.Key()
        key.decode(TEST_API_KEY_JSON, format=txpachube.DataFormats.JSON) 
        
        key_list = txpachube.KeyList()
        key_list.decode(TEST_API_KEYS_LIST_JSON, format=txpachube.DataFormats.JSON)

        user = txpachube.User()
        user.decode(TEST_USER_JSON, format=txpachube.DataFormats.JSON) 
        
        user_list = txpachube.UserList()
        user_list.decode(TEST_USERS_LIST_JSON, format=txpachube.DataFormats.JSON)
         
        
               
     
    def test_DecodeFromXml(self):
        """ Check decode from XML format """
        # Unit is only ever part of another structure, never alone.
        # No need to explicitly test if Unit can be decoded from XML
        
        # Location is only ever part of another structure, never alone.
        # No need to explicitly test if Unit can be decoded from XML
        
        datapoint = txpachube.Datapoint()
        datapoint.decode(TEST_DATAPOINT_XML, format=txpachube.DataFormats.XML)

        datastream = txpachube.Datastream()
        datastream.decode(TEST_DATASTREAM_XML, format=txpachube.DataFormats.XML)

        environment = txpachube.Environment()
        environment.decode(TEST_FEED_XML, format=txpachube.DataFormats.XML)

        environment_list = txpachube.EnvironmentList()
        environment_list.decode(TEST_FEEDS_LIST_XML, format=txpachube.DataFormats.XML)

        trigger = txpachube.Trigger()
        trigger.decode(TEST_TRIGGER_XML, format=txpachube.DataFormats.XML)    

        trigger_list = txpachube.TriggerList()
        trigger_list.decode(TEST_TRIGGERS_LIST_XML, format=txpachube.DataFormats.XML) 
         
        key = txpachube.Key()
        key.decode(TEST_API_KEY_XML, format=txpachube.DataFormats.XML) 
        
        key_list = txpachube.KeyList()
        key_list.decode(TEST_API_KEYS_LIST_XML, format=txpachube.DataFormats.XML)        

        user = txpachube.User()
        user.decode(TEST_USER_XML, format=txpachube.DataFormats.XML) 
        
        user_list = txpachube.UserList()
        user_list.decode(TEST_USERS_LIST_XML, format=txpachube.DataFormats.XML) 




    def test_EncodeToJson(self):
        """ Check encode to JSON format """
        # This test performs a crude check to ensure the JSON output
        # is valid JSON. Eventually it should be expanded to confirm
        # the output content matches the values contained in local
        # attributes.
        
        unit_kwargs = {txpachube.DataFields.Label : 'Celcius',
                       txpachube.DataFields.Type : txpachube.Unit.Basic_Si,
                       txpachube.DataFields.Symbol : "C"}
        unit = txpachube.Unit(**unit_kwargs)
        json_data = unit.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)



        location_kwargs = {txpachube.DataFields.Disposition : txpachube.Location.Fixed,
                           txpachube.DataFields.Domain : txpachube.Location.Physical,
                           txpachube.DataFields.Elevation : "40",
                           txpachube.DataFields.Exposure : txpachube.Location.Indoor,
                           txpachube.DataFields.Latitude : 51.5235375648154,
                           txpachube.DataFields.Longitude : -0.0807666778564453,
                           txpachube.DataFields.Name : 'temp'}
        location = txpachube.Location(**location_kwargs)
        json_data = location.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        datapoint_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:51.133782Z", 
                            txpachube.DataFields.Value : "999"}
        datapoint = txpachube.Datapoint(**datapoint_kwargs)
        json_data = datapoint.encode(txpachube.DataFormats.JSON)



        datastream_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:52.133782Z",
                             txpachube.DataFields.Current_Value : "27.0",
                             txpachube.DataFields.Datapoints : [datapoint_kwargs],
                             txpachube.DataFields.Id : 7021,
                             txpachube.DataFields.Maximum_Value : "35.8",
                             txpachube.DataFields.Minimum_Value : "15.9",
                             txpachube.DataFields.Tags : ['temp', 'Temperature', 'C'],
                             txpachube.DataFields.Unit : unit_kwargs,
                             txpachube.DataFields.Updated : "2010-04-12T11:31:51.133782Z"}
        datastream = txpachube.Datastream(**datastream_kwargs)
        json_data = datastream.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        env_inDict = json.loads(TEST_FEED_JSON)
        environment = txpachube.Environment(**env_inDict)
        json_data = environment.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        envList_inDict = json.loads(TEST_FEEDS_LIST_JSON)
        environment_list = txpachube.EnvironmentList(**envList_inDict)
        json_data = environment_list.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        trigger_inDict = json.loads(TEST_TRIGGER_JSON)
        trigger = txpachube.Trigger(**trigger_inDict)
        json_data = trigger.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        trigger_list_inDict = {txpachube.DataFields.Datastream_Trigger : json.loads(TEST_TRIGGERS_LIST_JSON)}
        trigger_list = txpachube.TriggerList(**trigger_list_inDict)
        json_data = trigger_list.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        key_inDict = json.loads(TEST_API_KEY_JSON)
        key = txpachube.Key(**key_inDict)
        json_data = key.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        key_list_inDict = json.loads(TEST_API_KEYS_LIST_JSON)
        key_list = txpachube.KeyList(**key_list_inDict)
        json_data = key_list.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        user_inDict = json.loads(TEST_USER_JSON)
        user = txpachube.User(**user_inDict)
        json_data = user.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        user_list_inDict = {txpachube.DataFields.Users : json.loads(TEST_USERS_LIST_JSON)}
        user_list = txpachube.UserList(**user_list_inDict)        
        json_data = user_list.encode(txpachube.DataFormats.JSON)
        valid_json = json.loads(json_data)
        
        
        
    def test_EncodeToXml(self):
        """ Check encode to XML format """
        # This test performs a crude check to ensure the XML output
        # is valid XML. Eventually it should be expanded to confirm
        # the output content matches the values contained in local
        # attributes.
        
        unit_kwargs = {txpachube.DataFields.Label : 'Celcius',
                       txpachube.DataFields.Type : txpachube.Unit.Basic_Si,
                       txpachube.DataFields.Symbol : "C"}
        unit = txpachube.Unit(**unit_kwargs)
        unit_xml = unit.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(unit_xml)


        location_kwargs = {txpachube.DataFields.Disposition : txpachube.Location.Fixed,
                           txpachube.DataFields.Domain : txpachube.Location.Physical,
                           txpachube.DataFields.Elevation : "40",
                           txpachube.DataFields.Exposure : txpachube.Location.Indoor,
                           txpachube.DataFields.Latitude : 51.5235375648154,
                           txpachube.DataFields.Longitude : -0.0807666778564453,
                           txpachube.DataFields.Name : 'temp'}
        location = txpachube.Location(**location_kwargs)
        location_xml = location.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(location_xml)
        
        
        
        datapoint_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:51.133782Z", 
                            txpachube.DataFields.Value : "999"}
        datapoint = txpachube.Datapoint(**datapoint_kwargs)
        datapoint_xml = datapoint.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(datapoint_xml)



        datastream_kwargs = {txpachube.DataFields.At : "2010-04-12T11:31:52.133782Z",
                             txpachube.DataFields.Current_Value : "27.0",
                             txpachube.DataFields.Datapoints : [datapoint_kwargs],
                             txpachube.DataFields.Id : 7021,
                             txpachube.DataFields.Maximum_Value : "35.8",
                             txpachube.DataFields.Minimum_Value : "15.9",
                             txpachube.DataFields.Tags : ['temp', 'Temperature', 'C'],
                             txpachube.DataFields.Unit : unit_kwargs,
                             txpachube.DataFields.Updated : "2010-04-12T11:31:51.133782Z"}
        datastream = txpachube.Datastream(**datastream_kwargs)
        datastream_xml = datastream.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(datastream_xml)
        
        
        
        env_inDict = json.loads(TEST_FEED_JSON)
        environment = txpachube.Environment(**env_inDict)
        environment_xml = environment.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(environment_xml)
        
        
        
        envList_inDict = json.loads(TEST_FEEDS_LIST_JSON)
        environment_list = txpachube.EnvironmentList(**envList_inDict)
        environment_list_xml = environment_list.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(environment_list_xml)
        
        
        trigger_inDict = json.loads(TEST_TRIGGER_JSON)
        trigger = txpachube.Trigger(**trigger_inDict)
        trigger_xml = trigger.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(trigger_xml)
        
        
        trigger_list_inDict = {txpachube.DataFields.Datastream_Trigger : json.loads(TEST_TRIGGERS_LIST_JSON)}
        trigger_list = txpachube.TriggerList(**trigger_list_inDict)
        trigger_list_xml = trigger_list.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(trigger_list_xml)
        
        
        key_inDict = json.loads(TEST_API_KEY_JSON)
        key = txpachube.Key(**key_inDict)
        key_xml = key.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(key_xml)
        
        
        key_list_inDict = json.loads(TEST_API_KEYS_LIST_JSON)
        key_list = txpachube.KeyList(**key_list_inDict)
        key_list_xml = key_list.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(key_list_xml)
        
        
        user_inDict = json.loads(TEST_USER_JSON)
        user = txpachube.User(**user_inDict)
        user_xml = user.encode(txpachube.DataFormats.XML)
        valid_xml = etree.fromstring(user_xml)
        
        
        user_list_inDict = {txpachube.DataFields.Users : json.loads(TEST_USERS_LIST_JSON)}
        user_list = txpachube.UserList(**user_list_inDict)        
        user_list_xml = user_list.encode(txpachube.DataFormats.XML)             
        valid_xml = etree.fromstring(user_list_xml)
        
            
    def tearDown(self):
        pass
    
            
suite = unittest.TestLoader().loadTestsFromTestCase(DataStructureTestCase)

    
              
if __name__ == "__main__":

    runner = unittest.TextTestRunner()
    runner.run(suite)
    
    


    
