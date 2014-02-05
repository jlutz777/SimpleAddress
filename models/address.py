from dataobject import DataModel


class AddressModel(DataModel):
    def __init__(self, mongoUrl, dbName, collectionName='simpleaddresses'):
        super(AddressModel, self).__init__(mongoUrl, dbName, collectionName)

    def getCreationFields(self):
        self.fields = ["first_name", "last_name", "spouse", "email_address",
                       "street_1", "street_2", "city", "state", "zip",
                       "country", "home_phone", "mobile_phone",
                       "relationship", "title", "children", "label_name"]
        return super(AddressModel, self).getCreationFields()
