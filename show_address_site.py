import os
from bottle import get, post, put, delete, HTTPResponse, request, route, run, TEMPLATE_PATH, jinja2_template as template, static_file
from libraries.utils import JSONHelper, strToId, CSVHelper
from models.address import AddressModel

MODULEPATH = os.path.dirname(__file__)
TEMPLATE_PATH.append(os.path.join(MODULEPATH,"views"))

@route('/')
def index():
    address_fields=AddressModel().getCreationFields()
    return template('home.html', address_fields=address_fields)

@get('/addresses')
def get_addresses():
    helper = AddressModel()
    addresses = helper.getMultiple()
    jsonAddresses = JSONHelper().encode(addresses)
    return HTTPResponse(jsonAddresses, status=200, header={'Content-Type':'application/json'})

@post('/addresses')
def post_addresses():
    helper = AddressModel()
    throwAway, newAddress = JSONHelper().decode(request.body.read())

    postId = helper.create(newAddress)
    if postId != -1:
        return HTTPResponse(JSONHelper().encode({'id':postId}), status=200, header={'Content-Type':'application/json'})
    else:
        return return_error(400, "Create did not work.")

@put('/addresses')
def put_addresses():
    helper = AddressModel()
    ids, decodeds = JSONHelper().decode(request.body.read())

    if helper.updateMultiple(ids, decodeds):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Update did not work.")

@delete('/addresses/<deleteId>')
def delete_addresses(deleteId):
    helper = AddressModel()

    if helper.delete(strToId(deleteId)):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Delete did not work")

@get('/csv')
def csv_export():
    helper = AddressModel()
    addresses = helper.getMultiple()
    csvAddresses = CSVHelper().convertToCSV(addresses, helper.getCreationFields())
    return HTTPResponse(csvAddresses, status=200, header={'Content-Type': 'text/csv', 'Content-disposition': 'attachment;filename=addresses.csv'})

@get('/importcsv')
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
    
@route('/js/<filename>')
def js_static(filename):
    return static_file(filename, root=os.path.join(MODULEPATH, 'static/js'))

@route('/css/<filename>')
def css_static(filename):
    return static_file(filename, root=os.path.join(MODULEPATH, 'static/css'))

def return_error(status, msg=''):
    json_err = JSONHelper().encode({'error':msg})
    return HTTPResponse(json_err, status=status, header={'Content-Type':'application/json'})

run(host='0.0.0.0', port=80)
