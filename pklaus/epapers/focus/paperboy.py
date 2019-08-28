"""
FOCUS-paperboy delivers your FOCUS e-magazine freshly every week.
"""


try:
    from bs4 import BeautifulSoup
    import requests
    ext_deps = True
except ImportError:
    ext_deps = False
import random
import http.cookiejar
import time
import os
import sys
import logging
from urllib.parse import urljoin
import re


BASE_URL = 'https://focus-epaper.de'
LOGIN_URL = BASE_URL + '/login_check'
ISSUES_URL_TPL = BASE_URL + '/hefte?type=16&page={}'

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-agent', '-ua', required=True, help='User agent you want paperboy to use.')
    parser.add_argument('--output-directory', '-o', required=True, help='Directory to store the PDFs of the downloaded issues.')
    parser.add_argument('--email', '-e', required=True, help='Email address of your account at ' + BASE_URL)
    parser.add_argument('--password', '-p', required=True, help='Password for your account at ' + BASE_URL)
    parser.add_argument('--cookie-file', '-c', help='File to store the cookies in.', default='~/.FOCUS-paperboy_cookies.txt')
    parser.add_argument('--debug', '-d', action='store_true', help='Increase verbosity.')

    if not ext_deps: parser.error("Missing at least one of the python modules 'requests' or 'beautifulsoup4'.")

    args = parser.parse_args()

    if args.debug: level = logging.DEBUG
    else: level = logging.INFO
    logging.basicConfig(level=level, format='%(levelname)-8s %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)

    browser = Browser(args.user_agent, os.path.expanduser(args.cookie_file))

    random_sleep()
    index_page = browser.get(BASE_URL)
    random_sleep()

    if BeautifulSoup(index_page.text, "html.parser").find('a', text='Logout'):
        logging.info("Already logged in.")
    else:
        login_page = index_page
        login_form = BeautifulSoup(login_page.text, "html.parser").find('form')
        assert login_form.get('action') == '/login_check'
        csrf_field = login_form.find('input', type='hidden')
        form_data = {csrf_field['name']: csrf_field['value']}

        login_data = {
          '_username': args.email,
          '_password': args.password,
          '_remember_me': 'on'
        }
        login_data.update(form_data)
        logging.info("Trying to log in.")
        login_answer = browser.post(LOGIN_URL, data=login_data)
        random_sleep()

        if not BeautifulSoup(login_answer.text, "html.parser").find('a', text='Logout'):
            logging.error('Incorrect credentials?')
            sys.exit(1)

    # Create output directory if it doesn't exist:
    if not os.path.isdir(args.output_directory):
        os.makedirs(args.output_directory)

    cd_re = re.compile(r'filename="(.*)"') # Content-Disposition regex

    # Download all issues:
    page = 1
    while True:
        issues_url = ISSUES_URL_TPL.format(page)
        page += 1
        issues_page = browser.get(issues_url)
        issues_page = BeautifulSoup(issues_page.text, "html.parser")
        links = issues_page.find_all('a', href=True)
        links = [link for link in links if link['href'].startswith('/hefte/download/')]
        if not links:
            logging.info('No further download links found on page %d. Quitting.', page)
            break
        for link in links:
            issue_url = BASE_URL + link['href']
            logging.info('Issue URL: %s', issue_url)
            issue_response = browser.get(issue_url, stream=True)
            try:
                filename = cd_re.search(issue_response.headers['Content-Disposition']).group(1)
            except (IndexError, AttributeError, KeyError):
                logging.warning('Something wrong with this issue: {} ?'.format(issue['title']))
                issue_response.close()
                continue
            fullpath = os.path.join(args.output_directory, filename)
            if os.path.exists(fullpath):
                logging.info("{} already downloaded... ".format(filename))
                issue_response.close()
                continue
            logging.info("Downloading {}...".format(filename))
            with open(fullpath, 'wb') as f:
                for chunk in issue_response.iter_content(1024):
                    f.write(chunk)
            issue_response.close()

    browser.close()


class Browser(object):
    def __init__(self, user_agent, cookie_file, store_any_cookie=False):
        self.s = requests.Session()
        self.store_any_cookie = store_any_cookie
        self.cookie_file = cookie_file
        if cookie_file:
            self.s.cookies = http.cookiejar.LWPCookieJar()
            try:
                self.s.cookies.load(cookie_file, ignore_discard=self.store_any_cookie)
            except FileNotFoundError:
                pass
        headers = {
          'User-Agent': user_agent,
          'Dnt': '1',
          'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          'Accept-Encoding': "gzip, deflate",
          'Accept-Language': "en,en-gb;q=0.8,en-us;q=0.5,de;q=0.3"
        }
        self.s.headers.update(headers)
        self.last = None

    def close(self):
        logging.debug("saving cookies")
        try:
            self.s.cookies.save(self.cookie_file, ignore_discard=self.store_any_cookie)
        except:
            pass

    def set_referer(self, func, *args, **kwargs):
        if 'referer' in kwargs:
            headers = { 'Referer': kwargs['referer'] }
            del kwargs['referer']
            if 'headers' in kwargs:
                kwargs['headers'].update(headers)
            else:
                kwargs['headers'] = headers
            return func(*args, **kwargs)

        if self.last:
            headers = { 'Referer': self.last }
            try:
                kwargs['headers'].update(headers)
            except KeyError:
                kwargs['headers'] = headers
        self.last = args[0]
        return func(*args, **kwargs)

    def get(self, *args, **kwargs):
        logging.debug('Browser GET {}'.format(args[0]))
        return self.set_referer(self.s.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        logging.debug('Browser POST {}'.format(args[0]))
        return self.set_referer(self.s.post, *args, **kwargs)


def random_sleep(min_sec=0.6, max_sec=5.3):
    st = random.uniform(min_sec, max_sec)
    logging.debug('Sleep time: {}'.format(st))
    time.sleep(st)
