from dataobject import DataModel
import os

class AddressModel(DataModel):
    def __init__(self):
        MONGO_DB = os.environ.get('MONGOHQ_DB')
        super(AddressModel, self).__init__(MONGO_DB, 'simpleaddresses')

    def getCreationFields(self):
        self.fields = ["first_name", "last_name", "spouse", "email_address", "street_1", "street_2", "city", "state", "zip", "country", "home_phone", "mobile_phone", "relationship", "title", "children", "label_name"]
        return super(AddressModel, self).getCreationFields()
