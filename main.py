#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from calais import Calais
from urllib import urlopen,quote
from urllib2 import Request
from google.appengine.api import urlfetch
from xml.dom.minidom import parseString
import simplejson as json
from models import SparkSpectralUser,SparkSpectralTopic, UserTopicRelation
import logging

import re
CALAIS_API_KEY="pc5v39x8sq3mh4mv9zm2ppre"
FILENAME='sparks_list.txt'
FILENAME_JSON='sparks_list_json.txt'

class MainHandler(webapp.RequestHandler):
    calais = Calais('pc5v39x8sq3mh4mv9zm2ppre' , submitter="ask-a-sap-question")

    def get(self):
        file =open(FILENAME)
        for line in file:
            self.writeout(line)
        file.close()
        self.response.out.write('Hello world!')

    def writeout(self, topic):
        self.response.out.write("<h3>" + topic + "</h3><ul>")
        #topic_result= self.calais.analyze(topic)
        #if hasattr(topic_result, "entities"):
            #for entity in topic_result.entities:
                #self.response.out.write("<li>"+entity['name']+" (calais)<li/>")
        r = Request("http://spotlight.dbpedia.org/rest/annotate?text=" + quote(topic))
        r.add_header("Accept","application/json")
        u= urlopen(r)
        data= u.read()
        #if re.search(re.compile("<a href"),data) == None:
            #topic_result= self.calais.analyze(topic)
            #if hasattr(topic_result, "entities"):
                #for entity in topic_result.entities:
                    #self.response.out.write("<li>" + entity["name"] +" /relevance: " + "%f" %  entity["relevance"] + " (calais)<li/>")
        #else:
            #self.response.out.write("<li>"+data+" (dbpedia spotlight)<li/>")  http://dbpedia.org/ontology/MusicalArtist
        #self.response.out.write("</ul><hr/>")
        self.response.out.write("<li>"+data+" (dbpedia spotlight)<li/>") 

class PlusSparklerHandler(webapp.RequestHandler):

	def get(self):
		file= open(FILENAME_JSON)
		
		# analyze json
		json_data= json.load(file)
		file.close()
		# extract user_id 
		#user_id= json_data["user_id"]
		user_id= self.request.get("user_id")
		if user_id == '':
		    user_id= json_data["user_id"]
		    
		# if user_id exists
		user_obj= self.create_or_get_user(user_id)
		#if user_obj["is_new"]:
		# create mode for sparks
		self.response.out.write("You were here already.")
		
		for spark in json_data["sparks"]:
		    topic = self.create_or_get_topic(user_obj,spark)
		    self.response.out.write("<p>" + spark + "</p>")
		
		
		self.response.out.write('Hello world ' + user_id)
	
	def create_or_get_user(self,user_id):
	    q = SparkSpectralUser.all()
	    q.filter("user_name =", user_id)
	    if (q.count() >0):
		ssu= q.fetch(1)
		user_obj= ssu[0]
	    else:
		ssu= SparkSpectralUser(user_name= user_id)
		ssu.put()
		user_obj= ssu
	    return user_obj
	    
	def create_or_get_topic(self, user_obj, topic_name):
	    q = SparkSpectralTopic.all()
	    q.filter("topic =", topic_name)
	    if (q.count() >0):
		topic= q.fetch(1)
		topic_obj= topic[0]
	    else:
		topic_obj= SparkSpectralTopic(topic= topic_name)
		topic_obj.put()
		
	    q2= UserTopicRelation.all()
	    q2.filter("topic_ref =", topic_obj)
	    q2.filter("user_ref =", user_obj)
	    if (q2.count() >0 ):
                logging.info("UserTopicRelation found " + user_obj + " / " + topic_obj)
                pass
            else:
		rel= UserTopicRelation(topic_ref= topic_obj, user_ref= user_obj)
		rel.put()
                logging.info("UserTopicRelation created" + rel.user_ref + " / " + rel.topic_ref )
	    
	    return topic_obj
        
class TopicEnricherHandler(webapp.RequestHandler):
    
    def get(self):
        topics_query = SparkSpectralTopic.all()

        if (topics_query.count() >0 ):
            self.response.out.write("<ul>")
            topics= topics_query.fetch(100)
            for topic in topics:
                self.response.out.write("<li><b>" + topic.topic + "</b> ")
                if topic.topic_uri != None:
                    self.response.out.write("(topic uri: " + topic.topic_uri + " )")
                else:
                    r = "http://spotlight.dbpedia.org/rest/annotate?text=" + quote(topic.topic)
                    #r.add_header("Accept","application/json")
                    u= urlfetch.fetch(url= r, headers={'Accept': 'application/json'})
                    if u.status_code == 200:
                        json_data= json.loads(u.content)
                        if json_data["Resources"]:
                            self.response.out.write("<i>Data: "+json_data["Resources"][0]["@URI"] +"</i>") 
                
                self.response.out.write("</li>")
            self.response.out.write("</ul>")
        
def main():
    application = webapp.WSGIApplication([('/', MainHandler),('/plussparkler',PlusSparklerHandler), ('/enrichtopics',TopicEnricherHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
