from bottle import Bottle, get, post, put, delete, HTTPResponse, request, route, run, TEMPLATE_PATH, jinja2_template as template, static_file
from gunicorn.app.base import Application
from libraries.utils import JSONHelper, strToId, CSVHelper
from models.address import AddressModel
import os

MODULEPATH = os.path.dirname(__file__)
TEMPLATE_PATH.append(os.path.join(MODULEPATH,"views"))

class AddressServer(Application):
    """Strongly borrowed from:  http://damianzaremba.co.uk/2012/08/running-a-wsgi-app-via-gunicorn-from-python/"""

    def __init__(self, options={}):
        self.usage = None
        self.callable = None
        self.prog = None
        self.options = options
        self.do_load_config()
        super(AddressServer, self).__init__()
        self.app = Bottle()
        self.add_routes()

    def add_routes(self):
        self.app.route('/', 'GET', callback=index)
        self.app.route('/addresses', 'GET', callback=get_addresses)
        self.app.route('/addresses', 'POST', callback=post_addresses)
        self.app.route('/addresses', 'PUT', callback=put_addresses)
        self.app.route('/addresses/<deleteId>', 'DELETE', callback=delete_addresses)
        self.app.route('/csv', 'GET', callback=csv_export)
        self.app.route('/importcsv', 'GET', callback=csv_import)
        self.app.route('/js/<filename>', 'GET', callback=js_static)
        self.app.route('/css/<filename>', 'GET', callback=css_static)

    def init(self, *args):
        cfg = {}
        for k,v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                cfg[k.lower()] = v
        return cfg

    def load(self):
        return self.app

def index():
    address_fields=AddressModel().getCreationFields()
    return template('home.html', address_fields=address_fields)

def get_addresses():
    helper = AddressModel()
    addresses = helper.getMultiple()
    jsonAddresses = JSONHelper().encode(addresses)
    return HTTPResponse(jsonAddresses, status=200, header={'Content-Type':'application/json'})

def post_addresses():
    helper = AddressModel()
    throwAway, newAddress = JSONHelper().decode(request.body.read())

    postId = helper.create(newAddress)
    if postId != -1:
        return HTTPResponse(JSONHelper().encode({'id':postId}), status=200, header={'Content-Type':'application/json'})
    else:
        return return_error(400, "Create did not work.")

def put_addresses():
    helper = AddressModel()
    ids, decodeds = JSONHelper().decode(request.body.read())

    if helper.updateMultiple(ids, decodeds):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Update did not work.")

def delete_addresses(deleteId):
    helper = AddressModel()

    if helper.delete(strToId(deleteId)):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Delete did not work")

def csv_export():
    helper = AddressModel()
    addresses = helper.getMultiple()
    csvAddresses = CSVHelper().convertToCSV(addresses, helper.getCreationFields())
    return HTTPResponse(csvAddresses, status=200, header={'Content-Type': 'text/csv', 'Content-disposition': 'attachment;filename=addresses.csv'})

def csv_import():
    helper = AddressModel()
    addresses = CSVHelper().convertFromCSV('contacts.csv')
    atleastOneFailed = False
    for address in addresses:
        if helper.create(address) == -1:
            atleastOneFailed = True
    if not atleastOneFailed:
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Import did not work.")
    
def js_static(filename):
    return static_file(filename, root=os.path.join(MODULEPATH, 'static/js'))

def css_static(filename):
    return static_file(filename, root=os.path.join(MODULEPATH, 'static/css'))

def return_error(status, msg=''):
    json_err = JSONHelper().encode({'error':msg})
    return HTTPResponse(json_err, status=status, header={'Content-Type':'application/json'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    AddressServer({"bind": "0.0.0.0:"+str(port), "workers": 3, "proc_name": "simpleaddress", "max_requests": 100, "timeout": 300}).run()
