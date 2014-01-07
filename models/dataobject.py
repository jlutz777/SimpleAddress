from pymongo import MongoClient
from libraries.utils import fieldsFromFieldNameArray
import os

class DataModel(object):
    fields = []

    def __init__(self, dbName, tableName):
        MONGO_URL = os.environ.get('MONGOHQ_URL')
        client = MongoClient(MONGO_URL)
        db = client[dbName]
        self.table = db[tableName]

    def getMultiple(self, sortColumn='first_name', asc=True):
        if asc:
            asc = 1
        else:
            asc = -1
        return self.table.find( {'$query': {}, '$orderby': { sortColumn : asc } })

    def get(self, criteria):
        return self.table.find_one(criteria)

    def create(self, item):
        # returns the new id
        return str(self.table.insert(item))

    def updateMultiple(self, ids, items):
        if type(ids) is not list:
            return self.update(ids, items)
        else:
            # Return False if any updates didn't succeed
            success = True
            for i in range(len(ids)):
                if not self.update(ids[i], items[i]):
                    success = False
            return success

    def update(self, thisId, item):
        res = self.table.update({'_id': thisId}, {'$set': item})
        if res[u'updatedExisting'] and res[u'err'] is None:
            return True
        else:
            return False

    def delete(self, thisId):
        res = self.table.remove({'_id': thisId})
        print str(res)
        if res[u'err'] is None and res[u'n'] <> 0:
            return True
        else:
            return False

    def getCreationFields(self):
        return fieldsFromFieldNameArray(self.fields)
