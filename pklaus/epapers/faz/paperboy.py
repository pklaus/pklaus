"""
FAZ-paperboy delivers your FAZ or F.A.S. newspaper freshly every day.
"""


try:
    from bs4 import BeautifulSoup
    import requests
    ext_deps = True
except ImportError:
    ext_deps = False
import random
import re
import http.cookiejar
import time
import os
import sys
import stat
import logging

logger = logging.getLogger(__name__)

def logged_in(profile_page_html, fullname):
    # formerly this was:
    #soup = BeautifulSoup(profile_page_html, "html.parser")
    #return len(soup.select('span.Username')) > 1
    return fullname in profile_page_html

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-agent', '-ua', required=True, help='User agent you want paperboy to use.')
    parser.add_argument('--output-directory', '-o', required=True, help='Directory to store the PDFs of the downloaded newspaper issues.')
    parser.add_argument('--fullname', '-f', required=True, help='Full name of the user as shown when logged in to the profile on https://www.faz.net/mein-faz-net/profil/ - used to check if logged in successfully.')
    parser.add_argument('--username', '-u', required=True, help='User name to login at https://faz.net for the e-paper download.')
    parser.add_argument('--password', '-p', required=True, help='Password for user given by --username.')
    parser.add_argument('--cookie-file', '-c', help='File to store the cookies in.', default='~/.FAZ-paperboy_cookies.txt')
    parser.add_argument('--filename-template', '-t', help='Template for the output filenames. By default this is "{isodate}_{orig_newspaper}.pdf". {isodate} is the date in the format YYYY-MM-DD. For the date in the format YYYYMMDD, just use {date}. If you want to use the original filename of the PDFs, you could use "{original}.pdf". For a short version of the newspaper name, there is also {newspaper}.', default='{isodate}_{orig_newspaper}.pdf')
    parser.add_argument('--debug', '-d', action='store_true', help='Increase verbosity.')

    if not ext_deps: parser.error("Missing at least one of the python modules 'requests' or 'beautifulsoup4'.")

    args = parser.parse_args()

    if args.debug: level = logging.DEBUG
    else: level = logging.INFO
    logging.basicConfig(level=level, format='%(levelname)-8s %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)

    browser = Browser(args.user_agent, os.path.expanduser(args.cookie_file))

    random_sleep()
    index_page = browser.get('https://www.faz.net')
    # With the index_page alone we cannot easily find out if we are logged in or not...
    # A JS function replaces the login button by the user name depending on a cookie:
    # function LoginDecorator
    # in http://www.faz.net/5.9.8/js/all_scripts.min.js

    random_sleep()

    login_page = browser.get('https://www.faz.net/mein-faz-net/profil/')

    random_sleep()
    if logged_in(login_page.text, fullname=args.fullname):
        logger.info("Already logged in.")
    else:
        logger.info("Not logged in yet, trying to log in.")
        login_data = {
          'loginName': args.username,
          'loginUrl': '/mein-faz-net/',
          'password': args.password,
          'redirectUrl': '/mein-faz-net/',
          'rememberMe': 'on'
        }
        login_answer = browser.post('https://www.faz.net/membership/loginNoScript', data=login_data)

        login_page = browser.get('https://www.faz.net/mein-faz-net/profil/')
        if args.debug:
            with open('login_page.html', 'w') as f:
                f.write(login_page.text)

        if not logged_in(login_page.text, fullname=args.fullname):
            logger.error('Incorrect credentials?')
            sys.exit(1)

    random_sleep()
    epaper = browser.get('http://epaper.faz.net/')
    epaper = BeautifulSoup(epaper.text, "html.parser")

    newspapers = ('FAZ', 'WOCHE', 'FAS') # in the order in which they are listed on the page
    issues = []
    for i, newspaper in enumerate(newspapers):
        for dropdown in epaper.select('.dropdown-issues-list')[i].select('li a'):
            if dropdown['data-slug'] != newspaper:
                logger.warning("Strange dropdown item: " + str(dropdown))
                continue
            releaseDate = dropdown['data-release-date']
            data = {
              'releaseDate': releaseDate,
              'slug':        newspaper,
            }
            issue_answer = browser.post_json('http://epaper.faz.net/api/epaper/change-release-date', json=data)
            soup = BeautifulSoup(issue_answer['htmlContent'], "html.parser")
            main_issue = soup.select('div.newspaper.main-issue')
            if len(main_issue) != 1:
                logger.warning("Strange content for this issue: {} - {}?".format(newspaper, releaseDate))
                for line in str(soup).split('\n'): logger.debug(line)
                continue
            soup = main_issue[0]
            links = soup.findAll('a', href=re.compile('webreader'))
            if len(links) != 1:
                logger.warning("No subscription for this issue: {} - {}?".format(newspaper, releaseDate))
                continue
            link = links[0]['href']
            link = link.split('/')[2]
            issues.append({'newspaper': newspaper, 'link': link, 'releaseDate': releaseDate})

    # Create output directory if it doesn't exist:
    if not os.path.isdir(args.output_directory):
        os.makedirs(args.output_directory)

    # Download all newspaper issues:
    cd_re = re.compile(r'filename="(.*)"') # Content-Disposition regex
    random_sleep()
    for issue in issues:

        pdf_url = 'http://epaper.faz.net/epaper/download/{}'.format(issue['link'])
        pdf_response = browser.get(pdf_url, stream=True)

        try:
            orig_filename = cd_re.search(pdf_response.headers['Content-Disposition']).group(1)
        except (IndexError, AttributeError, KeyError):
            logger.warning('Something wrong with this issue: {} ?'.format(issue))
            pdf_response.close()
            continue

        date = ''.join(reversed(issue['releaseDate'].split('.')))
        isodate = '-'.join(reversed(issue['releaseDate'].split('.')))
        original = os.path.splitext(orig_filename)[0]
        match = re.match('^([^\d]*)-\d{2}\.\d{2}\.\d{4}$', original)
        if match:
            orig_newspaper = match.group(1)
        else:
            logger.warn("Couln't match the original filename. Please report this issue to the author.")
            logger.warn("Setting orig_newspaper = original = " + original)
            orig_newspaper = original
        filename = args.filename_template.format(newspaper=issue['newspaper'], isodate=isodate, date=date, original=original, orig_newspaper=orig_newspaper)
        fullpath = os.path.join(args.output_directory, filename)

        if os.path.exists(fullpath):
            logger.info("{} already downloaded.".format(filename))
            pdf_response.close()
            continue

        logger.info("Downloading {}...".format(orig_filename))
        if filename != orig_filename:
            logger.info("...saving as {}".format(filename))
        with open(fullpath, 'wb') as f:
            for chunk in pdf_response.iter_content(1024):
                f.write(chunk)
        pdf_response.close()

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
        logger.debug("saving cookies")
        try:
            self.s.cookies.save(self.cookie_file, ignore_discard=self.store_any_cookie)
        except:
            pass

    def post_json(self, *args, **kwargs):
        # Different headers for json requests:
        headers = {
          'Accept': 'application/json, text/javascript, */*; q=0.01',
          'X-Requested-With': 'XMLHttpRequest',
          'Connection': 'keep-alive',
        }
        try:
            kwargs['headers'].update(headers)
        except KeyError:
            kwargs['headers'] = headers
        return self.post(*args, **kwargs).json()

    def get_json(self, *args, **kwargs):
        # Different headers for json requests:
        headers = {
          'Accept': 'application/json, text/javascript, */*; q=0.01',
          'X-Requested-With': 'XMLHttpRequest',
          'Connection': 'keep-alive',
        }
        try:
            kwargs['headers'].update(headers)
        except KeyError:
            kwargs['headers'] = headers
        return self.get(*args, **kwargs).json()

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
        logger.debug('Browser GET {}'.format(args[0]))
        return self.set_referer(self.s.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        logger.debug('Browser POST {}'.format(args[0]))
        return self.set_referer(self.s.post, *args, **kwargs)


def random_sleep(min_sec=0.6, max_sec=5.3):
    st = random.uniform(min_sec, max_sec)
    logger.debug('Sleep time: {}'.format(st))
    time.sleep(st)
