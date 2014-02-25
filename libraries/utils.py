"""
This is a catch-all module for various utilities.

Keeping this functionality in one file makes it easy to
reference from outside.  The module contains a JSON
converter, a CSV import and export, a Field for easily
printing out data object fields automatically, and more.

"""

from bson import json_util
from bson.objectid import ObjectId
import io
import csv
import json
from pymongo.cursor import Cursor


class JSONHelper:

    """
    This class converts to and from JSON for you.

    Given an object of pretty much any sort, it converts
    to and from JSON.  For a mongo cursor, it converts
    id for you to a string.

    """

    def encode(self, o):
        """Return a json string of the object.

        :param o: the object to JSON serialize
        :returns: JSON of the object
        :rtype: str

        """

        if isinstance(o, Cursor):
            results = []
            for item in o:
                idToStr(item)
                results.append(item)
            return json.dumps(results, default=json_util.default)
        else:
            return json.dumps(o, default=json_util.default)

    def pullId(self, data):
        """Separate the id of the dict from the rest of the data.

        :param data: the dict to separate id
        :param type: dict
        :returns: The id and the data, separated
        :rtype: tuple

        """

        thisId = data.get('_id', None)
        if thisId:
            del data['_id']
            return strToId(thisId), data
        else:
            return thisId, data

    def decode(self, o):
        """Return the json decoded data of an object.

        :param o: the JSON string to deserialize
        :type o: str
        :returns: The ids and the objects, separated
        :rtype: tuple of lists

        """

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

    """
    This class converts to and from CSV for you.

    Given fields or a file, CSV conversion is done.

    """

    def convertToCSV(self, o, orderedFields):
        """Return a string in csv form.

        :param o: the object to convert to csv
        :param orderFields: the fields to convert
        :type orderFields: list of fields
        :returns: string in csv form
        :rtype: str

        """

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
        """Return a list of dictionaries from a csv file.

        :param fileName: the filename to parse
        :type fileName: str
        :returns: a list of dictionaries from the csv info
        :rtype: list

        """

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
    """Take a dictionary of data and convert the _id column to a str.

    :param row: the dictionary to convert
    :type row: dict
    :returns: (nothing) ... converts inline

    """

    for key in row:
        if key == '_id':
            row[key] = str(row[key])
            break


def strToId(thisStr):
    """Return an ObjectId from a str.

    :param thisStr: the string to convert to ObjectId
    :type thisStr: str
    :returns: the converted string
    :rtype: ObjectId

    """

    return ObjectId(thisStr)


def fieldsFromFieldNameArray(fieldNames):
    """Return a list of fields based on field names.

    Note that the field names follow a naming convention
    in order to be properly converted.  They must have
    underscores where words are separated.

    :param fieldNames: the names of the fields
    :type fileName: list
    :returns: Fields for the given field names
    :rtype: list

    """

    fields = []
    for field in fieldNames:
        if type(field) is not str:
            fields.append(Field(field[0], field[1]))
        elif field != "_id":
            fields.append(Field(field))
    return fields


class Field:

    """
    Field class to easily convert inputs to fields.

    They store information, parse the placeholder test,
    and store field types if given.

    """

    name = ''
    placeholder = ''
    fieldType = ''

    def __init__(self, name, fieldType='', placeholder=''):
        self.name = name
        self.fieldType = fieldType
        if placeholder == '':
            self.parsePlaceholderFromName()
        else:
            self.placeholder = placeholder

    def parsePlaceholderFromName(self):
        """Get the placeholder from the field name.

        This uses a naming convention of underscores for
        new words so it can be easily parsed.

        :returns: the place holder text for the field

        """

        if self.placeholder == '':
            pieces = self.name.split("_")
            nameWithSpaces = " ".join(pieces)
            self.placeholder = nameWithSpaces.title()
        return self.placeholder

    def __repr__(self):
        return self.placeholder
