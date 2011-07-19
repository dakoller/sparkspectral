#!/usr/bin/env python
from google.appengine.ext import db

class SparkSpectralUser(db.Model):
    user_name = db.StringProperty(required=False)
    is_new = bool
    
class SparkSpectralTopic(db.Model):
    topic = db.StringProperty()
    topic_uri= db.LinkProperty()
    
class UserTopicRelation(db.Model):
    user_ref=db.ReferenceProperty(SparkSpectralUser)
    topic_ref= db.ReferenceProperty(SparkSpectralTopic)
    


