import cookielib
import editor
import re
import threading
import urllib, urllib2

USER_AGENT = "SublimeText2 - %s" % editor.PLUGIN_NAME
LOGIN_URL = "http://www.pythonanywhere.com/login/"
FILES_URL = "http://www.pythonanywhere.com/user/%s/files/%s"
RELOAD_URL = "http://www.pythonanywhere.com/user/%s/webapps/reload"

cookie_handler = urllib2.HTTPCookieProcessor()
opener = urllib2.build_opener(cookie_handler)
opener.addheaders = [('User-Agent', USER_AGENT)]

class BackgroundThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.result = None
        self.error = None
        super(BackgroundThread, self).__init__(*args, target=self.process, **kwargs)

    def run(self, *args, **kwargs):
        try:
            super(BackgroundThread, self).run(*args, **kwargs)
        except Exception, e:
            self.error = e

    def process(self):
        pass

class LoginThread(BackgroundThread):
    def process(self, username, password):
        req = urllib2.Request(LOGIN_URL)
        result = opener.open(req)
        csrftoken = None
        for cookie in cookie_handler.cookiejar:
            if cookie.name == "csrftoken":
                csrftoken = cookie.value

        result = opener.open(LOGIN_URL,
            urllib.urlencode(dict(
                csrfmiddlewaretoken=csrftoken,
                username=username,
                password=password)))

        if result.geturl().startswith(LOGIN_URL):
            cookie_handler.cookiejar.clear()
            raise Exception, "invalid username or password"

class NewFileThread(BackgroundThread):
    def process(self, username, dirname, filename):
        result = opener.open(FILES_URL % (username, dirname),
            urllib.urlencode(dict(filename=filename)))
        check_result(result)

class OpenFileThread(BackgroundThread):
    def process(self, username, file_path):
        result = opener.open(FILES_URL % (username, file_path))
        self.result = check_result(result)

class SaveFileThread(BackgroundThread):
    def process(self, username, file_path, content):
        result = opener.open(FILES_URL % (username, file_path),
            urllib.urlencode(dict(new_contents=content)))
        check_result(result)

class ReloadWbAppsThread(BackgroundThread):
    def process(self, username):
        result = opener.open(RELOAD_URL % username)
        check_result(result)


def is_logged_in():
    return bool(cookie_handler.cookiejar)

def check_result(result):
    if result.geturl().startswith(LOGIN_URL):
        cookie_handler.cookiejar.clear()
        raise Exception, "invalid username or password (cookie expired, relogin please)"
    content = result.read()
    error_match = re.match(r'.*<div.*?id_error_message.*?>(.*?)</div>.*',
        content, re.S)
    if error_match:
        raise Exception, error_match.group(1).strip()
    return content
