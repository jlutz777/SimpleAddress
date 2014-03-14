"""
This is the main file for starting up the entire address site.

It wraps everything and glues it all together to grab the proper
views, utilities, models, and static files.  The application itself
runs wsgi via gunicorn and serves up the web with bottle.  Authentication
is done through cork, templates through jinja, client side manipulation
through AngularJS, css is mostly bootstrap, and the backend via MongoDB.
The rest is custom code to bring it all together.

"""

from bottle import Bottle, hook, HTTPResponse, request, TEMPLATE_PATH
from bottle import jinja2_template as template, static_file, debug
from beaker.middleware import SessionMiddleware
from cork import Cork, AuthException, AAAException
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

    """
    This class is the gunicorn wrapper to serve up bottle.

    Strongly borrowed from:
    http://damianzaremba.co.uk/2012/08/running-a-wsgi-
    app-via-gunicorn-from-python/

    """

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
        """Set up cork using environment variables."""

        EMAIL = os.environ.get('EMAIL_SENDER')
        EMAIL_PASS = os.environ.get('EMAIL_PASSWORD')
        self.MONGO_DB = os.environ.get('MONGOHQ_DB')
        self.MONGO_URL = os.environ.get('MONGOHQ_URL')
        mb = MongoDBBackend(self.MONGO_DB, self.MONGO_URL)
        self.loginPlugin = Cork(backend=mb, email_sender=EMAIL,
                                smtp_url='starttls://' + EMAIL + ':' +
                                EMAIL_PASS + '@smtp.gmail.com:587')

    def add_middleware(self):
        """Set up the session middleware."""

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
        """Add all the application routes."""

        self.app.route(LOGIN_PATH, 'GET', callback=get_login)
        self.app.route(LOGIN_PATH, 'POST', callback=post_login,
                       apply=self.add_login_plugin)
        self.app.route('/logout', 'GET', callback=logout,
                       apply=self.add_login_plugin)
        self.app.route('/register', 'GET', callback=get_register,
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
        self.app.route('/reset_password', 'GET', callback=get_reset_password)
        self.app.route('/reset_password', 'POST', callback=post_reset_password,
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
        self.app.route('/christmas_card', 'GET',
                       callback=christmas_card_csv_export,
                       apply=self.check_login)
#        self.app.route('/import_csv', 'GET', callback=csv_import,
#                       apply=self.check_login)

        self.app.route('/js/<filename>', 'GET', callback=js_static)
        self.app.route('/css/<filename>', 'GET', callback=css_static)

    def init(self, *args):
        """Add any options passed in to the config.

        :param *args: the arguments of the application
        :returns: config object
        :rtype: dict

        """

        cfg = {}
        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                cfg[k.lower()] = v
        return cfg

    def load(self):
        """Load and return the bottle app."""

        return self.app

    @hook('before_request')
    def check_login(self, fn):
        """Hook for checking the login before doing logic.

        :param fn: the function to call if the user is logged in
        :returns: the wrapped function
        :rtype: def

        """

        def check_uid(**kwargs):
            self.loginPlugin.require(fail_redirect=LOGIN_PATH)
            kwargs["helper"] = AddressModel(self.MONGO_URL, self.MONGO_DB)
            kwargs["userName"] = self.loginPlugin.current_user.username
            return fn(**kwargs)
        return check_uid

    @hook('before_request')
    def add_login_plugin(self, fn):
        """Hook for adding the plugin information.

        :param fn: the function to pass the plugin
        :returns: the wrapped function
        :rtype: def

        """

        def add_plugin(**kwargs):
            kwargs["loginPlugin"] = self.loginPlugin
            return fn(**kwargs)
        return add_plugin


def post_get(name, default=''):
    """Get posted information.

    :param name: the key of the posted information
    :type name: str
    :param default: the default value if not found
    :type default: str
    :returns: the value of the posted information
    :rtype: str

    """

    return request.POST.get(name, default).strip()


def get_login():
    """The login page.

    :returns: the html of the login page
    :rtype: str

    """

    return template('login.html')


def post_login(loginPlugin):
    """Handle the login page's post information.

    If successful, it redirects to the home page, but if it fails
    it goes back to the login page.

    :param loginPlugin: the login plugin to authenticate against
    :type loginPlugin: object
    :returns: (nothing)

    """

    errMessage = ''
    success = False
    try:
        username = post_get('username')
        password = post_get('password')
        success = loginPlugin.login(username, password, success_redirect='/')
        if not success:
            errMessage = 'User name and/or password were incorrect.'
    # redirects throw an exception, so ignore
    except HTTPResponse:
        raise
    except Exception:
        errMessage = 'Login had an unknown error.'
        log.exception(errMessage)
    return template('login.html', errMessage=errMessage)


def logout(loginPlugin):
    """Log out the current user and redirect to the login page.

    :param loginPlugin: the login plugin to log out
    :type loginPlugin: object
    :returns: (nothing)

    """

    loginPlugin.logout(success_redirect=LOGIN_PATH)


def get_register(loginPlugin):
    """Register a new user based on post information.

    :param loginPlugin: the login plugin to use to create a user
    :type loginPlugin: object
    :returns: the html after registering
    :rtype: str

    """

    return template('registration.html')


def post_register(loginPlugin):
    """Register a new user based on post information.

    :param loginPlugin: the login plugin to use to create a user
    :type loginPlugin: object
    :returns: the html after registering
    :rtype: str

    """

    errMessage = ''
    success = False
    try:
        loginPlugin.register(post_get('username'), post_get('password'),
                             post_get('email_address'))
        success = True
    except AssertionError:
        errMessage = 'You must fill out user name, password,'
        errMessage += ' and email address to register.'
        log.exception(errMessage)
    except Exception:
        errMessage = 'An unknown error occurred.'
        log.exception(errMessage)
    return template('registration.html', success=success,
                    errMessage=errMessage)


def validate_registration(loginPlugin, registration_code):
    """Validate a registration so a new user can log in.

    Once registered users receive an email, they will click on a link
    to validate before logging in.

    :param loginPlugin: the login plugin to validate against
    :type loginPlugin: object
    :param registration_code: the registration code from the email
    :type registration_code: str
    :returns: the html after validating
    :rtype: str

    """

    loginPlugin.validate_registration(registration_code)
    return 'Thanks. <a href="/login">Go to login</a>'


def get_reset_password():
    """Get the user name and email address to reset the password.

    :returns: the html form for resetting password
    :rtype: str

    """

    return template('get_reset_code.html')


def post_reset_password(loginPlugin):
    """Send out the password reset email.

    If the email fails, this page will display an error message.

    :param loginPlugin: the login plugin to user to reset the password
    :type loginPlugin: object
    :returns: the html after attempting to reset the password
    :rtype: str

    """

    errMessage = ''
    success = False
    try:
        userName = post_get('username')
        emailAddress = post_get('email_address')
        loginPlugin.send_password_reset_email(username=userName,
                                              email_addr=emailAddress)
    except AuthException:
        errMessage = 'Your username or email address is invalid.'
        log.exception(errMessage)
    except AAAException:
        errMessage = 'Your username is invalid.'
        log.exception(errMessage)
    except Exception:
        errMessage = 'An unknown error occurred.'
        log.exception(errMessage)
    return template('get_reset_code.html', success=success,
                    errMessage=errMessage)


def get_change_password(reset_code):
    """The change password page.

    :param reset_code: the reset code to get a changed password
    :type reset_code: str
    :returns: the html after attempting to change the password
    :rtype: str

    """

    return template('password_reset_form.html', reset_code=reset_code)


def post_change_password(loginPlugin):
    """Reset the password of a user.

    :param loginPlugin: the login plugin to user to change the password
    :type loginPlugin: object
    :returns: the html after resetting the password
    :rtype: str

    """

    loginPlugin.reset_password(post_get('reset_code'), post_get('password'))
    return 'Thanks. <a href="/login">Go to login</a>'


def index(helper, userName):
    """The home page.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: the html of the home page
    :rtype: str

    """

    address_fields = helper.getCreationFields()
    return template('home.html', address_fields=address_fields)


def get_addresses(helper, userName):
    """The JSON of all addresses for the given user.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: JSON data of all the addresses
    :rtype: str

    """

    addresses = helper.getMultiple(userName=userName)
    jsonAddresses = JSONHelper().encode(addresses)
    return HTTPResponse(jsonAddresses, status=200,
                        header={'Content-Type': 'application/json'})


def post_addresses(helper, userName):
    """Create a new address.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: JSON data indicating success or not
    :rtype: str

    """

    throwAway, newAddress = JSONHelper().decode(request.body.read())

    postId = helper.create(newAddress, userName=userName)
    if postId != -1:
        return HTTPResponse(JSONHelper().encode({'_id': postId}), status=200,
                            header={'Content-Type': 'application/json'})
    else:
        return return_error(400, "Create did not work.")


def put_addresses(helper, userName):
    """Save changes to an address.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: JSON data indicating success or not
    :rtype: str

    """

    ids, decodeds = JSONHelper().decode(request.body.read())

    if helper.updateMultiple(ids, decodeds, userName=userName):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Update did not work.")


def delete_addresses(deleteId, helper, userName):
    """Delete an address.

    :param deleteId: the id of the address to delete
    :type deleteId: str
    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: JSON data indicating success or not
    :rtype: str

    """

    if helper.delete(strToId(deleteId), userName=userName):
        return HTTPResponse(status=200)
    else:
        return return_error(400, "Delete did not work")


def csv_export(helper, userName):
    """Export all addresses in the database as a csv file.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: HTTP response with the csv file download
    :rtype: HTTPResponse

    """

    addresses = helper.getMultiple(userName=userName)
    csvAddresses = CSVHelper().convertToCSV(addresses,
                                            helper.getCreationFields())
    disposition = "attachment;filename=addresses.csv"
    return HTTPResponse(csvAddresses, status=200,
                        header={'Content-Type': 'text/csv',
                                'Content-disposition': disposition})


def christmas_card_csv_export(helper, userName):
    """Export Christmas-approved addresses with applicable fields as a csv.

    :param helper: the helper object to operate on the databaes
    :type helper: DataObject
    :param userName: the user name of the currently logged in user
    :type userName: str
    :returns: HTTP response with the csv file download
    :rtype: HTTPResponse

    """

    addresses = helper.getMultiple(userName, {'send_christmas_card': True})
    csvAddresses = CSVHelper().convertToCSV(addresses,
                                            helper.getChristmasFields())
    disposition = "attachment;filename=christmas_card.csv"
    return HTTPResponse(csvAddresses, status=200,
                        header={'Content-Type': 'text/csv',
                                'Content-disposition': disposition})


#This is really for testing purposes and needs updated to use for real.
#def csv_import(helper, userName):
#    addresses = CSVHelper().convertFromCSV('contacts.csv')
#    atleastOneFailed = False
#    for address in addresses:
#        if helper.create(address, userName=userName) == -1:
#            atleastOneFailed = True
#    if not atleastOneFailed:
#        return HTTPResponse(status=200)
#    else:
#        return return_error(400, "Import did not work.")


def js_static(filename):
    """Get static javascript files.

    :param filename: the name of the javascript file
    :type filename: str
    :returns: The given js file
    :rtype: file

    """

    return static_file(filename, root=os.path.join(MODULEPATH, 'static/js'))


def css_static(filename):
    """Get static css files.

    :param filename: the name of the css file
    :type filename: str
    :returns: The given css file
    :rtype: file

    """

    return static_file(filename, root=os.path.join(MODULEPATH, 'static/css'))


def return_error(status, msg=''):
    """Return a JSON error message.

    :param status: the response code
    :type status: int
    :param msg: the message to return to the user
    :type msg: str
    :returns: The JSON data of the error
    :rtype: str

    """

    json_err = JSONHelper().encode({'error': msg})
    return HTTPResponse(json_err, status=status,
                        header={'Content-Type': 'application/json'})

if __name__ == '__main__':
    ipaddress = "0.0.0.0"
    port = os.environ.get("PORT", 5000)
    AddressServer({"bind": ipaddress + ":" + port, "workers": 3,
                   "proc_name": "simpleaddress", "max_requests": 100,
                   "timeout": 300}).run()
