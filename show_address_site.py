from bottle import Bottle, hook, HTTPResponse, request, TEMPLATE_PATH
from bottle import jinja2_template as template, static_file, debug
from beaker.middleware import SessionMiddleware
from cork import Cork, AuthException
from cork.backends import MongoDBBackend
from gunicorn.app.base import Application
from libraries.utils import JSONHelper, strToId, CSVHelper
from models.address import AddressModel
import logging
import os

logging.basicConfig(format='localhost - - [%(asctime)s] %(message)s',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)
debug(True)

MODULEPATH = os.path.dirname(__file__)
TEMPLATE_PATH.append(os.path.join(MODULEPATH, "views"))
LOGIN_PATH = '/login'
CHANGE_PASSWORD_PATH = '/change_password'
VALIDATE_REGISTRATION_PATH = '/validate_registration'


class AddressServer(Application):
    """Strongly borrowed from:
    http://damianzaremba.co.uk/2012/08/running-a-wsgi-
    app-via-gunicorn-from-python/"""

    def __init__(self, options={}):
        self.usage = None
        self.callable = None
        self.prog = None
        self.options = options
        self.do_load_config()

        self.setup_cork()

        super(AddressServer, self).__init__()
        self.app = Bottle()
        self.add_routes()
        self.add_middleware()

    def setup_cork(self):
        EMAIL = os.environ.get('EMAIL_SENDER')
        EMAIL_PASS = os.environ.get('EMAIL_PASSWORD')
        self.MONGO_DB = os.environ.get('MONGOHQ_DB')
        self.MONGO_URL = os.environ.get('MONGOHQ_URL')
        mb = MongoDBBackend(self.MONGO_DB, self.MONGO_URL)
        self.loginPlugin = Cork(backend=mb, email_sender=EMAIL,
                                smtp_url='starttls://' + EMAIL + ':' +
                                EMAIL_PASS + '@smtp.gmail.com:587')

    def add_middleware(self):
        ENCRYPT_KEY = os.environ.get('ENCRYPT_KEY')
        session_opts = {
            'session.cookie_expires': True,
            'session.encrypt_key': ENCRYPT_KEY,
            'session.httponly': True,
            'session.timeout': 3600 * 24,  # 1 day
            'session.type': 'cookie',
            'session.validate_key': True,
        }
        self.app = SessionMiddleware(self.app, session_opts)

    def add_routes(self):
        self.app.route(LOGIN_PATH, 'GET', callback=get_login)
        self.app.route(LOGIN_PATH, 'POST', callback=post_login,
                       apply=self.add_login_plugin)
        self.app.route('/logout', 'GET', callback=logout,
                       apply=self.add_login_plugin)
        self.app.route('/register', 'POST', callback=post_register,
                       apply=self.add_login_plugin)
        self.app.route(VALIDATE_REGISTRATION_PATH + '/<registration_code>',
                       'GET', callback=validate_registration,
                       apply=self.add_login_plugin)
        self.app.route(CHANGE_PASSWORD_PATH + '/<reset_code>', 'GET',
                       callback=get_change_password)
        self.app.route(CHANGE_PASSWORD_PATH, 'POST',
                       callback=post_change_password,
                       apply=self.add_login_plugin)
        self.app.route('/reset_password', 'POST', callback=reset_password,
                       apply=self.add_login_plugin)

        self.app.route('/', 'GET', callback=index, apply=self.check_login)
        self.app.route('/addresses', 'GET', callback=get_addresses,
                       apply=self.check_login)
        self.app.route('/addresses', 'POST', callback=post_addresses,
                       apply=self.check_login)
        self.app.route('/addresses', 'PUT', callback=put_addresses,
                       apply=self.check_login)
        self.app.route('/addresses/<deleteId>', 'DELETE',
                       callback=delete_addresses, apply=self.check_login)
        self.app.route('/csv', 'GET', callback=csv_export,
                       apply=self.check_login)
        self.app.route('/importcsv', 'GET', callback=csv_import,
                       apply=self.check_login)

        self.app.route('/js/<filename>', 'GET', callback=js_static)
        self.app.route('/css/<filename>', 'GET', callback=css_static)

    def init(self, *args):
        cfg = {}
        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                cfg[k.lower()] = v
        return cfg

    def load(self):
        return self.app

    @hook('before_request')
    def check_login(self, fn):
        def check_uid(**kwargs):
            self.loginPlugin.require(fail_redirect=LOGIN_PATH)
            kwargs["helper"] = AddressModel(self.MONGO_URL, self.MONGO_DB)
            kwargs["userName"] = self.loginPlugin.current_user.username
            return fn(**kwargs)
        return check_uid

    @hook('before_request')
    def add_login_plugin(self, fn):
        def add_plugin(**kwargs):
            kwargs["loginPlugin"] = self.loginPlugin
            return fn(**kwargs)
        return add_plugin


def post_get(name, default=''):
    return request.POST.get(name, default).strip()


def get_login():
    return template('login_form.html')


def post_login(loginPlugin):
    username = post_get('username')
    password = post_get('password')
    loginPlugin.login(username, password, success_redirect='/',
                      fail_redirect=LOGIN_PATH)


def logout(loginPlugin):
    loginPlugin.logout(success_redirect=LOGIN_PATH)


def post_register(loginPlugin):
    loginPlugin.register(post_get('username'), post_get('password'),
                         post_get('email_address'))
    return 'Please check your mailbox'


def validate_registration(loginPlugin, registration_code):
    loginPlugin.validate_registration(registration_code)
    return 'Thanks. <a href="/login">Go to login</a>'


def reset_password(loginPlugin):
    """Send out password reset email"""
    try:
        userName = post_get('username')
        emailAddress = post_get('email_address')
        loginPlugin.send_password_reset_email(username=userName,
                                              email_addr=emailAddress)
    except AuthException:
        return 'Invalid username or email address.'
    return 'Please check your mailbox.'


def get_change_password(reset_code):
    return template('password_reset_form.html', reset_code=reset_code)


def post_change_password(loginPlugin):
    loginPlugin.reset_password(post_get('reset_code'), post_get('password'))
    return 'Thanks. <a href="/login">Go to login</a>'


def index(helper, userName):
    address_fields = helper.getCreationFields()
    return template('home.html', address_fields=address_fields)


def get_addresses(helper, userName):
    addresses = helper.getMultiple(userName=userName)
    jsonAddresses = JSONHelper().encode(addresses)
    return HTTPResponse(jsonAddresses, status=200,
                        header={'Content-Type': 'application/json'})


def post_addresses(helper, userName):
    throwAway, newAddress = JSONHelper().decode(request.body.read())

    postId = helper.create(newAddress, userName=userName)
    if postId != -1:
        return HTTPResponse(JSONHelper().encode({'id': postId}), status=200,
                            header={'Content-Type': 'application/json'})
    else:
        return return_error(400, "Create did not work.")


def put_addresses(helper, userName):
    ids, decodeds = JSONHelper().decode(request.body.read())

    if helper.updateMultiple(ids, decodeds, userName=userName):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Update did not work.")


def delete_addresses(deleteId, helper, userName):
    if helper.delete(strToId(deleteId), userName=userName):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Delete did not work")


def csv_export(helper, userName):
    addresses = helper.getMultiple(userName=userName)
    csvAddresses = CSVHelper().convertToCSV(addresses,
                                            helper.getCreationFields())
    disposition = "attachment;filename=addresses.csv"
    return HTTPResponse(csvAddresses, status=200,
                        header={'Content-Type': 'text/csv',
                                'Content-disposition': disposition})


def csv_import(helper, userName):
    addresses = CSVHelper().convertFromCSV('contacts.csv')
    atleastOneFailed = False
    for address in addresses:
        if helper.create(address, userName=userName) == -1:
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
    json_err = JSONHelper().encode({'error': msg})
    return HTTPResponse(json_err, status=status,
                        header={'Content-Type': 'application/json'})

if __name__ == '__main__':
    ipaddress = "0.0.0.0"
    port = os.environ.get("PORT", 5000)
    AddressServer({"bind": ipaddress + ":" + port, "workers": 3,
                   "proc_name": "simpleaddress", "max_requests": 100,
                   "timeout": 300}).run()
