"""
This is a standard data object to easily do CRUD operations.

Currently the module speaks with a mongo database in the
backend, but it could be flexible enough to speak
with anything.  This is generic in that the object could
be anything and is intended (but not required) to be
inherited from.

"""

from pymongo import MongoClient
from libraries.utils import fieldsFromFieldNameArray


class DataModel(object):

    """
    This class does CRUD operations on a generic object.

    It has all the requisite required fields and other
    information needed to speak with the database.
    If not inherited from, field should be defined if
    you easily want to discover the fields needed to
    create a new object.

    """

    fields = []

    def __init__(self, mongoUrl, dbName, tableName):
        client = MongoClient(mongoUrl)
        db = client[dbName]
        self.table = db[tableName]

    def getMultiple(self, userName, sortColumn='',
                    secondSortColumn='', asc=True):
        """Return a list of objects associated with a user.

        :param userName: the name of the user
        :type userName: str
        :param sortColumn: the sort column to use (if needed)
        :type sortColumn: str
        :param secondSortColumn: secondary sort solumn (if needed)
        :type secondSortColumn: str
        :param asc: sort direction, true for asc
        :type message: bool
        :returns: objects found
        :rtype: list

        """

        if asc:
            asc = 1
        else:
            asc = -1

        if sortColumn == '':
            return self.table.find({'$query': {'userName': userName}})
        elif secondSortColumn == '':
            return self.table.find({'$query': {'userName': userName},
                                    '$orderby': {sortColumn: asc}})
        else:
            self.table.ensure_index([('userName', asc), (sortColumn, asc),
                                     (secondSortColumn, asc)])
            return self.table.find({'$query': {'userName': userName}}) \
                             .sort([(sortColumn, asc),
                                    (secondSortColumn, asc)])

    def create(self, item, userName):
        item['userName'] = userName
        # returns the new id
        return str(self.table.insert(item))

    def updateMultiple(self, ids, items, userName):
        if type(ids) is not list:
            return self.update(ids, items, userName)
        else:
            # Return False if any updates didn't succeed
            success = True
            for i in range(len(ids)):
                if not self.update(ids[i], items[i], userName):
                    success = False
            return success

    def update(self, thisId, item, userName):
        item['userName'] = userName
        res = self.table.update({'_id': thisId, 'userName': userName},
                                {'$set': item})
        if res[u'updatedExisting'] and res[u'err'] is None:
            return True
        else:
            return False

    def delete(self, thisId, userName):
        res = self.table.remove({'_id': thisId, 'userName': userName})
        print str(res)
        if res[u'err'] is None and res[u'n'] != 0:
            return True
        else:
            return False

    def getCreationFields(self):
        return fieldsFromFieldNameArray(self.fields)
