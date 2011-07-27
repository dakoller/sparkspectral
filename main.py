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
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from calais import Calais
from urllib import urlopen,quote
from urllib2 import Request
from google.appengine.api import urlfetch
from xml.dom.minidom import parseString
import simplejson as json
from models import SparkSpectralUser,SparkSpectralTopic, UserTopicRelation
import logging
import urllib2
import rdflib
import tweepy

from rdflib import ConjunctiveGraph
from rdflib.graph import Namespace, StringIO, RDF
from rdflib.term import BNode, Literal

import os
from google.appengine.ext.webapp import template
import re
CALAIS_API_KEY="pc5v39x8sq3mh4mv9zm2ppre"
FILENAME='sparks_list.txt'
FILENAME_JSON='sparks_list_json.txt'

class MainHandler(webapp.RequestHandler):
    calais = Calais('pc5v39x8sq3mh4mv9zm2ppre' , submitter="ask-a-sap-question")

    def get(self):
        json_s= self.request.get("json")
        self.response.out.write("<h2>Input data</h2><p>"+ urllib2.unquote(urllib2.quote(json_s.encode("utf8"))) + "</p><hr/>")

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
		#file= open(FILENAME_JSON)
		json_s= self.request.get("json")
                json_s2= urllib2.unquote(urllib2.quote(json_s.encode("utf8")))
		# analyze json
                logging.debug("json input: "+ json_s2)
                #self.response.out.write(json_s2)
		json_data= json.loads(json_s2)
                logging.info("user id: " + json_data["user_id"])
                
		#user_id= json_data["user_id"]
		user_id=''
                #user_id= self.request.get("user_id")
		if user_id == '':
		    user_id= json_data["user_id"]
		    
		# if user_id exists
		user_obj= self.create_or_get_user(user_id)
		
                content ='Hello world ' + user_id
		
		for spark in json_data["sparks"]:
		    topic = self.create_or_get_topic(user_obj,spark)
		    content= content + ("<p>" + spark + "</p>")
		
                
                template_values = {
                    'page_title': 'Page Title',
                    'content': content,
                    'url_linktext': 'web.de',
                }
        
                path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
                self.response.out.write(template.render(path, template_values))

	
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
                taskqueue.add(url="/enrichtopic",params={'topic2': topic_obj.topic, 'new_topic': True})
		
	    q2= UserTopicRelation.all()
	    q2.filter("topic_ref =", topic_obj)
	    q2.filter("user_ref =", user_obj)
	    if (q2.count() >0 ):
                logging.info("UserTopicRelation found " + user_obj.user_name + " / " + topic_obj.topic)
            else:
		rel= UserTopicRelation(topic_ref= topic_obj, user_ref= user_obj, weight=100)
		rel.put()
                logging.info("UserTopicRelation created" + topic_obj.topic + " / " + user_obj.user_name )
	    
	    return topic_obj
        
class TopicEnricherHandler(webapp.RequestHandler):
    
    def get(self):
        topic2= self.request.get("topic2")
        topics_query = SparkSpectralTopic.all()
        topics_query.filter("topic =", topic2)
        logging.warning("working on " + self.request.get("topic2"))
        new_topic = self.request.get("new_topic")
        if (topics_query.count() >0 ):
            topics= topics_query.fetch(1)
            for t in topics:
                logging.info("now enriching topic " + t.topic )
                if t.topic_uri != None:
                    logging.info("(topic uri: " + topic.topic_uri + " )")
                else:
                    logging.info("now going to dbpedia spotlight")
                    uri= self.getDBPediaURI(t.topic)
                    if uri != "":
                        logging.info("dbpedia lookup result= " + uri)
                        self.response.out.write("dbpedia lookup result= " + uri)
                        t.topic_uri= uri
                        t.put()
                    else:
                        logging.info("dbpedia lookup failed: no resource uri failed")
                        self.response.out.write("dbpedia lookup failed: no resource uri failed")
        else:
            logging.error("no topics found for " + self.request.get("topic2"))
    
    def post(self):
        topic2= self.request.get("topic2")
        topics_query = SparkSpectralTopic.all()
        topics_query.filter("topic =", topic2)
        logging.warning("working on " + self.request.get("topic2"))
        new_topic = self.request.get("new_topic")
        if (topics_query.count() >0 ):
            topics= topics_query.fetch(1)
            for t in topics:
                logging.info("now enriching topic " + t.topic )
                if t.topic_uri != None:
                    logging.info("(topic uri: " + topic.topic_uri + " )")
                else:
                    logging.info("now going to dbpedia spotlight")
                    uri= self.getDBPediaURI(t.topic)
                    if uri != "":
                        logging.info("dbpedia lookup result= " + uri)
                        self.response.out.write("dbpedia lookup result= " + uri)
                        t.topic_uri= uri
                        t.put()
                    else:
                        logging.info("dbpedia lookup failed: no resource uri failed")
                        self.response.out.write("dbpedia lookup failed: no resource uri failed")
        else:
            logging.error("no topics found for " + self.request.get("topic2"))
                    
    
    def getDBPediaURI(self,topic):
        result= urlfetch.fetch(url= "http://spotlight.dbpedia.org/rest/annotate?text=" + quote(topic), headers={"Accept": "application/json"})
        if result.status_code == 200:
            json_data= json.loads(result.content)
            logging.info("found following data to enrich topic '" + topic + "': " + str(json_data))
            try:
                dbpedia_uri=json_data["Resources"][0]["@URI"]
                return dbpedia_uri
            except KeyError:
                logging.error("no resource uri's found for "+ topic)
                return ""
        else:
            logging.error("getting dbpedia input for " + topic + " failed.")
            return ""
        
class UserProfileHandler(webapp.RequestHandler):

	def get(self):		
            user_id= self.request.get("user_id")
            
            logging.info("user id requested: " + user_id)
            user_obj= self.create_or_get_user(user_id)
            
            graph = ConjunctiveGraph()
            user_node= BNode()
            
            FOAF = Namespace("http://xmlns.com/foaf/0.1/")
            graph.add((user_node, RDF.type, FOAF['Person']))
            graph.add((user_node, FOAF['surname'], Literal('Koller')))
            
            content ='Hello world ' + graph.serialize()
            
            
            template_values = {
                'page_title': 'Page Title',
                'content': content,
                'url_linktext': 'web.de',
            }
    
            path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
            self.response.out.write(template.render(path, template_values))

	
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
	    
                
def main():
    application = webapp.WSGIApplication([('/', MainHandler),('/plussparkler',PlusSparklerHandler), ('/enrichtopic',TopicEnricherHandler),('/userprofile',UserProfileHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
