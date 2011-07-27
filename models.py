#!/usr/bin/env python
from google.appengine.ext import db

class SparkSpectralUser(db.Model):
    user_name = db.StringProperty(required=False)
    user_created = db.DateTimeProperty(auto_now_add=True)
    user_created = db.DateTimeProperty(auto_now_add=True)
    
class SparkResourceType(db.Model):
    type = db.StringProperty()
    uri = db.LinkProperty(required=False)
    
class SparkSpectralTopic(db.Model):
    topic = db.StringProperty()
    topic_uri= db.LinkProperty(required=False)
    topic_created = db.DateTimeProperty(auto_now_add=True)
    topic_changed = db.DateTimeProperty(auto_now_add=True)
    
class UserTopicRelation(db.Model):
    user_ref=db.ReferenceProperty(SparkSpectralUser)
    topic_ref= db.ReferenceProperty(SparkSpectralTopic)
    weight = db.IntegerProperty(default=100)
    relation_created = db.DateTimeProperty(auto_now_add=True)
    relation_changed = db.DateTimeProperty(auto_now_add=True)
    explicitly_set = db.BooleanProperty(default= True)
    inferred_from = db.SelfReferenceProperty(required=False)
    
    


