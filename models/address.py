"""
This is an address object to easily do CRUD operations.

Currently the module speaks with a mongo database in the
backend, but it could be flexible enough to speak
with anything.

"""

from dataobject import DataModel


class AddressModel(DataModel):

    """
    This class does CRUD operations on an address.

    It has all the requisite required fields and other
    information needed to speak with the database.

    """

    def __init__(self, mongoUrl, dbName, collectionName='simpleaddresses'):
        super(AddressModel, self).__init__(mongoUrl, dbName, collectionName)

    def getCreationFields(self):
        """Return array of fields for creating a new address.

        :returns: creation fields
        :rtype: list

        """

        self.fields = ["first_name", "last_name", "spouse", "email_address",
                       "street_1", "street_2", "city", "state", "zip",
                       "country", "home_phone", "mobile_phone",
                       "relationship", "title", "children", "label_name",
                       ("send_christmas_card", "checkBox")]
        return super(AddressModel, self).getCreationFields()
