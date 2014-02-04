from pymongo import MongoClient
from libraries.utils import fieldsFromFieldNameArray

class DataModel(object):
    fields = []

    def __init__(self, mongoUrl, dbName, tableName):
        client = MongoClient(mongoUrl)
        db = client[dbName]
        self.table = db[tableName]

    def getMultiple(self, userName, sortColumn='last_name', asc=True):
        if asc:
            asc = 1
        else:
            asc = -1
        return self.table.find( {'$query': {'userName' : userName}, '$orderby': { sortColumn : asc } })

    # If ever needed, do the check for username
    #def get(self, criteria):
    #    return self.table.find_one(criteria)

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
        res = self.table.update({'_id': thisId, 'userName': userName}, {'$set': item})
        if res[u'updatedExisting'] and res[u'err'] is None:
            return True
        else:
            return False

    def delete(self, thisId, userName):
        res = self.table.remove({'_id': thisId, 'userName': userName})
        print str(res)
        if res[u'err'] is None and res[u'n'] <> 0:
            return True
        else:
            return False

    def getCreationFields(self):
        return fieldsFromFieldNameArray(self.fields)
