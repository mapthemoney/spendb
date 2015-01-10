# coding=utf-8
import datetime
from json import dumps, loads
from sqlalchemy.types import Text, TypeDecorator
from sqlalchemy.sql.expression import select, func
from sqlalchemy.ext.mutable import Mutable

from openspending.core import db

ALIAS_PLACEHOLDER = u'‽'


def json_default(obj):
    if isinstance(obj, datetime.datetime):
        obj = obj.date()
    if isinstance(obj, datetime.date):
        obj = obj.isoformat()
    return obj


class MutableDict(Mutable, dict):

    """
    Create a mutable dictionary to track mutable values
    and notify listeners upon change.
    """

    @classmethod
    def coerce(cls, key, value):
        """
        Convert plain dictionaries to MutableDict
        """

        # If it isn't a MutableDict already we conver it
        if not isinstance(value, MutableDict):
            # If it is a dictionary we can convert it
            if isinstance(value, dict):
                return MutableDict(value)

            # Try to coerce but it will probably return a ValueError
            return Mutable.coerce(key, value)
        else:
            # Since we already have a MutableDict we can just return it
            return value

    def __setitem__(self, key, value):
        """
        Set a value to a key and notify listeners of change
        """

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        """
        Delete a key and notify listeners of change
        """

        dict.__delitem__(self, key)
        self.changed()


class JSONType(TypeDecorator):
    impl = Text

    def __init__(self):
        super(JSONType, self).__init__()

    def process_bind_param(self, value, dialect):
        return dumps(value, default=json_default)

    def process_result_value(self, value, dialiect):
        return loads(value)

    def copy_value(self, value):
        return loads(dumps(value))


class DatasetFacetMixin(object):

    @classmethod
    def dataset_counts(cls, datasets):
        ds_ids = [d.id for d in datasets]
        if not len(ds_ids):
            return []
        q = select([cls.code, func.count(cls.dataset_id)],
                   cls.dataset_id.in_(ds_ids), group_by=cls.code,
                   order_by=func.count(cls.dataset_id).desc())
        return db.session.bind.execute(q).fetchall()
