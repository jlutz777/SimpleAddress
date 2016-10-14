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

    def getMultiple(self, userName, filterCriteria={}, sortColumn='',
                    secondSortColumn='', asc=True):
        """Return a list of objects associated with a user.

        :param userName: the name of the user
        :type userName: str
        :param filterCriteria: criteria for the data to match (if needed)
        :type filterCriteria: dict
        :param sortColumn: the sort column to use (if needed)
        :type sortColumn: str
        :param secondSortColumn: secondary sort solumn (if needed)
        :type secondSortColumn: str
        :param asc: sort direction, true for asc
        :type message: bool
        :returns: objects found
        :rtype: cursor

        """

        if asc:
            asc = 1
        else:
            asc = -1

        # Copy over if anyone passes in a userName so you can't impersonate
        filterCriteria['userName'] = userName

        if sortColumn == '':
            return self.table.find({'$query': filterCriteria})
        elif secondSortColumn == '':
            return self.table.find({'$query': filterCriteria,
                                    '$orderby': {sortColumn: asc}})
        else:
            self.table.ensure_index([('userName', asc), (sortColumn, asc),
                                     (secondSortColumn, asc)])
            return self.table.find({'$query': filterCriteria}) \
                             .sort([(sortColumn, asc),
                                    (secondSortColumn, asc)])

    def create(self, item, userName):
        """Create a new item and returns the id.

        :param item: the data to be inserted
        :type item: str
        :param userName: the name of the user
        :type userName: str
        :returns: id of inserted item
        :rtype: str

        """

        item['userName'] = userName
        return str(self.table.insert(item))

    def updateMultiple(self, ids, items, userName):
        """Update a group of items and returns success.

        :param ids: the ids of the items to be updated
        :type ids: list or string
        :param items: the objects to be updated
        :type items: list or object
        :param userName: the name of the user
        :type userName: str
        :returns: success of update
        :rtype: bool

        """

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
        """Update a single item and returns success.

        :param thisId: the id of the item to be updated
        :type thisId: string
        :param item: the data to be updated
        :type item: str
        :param userName: the name of the user
        :type userName: str
        :returns: success of update
        :rtype: bool

        """

        item['userName'] = userName
        res = self.table.update({'_id': thisId, 'userName': userName},
                                {'$set': item})
        if res['updatedExisting']:
            return True
        else:
            return False

    def delete(self, thisId, userName):
        """Update a single item and returns success.

        :param thisId: the id of the item to be deleted
        :type thisId: string
        :param userName: the name of the user
        :type userName: str
        :returns: success of update
        :rtype: bool

        """

        res = self.table.remove({'_id': thisId, 'userName': userName})
        print str(res)
        if res[u'ok'] == 1:
            return True
        else:
            return False

    def getCreationFields(self):
        """Return list of the fields for creating an item.

        :returns: fields for creation of item
        :rtype: list

        """

        return fieldsFromFieldNameArray(self.fields)
