#!/usr/bin/python

# Copyright (C) 2013 Gerwin Sturm, FoldedSoft e.U.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Model definition for the Mirror API."""


from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages

from endpoints_proto_datastore.ndb import EndpointsDateTimeProperty
from endpoints_proto_datastore.ndb import EndpointsModel
from endpoints_proto_datastore.ndb import EndpointsUserProperty
from endpoints_proto_datastore.ndb import EndpointsAliasProperty


class MenuAction(messages.Enum):
    REPLY = 1
    REPLY_ALL = 2
    DELETE = 3
    SHARE = 4
    READ_ALOUD = 5
    VOICE_CALL = 6
    NAVIGATE = 7
    TOGGLE_PINNED = 8
    CUSTOM = 9


class MenuValue(EndpointsModel):

    class MenuValueState(messages.Enum):
        DEFAULT = 1
        PENDING = 2
        CONFIRMED = 3

    displayName = ndb.StringProperty(required=True)
    iconUrl = ndb.StringProperty(required=True)
    state = msgprop.EnumProperty(MenuValueState, required=True)


class MenuItem(EndpointsModel):
    action = msgprop.EnumProperty(MenuAction, required=True)
    id = ndb.StringProperty()
    removeWhenSelected = ndb.BooleanProperty(default=False)
    values = ndb.LocalStructuredProperty(MenuValue, repeated=True)


class Attachment(EndpointsModel):
    """Attachment to a timeline card

    Due to limitations in Cloud Endpoints this works a bit differently than
    the attachments in the official API. Normally you would add attachments
    by uploading the media data (as image/audio/video). Attachments in this
    implementation can only by of type image and are represented either as
    URL or Data-URI and can be added/retrieved/updated directly by filling
    the attachments field in the timeline.insert method.
    """
    contentType = ndb.StringProperty()
    contentUrl = ndb.TextProperty()


class TimelineItem(EndpointsModel):
    """Model for timeline cards.

    Since the when property is auto_now_add=True, Cards will document when
    they were inserted immediately after being stored.
    """
    _message_fields_schema = (
        "id",
        "attachments",
        "bundleId",
        "canonicalUrl",
        "created",
        "displayTime",
        "html",
        "htmlPages",
        "inReplyTo",
        "isBundleCover",
        "isDeleted",
        "isPinned",
        "menuItems",
        "sourceItemId",
        "speakableText",
        "text",
        "title",
        "updated"
    )

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)

    attachments = ndb.StructuredProperty(Attachment, repeated=True)
    bundleId = ndb.StringProperty()
    canonicalUrl = ndb.StringProperty()
    created = EndpointsDateTimeProperty(auto_now_add=True)
    displayTime = EndpointsDateTimeProperty()
    html = ndb.TextProperty()
    htmlPages = ndb.TextProperty(repeated=True)
    inReplyTo = ndb.IntegerProperty()
    isBundleCover = ndb.BooleanProperty(default=False)
    isDeleted = ndb.BooleanProperty(default=False)
    isPinned = ndb.BooleanProperty(default=False)
    menuItems = ndb.LocalStructuredProperty(MenuItem, repeated=True)
    sourceItemId = ndb.StringProperty()
    speakableText = ndb.TextProperty()
    text = ndb.StringProperty()
    title = ndb.StringProperty()
    updated = EndpointsDateTimeProperty(auto_now=True)


class ShareEntity(EndpointsModel):
    """Model for share entities"""

    _message_fields_schema = ("id", "displayName", "imageUrls")

    displayName = ndb.StringProperty(required=True)
    imageUrls = ndb.StringProperty(repeated=True)
    user = EndpointsUserProperty(required=True, raise_unauthorized=True)

    def IdSet(self, value):
        if not isinstance(value, basestring):
            raise TypeError("ID must be a string.")

        self.UpdateFromKey(ndb.Key("User", self.user.email(), ShareEntity, value))

    @EndpointsAliasProperty(setter=IdSet, required=True)
    def id(self):
        if self.key is not None:
            return self.key.pairs()[1][1]


class Subscription(EndpointsModel):
    """Model for subscriptions"""

    _message_fields_schema = ("id", "collection", "userToken", "verifyToken", "operation", "callbackUrl")

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)
    collection = ndb.StringProperty(default="timeline")
    userToken = ndb.StringProperty(required=True)
    verifyToken = ndb.StringProperty(required=True)
    operation = msgprop.EnumProperty(MenuAction, repeated=True)
    callbackUrl = ndb.StringProperty(required=True)


class Action(messages.Message):
    """ProtoRPC Message Class for actions performed on timeline cards

    Since those actions are directly forwarded to subscriptions they
    don't need to be saved to the data store, hence no EndpointsModel class
    """

    collection = messages.StringField(1, default="timeline")
    itemId = messages.IntegerField(2, required=True)
    operation = messages.EnumField(MenuAction, 3, required=True)
    value = messages.StringField(4)


class ActionResponse(messages.Message):
    """Simple response to actions send to the Mirror API"""
    success = messages.BooleanField(1, default=True)
