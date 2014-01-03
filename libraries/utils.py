from bson import json_util
from bson.objectid import ObjectId
import io
import csv
import json
from pymongo.cursor import Cursor

class JSONHelper:
    def encode(self, o):
        if isinstance(o, Cursor):
            results = []
            for item in o:
                idToStr(item)
                results.append(item)
            return json.dumps(results, default=json_util.default)
        else:
            return json.dumps(o, default=json_util.default)

    def pullId(self, data):
        thisId = data.get('_id', None)
        if thisId:
            del data['_id']
            return strToId(thisId), data
        else:
            return thisId, data

    def decode(self, o):
        data = json.loads(o, object_hook=json_util.object_hook)
        if type(data) is list:
            ids = []
            objs = []
            for item in data:
                thisId, thisObj = self.pullId(item)
                ids.append(thisId)
                objs.append(thisObj)
            return ids, objs
        else:
            return self.pullId(data)

class CSVHelper:
    def convertToCSV(self, o, orderedFields):
        output = io.BytesIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(orderedFields)
        for item in o:
            idToStr(item)
            orderedValues = []
            for field in orderedFields:
                orderedValues.append(item.get(field.name, ''))
            writer.writerow(orderedValues)
        return output.getvalue()

    def convertFromCSV(self, fileName):
        reader = csv.reader(open(fileName), delimiter=',', quotechar='"')
        headers = reader.next()
        convertedData = []
        for row in reader:
            thisRow = {}
            for i in range(len(headers)):
                thisRow[headers[i]] = row[i]
            convertedData.append(thisRow)
        return convertedData

def idToStr(row):
    for key in row:
        if key == '_id':
            row[key] = str(row[key])

def strToId(thisStr):
    return ObjectId(thisStr)

def fieldsFromFieldNameArray(fieldNameArray):
    fields = []
    for field in fieldNameArray:
        if field != "_id":
            fields.append(Field(field))
    return fields

class Field:
    name = ''
    placeholder = ''

    def __init__(self, name):
        self.name = name
        self.parsePlaceholderFromName()

    def parsePlaceholderFromName(self):
        pieces = self.name.split("_")
        nameWithSpaces = " ".join(pieces)
        self.placeholder = nameWithSpaces.title()
        return self.placeholder

    def __repr__(self):
        return self.placeholder

