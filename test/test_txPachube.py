#!/usr/bin/env python

try:
    from xml.etree import cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree
from xml.dom import minidom
import re
import json

try:
    import txPachube
except ImportError:
    # cater for situation where txPachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import txPachube



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
"id" : 7021,
"status" : "frozen",
"title" : "Pachube Office environment",
"website":"http://www.haque.co.uk/",
"updated" : "2010-06-25T11:54:17.463771Z",
"version" : "1.0.0",
"creator" : "http://www.pachube.com/users/hdr",
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




def test_data_structures():
    # unit
    unit_kwargs = {txPachube.DataFields.Label : 'Celcius',
                   txPachube.DataFields.Type : txPachube.Unit.Basic_Si,
                   txPachube.DataFields.Symbol : "C"}
    test_unit = txPachube.Unit(**unit_kwargs)

    a = test_unit.toDict()
    b = test_unit.toXml()
    c = test_unit.encode(txPachube.DataFormats.JSON)
    d = test_unit.encode(txPachube.DataFormats.XML)
    # unit is only ever part of another structure, never alone.
    #test_unit.decode(XXX_JSON, format=txPachube.DataFormats.JSON)
    #test_unit.decode(XXX_XML, format=txPachube.DataFormats.XML)   


    # location
    location_kwargs = {txPachube.DataFields.Disposition : txPachube.Location.Fixed,
                       txPachube.DataFields.Domain : txPachube.Location.Physical,
                       txPachube.DataFields.Elevation : "40",
                       txPachube.DataFields.Exposure : txPachube.Location.Indoor,
                       txPachube.DataFields.Latitude : 51.5235375648154,
                       txPachube.DataFields.Longitude : -0.0807666778564453,
                       txPachube.DataFields.Name : 'temp'}
    test_location = txPachube.Location(**location_kwargs)

    a = test_location.toDict()
    b = test_location.toXml()
    c = test_location.encode(txPachube.DataFormats.JSON)
    d = test_location.encode(txPachube.DataFormats.XML)
    # location is only ever part of another structure, never alone.
    #test_location.decode(XXX_JSON, format=txPachube.DataFormats.JSON)
    #test_location.decode(XXX_XML, format=txPachube.DataFormats.XML)
    

    # datapoint
    datapoint_kwargs = {txPachube.DataFields.At : "2010-04-12T11:31:51.133782Z", 
                        txPachube.DataFields.Value : "999"}
    test_datapoint = txPachube.Datapoint(**datapoint_kwargs)
    
    a = test_datapoint.toDict()
    b = test_datapoint.toXml()
    c = test_datapoint.encode(txPachube.DataFormats.JSON)
    d = test_datapoint.encode(txPachube.DataFormats.XML)
    test_datapoint.decode(TEST_DATAPOINT_JSON, format=txPachube.DataFormats.JSON)
    test_datapoint.decode(TEST_DATAPOINT_XML, format=txPachube.DataFormats.XML)
    

    # datastream
    datastream_kwargs = {txPachube.DataFields.At : "2010-04-12T11:31:52.133782Z",
                         txPachube.DataFields.Current_Value : "27.0",
                         txPachube.DataFields.Datapoints : [datapoint_kwargs],
                         txPachube.DataFields.Id : 7021,
                         txPachube.DataFields.Maximum_Value : "35.8",
                         txPachube.DataFields.Minimum_Value : "15.9",
                         txPachube.DataFields.Tags : ['temp', 'Temperature', 'C'],
                         txPachube.DataFields.Unit : unit_kwargs,
                         txPachube.DataFields.Updated : "2010-04-12T11:31:51.133782Z"}
    test_datastream = txPachube.Datastream(**datastream_kwargs)    

    a = test_datastream.toDict()
    b = test_datastream.toXml()
    c = test_datastream.encode(txPachube.DataFormats.JSON)
    d = test_datastream.encode(txPachube.DataFormats.XML)
    test_datastream.decode(TEST_DATASTREAM_JSON, format=txPachube.DataFormats.JSON)
    test_datastream.decode(TEST_DATASTREAM_XML, format=txPachube.DataFormats.XML)
    
    
    # environment
    env_inDict = json.loads(TEST_FEED_JSON)
    test_environment = txPachube.Environment(**env_inDict)

    a = test_environment.toDict()
    b = test_environment.toXml()
    c = test_environment.encode(txPachube.DataFormats.JSON)
    d = test_environment.encode(txPachube.DataFormats.XML)
    test_environment.decode(TEST_FEED_JSON, format=txPachube.DataFormats.JSON)
    test_environment.decode(TEST_FEED_XML, format=txPachube.DataFormats.XML)
    
    # environment list
    envList_inDict = json.loads(TEST_FEEDS_LIST_JSON)
    envList = txPachube.EnvironmentList(**envList_inDict)

    a = envList.toDict()
    b = envList.toXml()
    c = envList.encode(txPachube.DataFormats.JSON)
    d = envList.encode(txPachube.DataFormats.XML)
    envList.decode(TEST_FEEDS_LIST_JSON, format=txPachube.DataFormats.JSON)
    envList.decode(TEST_FEEDS_LIST_XML, format=txPachube.DataFormats.XML)

    

    # trigger
    trigger_inDict = json.loads(TEST_TRIGGER_JSON)
    test_trigger = txPachube.Trigger(**trigger_inDict)

    a = test_trigger.toDict()
    b = test_trigger.toXml()
    c = test_trigger.encode(txPachube.DataFormats.JSON)
    d = test_trigger.encode(txPachube.DataFormats.XML)
    test_trigger.decode(TEST_TRIGGER_JSON, format=txPachube.DataFormats.JSON)
    test_trigger.decode(TEST_TRIGGER_XML, format=txPachube.DataFormats.XML)    
    
    # triggers list
    trigger_list_inDict = {txPachube.DataFields.Datastream_Trigger : json.loads(TEST_TRIGGERS_LIST_JSON)}
    test_trigger = txPachube.TriggerList(**trigger_list_inDict)

    a = test_trigger.toDict()
    b = test_trigger.toXml()
    c = test_trigger.encode(txPachube.DataFormats.JSON)
    d = test_trigger.encode(txPachube.DataFormats.XML)
    test_trigger.decode(TEST_TRIGGERS_LIST_JSON, format=txPachube.DataFormats.JSON)
    test_trigger.decode(TEST_TRIGGERS_LIST_XML, format=txPachube.DataFormats.XML) 
    

    # key 
    api_key_inDict = json.loads(TEST_API_KEY_JSON)
    test_key = txPachube.Key(**api_key_inDict)

    a = test_key.toDict()
    b = test_key.toXml()
    c = test_key.encode(txPachube.DataFormats.JSON)
    d = test_key.encode(txPachube.DataFormats.XML)
    test_key.decode(TEST_API_KEY_JSON, format=txPachube.DataFormats.JSON)
    test_key.decode(TEST_API_KEY_XML, format=txPachube.DataFormats.XML) 
    

    # key list
    key_list_inDict = json.loads(TEST_API_KEYS_LIST_JSON)
    test_key_list = txPachube.KeyList(**key_list_inDict)

    a = test_key_list.toDict()
    b = test_key_list.toXml()
    c = test_key_list.encode(txPachube.DataFormats.JSON)
    d = test_key_list.encode(txPachube.DataFormats.XML)
    test_key_list.decode(TEST_API_KEYS_LIST_JSON, format=txPachube.DataFormats.JSON)
    test_key_list.decode(TEST_API_KEYS_LIST_XML, format=txPachube.DataFormats.XML)
    
    # user 
    user_inDict = json.loads(TEST_USER_JSON)
    test_user = txPachube.User(**user_inDict)

    a = test_user.toDict()
    b = test_user.toXml()
    c = test_user.encode(txPachube.DataFormats.JSON)
    d = test_user.encode(txPachube.DataFormats.XML)
    test_user.decode(TEST_USER_JSON, format=txPachube.DataFormats.JSON)
    test_user.decode(TEST_USER_XML, format=txPachube.DataFormats.XML) 
    

    # user list
    user_list_inDict = {txPachube.DataFields.Users : json.loads(TEST_USERS_LIST_JSON)}
    test_user_list = txPachube.UserList(**user_list_inDict)

    a = test_user_list.toDict()
    b = test_user_list.toXml()
    c = test_user_list.encode(txPachube.DataFormats.JSON)
    d = test_user_list.encode(txPachube.DataFormats.XML)
    test_user_list.decode(TEST_USERS_LIST_JSON, format=txPachube.DataFormats.JSON)
    test_user_list.decode(TEST_USERS_LIST_XML, format=txPachube.DataFormats.XML)    
    
    
              
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    test_data_structures()
    print "Done"
    


    