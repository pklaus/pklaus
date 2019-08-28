"""
Tagesspiegel-paperboy delivers your Tagesspiegel newspaper freshly every day.
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
import stat
import logging
from urllib.parse import urljoin
import re

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-agent', '-ua', required=True, help='User agent you want paperboy to use.')
    parser.add_argument('--output-directory', '-o', required=True, help='Directory to store the PDFs of the downloaded newspaper issues.')
    parser.add_argument('--kundennummer', '-k', required=True, help='Kundennummer (customer number) for your e-paper subscription.')
    parser.add_argument('--plz', '-p', required=True, help='Postleitzahl (ZIP code) for your e-paper subscription.')
    parser.add_argument('--cookie-file', '-c', help='File to store the cookies in.', default='~/.FAZ-paperboy_cookies.txt')
    parser.add_argument('--debug', '-d', action='store_true', help='Increase verbosity.')
    parser.add_argument('--pdf',  action='store_true', help='Download in PDF format.')
    parser.add_argument('--epub', action='store_true', help='Download in ePub format.')
    parser.add_argument('--mobi', action='store_true', help='Download in Mobi format.')

    if not ext_deps: parser.error("Missing at least one of the python modules 'requests' or 'beautifulsoup4'.")

    args = parser.parse_args()

    if args.debug: level = logging.DEBUG
    else: level = logging.INFO
    logging.basicConfig(level=level, format='%(levelname)-8s %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)

    browser = Browser(args.user_agent, os.path.expanduser(args.cookie_file))

    random_sleep()
    index_page = browser.get('http://www.tagesspiegel.de/')
    random_sleep()

    login_page = browser.get('http://abo.tagesspiegel.de/aboangebote/e-paper')
    random_sleep()

    logging.info("Trying to log in.")
    login_data = {
      'form_id': 'epaper',
      'customer_number': args.kundennummer,
      'zip_code': args.plz,
      'submit': ''
    }
    login_answer = browser.post('http://abo.tagesspiegel.de/aboangebote/e-paper', data=login_data)
    random_sleep()

    if not BeautifulSoup(login_answer.text).find('a', href='econtent.php?log=out'):
        logging.error('Incorrect credentials?')
        sys.exit(1)

    # Create output directory if it doesn't exist:
    if not os.path.isdir(args.output_directory):
        os.makedirs(args.output_directory)

    # Download all newspaper issues:
    URLs = []
    if args.pdf:  URLs.append('http://epaper.tagesspiegel.de/epaper/econtent.php?archiv=pdf')
    if args.epub: URLs.append('http://epaper.tagesspiegel.de/epaper/econtent.php?archiv=epub')
    if args.mobi: URLs.append('http://epaper.tagesspiegel.de/epaper/econtent.php?archiv=mobi')

    # Content-Disposition: attachment; filename="TSP-20141207.pdf"
    cd_re = re.compile('filename="(.*)"') # Content-Disposition regex
    for url in URLs:
        random_sleep()
        issues_page = browser.get(url)
        random_sleep()
        issue_links = BeautifulSoup(issues_page.text).select('a.button')
        for issue_link in issue_links:
            random_sleep()
            issue_url = urljoin(url, issue_link['href'])
            issue_response = browser.get(issue_url, stream=True)
            try:
                filename = cd_re.search(issue_response.headers['Content-Disposition']).group(1)
            except (IndexError, AttributeError, KeyError):
                logging.warning('Something wrong with this issue: {} ?'.format(issue_url))
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
