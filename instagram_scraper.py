import calendar
import json
import os
import random
import re
import signal
import sys

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import DesiredCapabilities, ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from datetime import datetime
from time import mktime
import time
from selenium import webdriver
from .cleanse_text import cleanse_text


class InstagramScraper:

    def __init__(self, db_connection=None, ):
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36']
        self.date_format = '%Y-%m-%d %H:%M:%S'
        self.driver = None
        if db_connection:
            self.db_connection = db_connection

    def instagram_login(self, insta_username, insta_password):
        print("inside instagram_login")
        sys.stdout.flush()
        try:
            self.driver.get("http://www.instagram.com")
            try:
                username = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
                password = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
            except Exception:
                self.driver.get("http://www.instagram.com")
                username = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
                password = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
            # enter username and password
            username.clear()
            username.send_keys(insta_username)
            password.clear()
            password.send_keys(insta_password)
            # target the login button and click it
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            # handle NOT NOW
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))).click()
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))).click()
            except:
                pass
        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("Unable to login: " + str(e))
            sys.stdout.flush()

    def search_keyword(self, keyword):
        try:
            # target the search input field
            print("searching keyword :#", keyword)
            sys.stdout.flush()
            searchbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search']")))
            searchbox.clear()
            # search for the hashtag cat
            keyword = "#" + keyword
            searchbox.send_keys(keyword)
            # Wait for 5 seconds
            time.sleep(5)
            searchbox.send_keys(Keys.ENTER)
            time.sleep(5)
            searchbox.send_keys(Keys.ENTER)
            time.sleep(5)
        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("Unable to login: " + str(e))
            sys.stdout.flush()

    def local_to_utc(self, t):
        secs = time.mktime(t)
        return time.gmtime(secs)

    def utc_to_local(self, t):
        secs = calendar.timegm(t)
        return time.localtime(secs)

    def search_posts_by_keyword(self, keyword, since, max_posts, user=None):
        instagram_posts = []
        grid_url = "http://hub:4444/wd/hub"

        try:
            # auth_obj_db = self.get_auth_object_from_db(since)
            if user[3] is None or not user[3]:
                self.driver = webdriver.Remote(grid_url, DesiredCapabilities.CHROME)
                self.driver.set_page_load_timeout(30)
                print("username")
                print(user[1])
                sys.stdout.flush()
                self.instagram_login(user[1], user[2])
                print("session id in login")
                print(self.driver.session_id)
                sys.stdout.flush()
                mutable_auth_obj = (
                    user[0], user[1], user[2], self.driver.session_id, user[4],
                    user[5],
                    self.driver.command_executor._url)
                self.sql_update_instagram_login(mutable_auth_obj)
            else:
                try:
                    print("username")
                    print(user[1])
                    sys.stdout.flush()
                    self.driver = self.create_driver_session(user[3], user[6])
                    self.driver.set_page_load_timeout(30)
                    print("session id in reuse")
                    print(self.driver.session_id)
                    sys.stdout.flush()
                except:
                    self.driver = webdriver.Remote(grid_url, DesiredCapabilities.CHROME)
                    self.driver.set_page_load_timeout(30)
                    print("username")
                    print(user)
                    sys.stdout.flush()
                    self.instagram_login(user[1], user[2])
                    print("session id in login")
                    print(self.driver.session_id)
                    sys.stdout.flush()
                    mutable_auth_obj = (
                        user[0], user[1], user[2], self.driver.session_id, user[4],
                        user[5],
                        self.driver.command_executor._url)
                    self.sql_update_instagram_login(mutable_auth_obj)
            try:
                self.search_keyword(keyword)
                if len(self.driver.find_elements_by_xpath('//div[contains(string(), "No results found")]')) > 0:
                    print("invalid hashtag")
                    sys.stdout.flush()
                    return []
            except:
                self.driver = webdriver.Remote(grid_url, DesiredCapabilities.CHROME)
                self.driver.set_page_load_timeout(30)
                print("username")
                print(user[1])
                sys.stdout.flush()
                self.instagram_login(user[1], user[2])
                print("session id in login")
                print(self.driver.session_id)
                sys.stdout.flush()
                mutable_auth_obj = (
                    user[0], user[1], user[2], self.driver.session_id, user[4],
                    user[5],
                    self.driver.command_executor._url)
                self.sql_update_instagram_login(mutable_auth_obj)
                self.search_keyword(keyword)
            if len(self.driver.find_elements_by_xpath('//div[contains(string(), "No results found")]')) > 0:
                print("invalid hashtag")
                sys.stdout.flush()
                return []
            # posts
            posts = set()
            match = True
            try:
                most_recent_element = self.driver.find_element_by_xpath('//h2[contains(text(), "Most recent")]')
                desired_y = (most_recent_element.size['height'] / 2) + most_recent_element.location['y']
                window_h = self.driver.execute_script('return window.innerHeight')
                window_y = self.driver.execute_script('return window.pageYOffset')
                current_y = (window_h / 2) + window_y
                scroll_y_by = desired_y - current_y
                self.driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
            except NoSuchElementException:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
            scrolldown = self.driver.execute_script("var scrolldown=document.body.scrollHeight;return scrolldown;")
            time.sleep(2)
            while (match == True) and (len(posts) < max_posts):
                last_count = scrolldown
                time.sleep(3)
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                scrolldown = self.driver.execute_script("var scrolldown=document.body.scrollHeight;return scrolldown;")
                if last_count == scrolldown:
                    match = False
                links = set()
                random_links = set()
                try:
                    [
                        links.add(elem) for elem in
                        self.driver.find_elements_by_tag_name('a')
                    ]
                except:
                    try:
                        self.driver.find_element_by_tag_name('body').send_keys(Keys.ARROW_DOWN)
                        [
                            links.add(elem) for elem in
                            self.driver.find_elements_by_tag_name('a')
                        ]
                    except Exception as e:
                        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
                        print("ERROR: " + str(e))
                        sys.stdout.flush()
                        continue

                for link in links:
                    if '/p/' in link.get_attribute('href'):
                        posts.add(link)
                    else:
                        random_links.add(link)

                for idx, postlink in enumerate(posts):
                    try:
                        # create action chain object
                        action = ActionChains(self.driver)
                        # context click the item
                        action.context_click(on_element=postlink)
                        post_linkurl = postlink.get_attribute("href")
                        self.driver.execute_script("window.open('');")
                        sleeptime = random.uniform(0.5, 1.5)
                        time.sleep(sleeptime)
                        handles = self.driver.window_handles
                        newHandle = handles[1]
                        self.driver.switch_to.window(newHandle)
                        try:
                            self.driver.get(post_linkurl)
                        except:
                            continue
                        time.sleep(random.uniform(3, 5))
                        post_valid, post = self.parse_post_data(keyword, since, post_linkurl)
                        if post_valid:
                            instagram_posts.append(post)
                            print(post)
                            sys.stdout.flush()
                        self.driver.close()
                        self.driver.switch_to.window(handles[0])
                    except Exception as e:
                        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
                        print("Continue to next post")
                        continue
                        sys.stdout.flush()

        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("Error in getting posts" + str(e))
            sys.stdout.flush()
        print("No of posts returned: %d " % len(instagram_posts))
        sys.stdout.flush()
        return instagram_posts

    def parse_post_data(self, keyword, since, posturl):
        try:
            post = dict()
            post_valid = False
            html = self.driver.page_source
            if "window.__additionalDataLoaded(" not in html:
                for x in range(5):
                    self.driver.get(posturl)
                    time.sleep(5)
                    html = self.driver.page_source
                    if "window.__additionalDataLoaded(" in html:
                        break
                    else:
                        if x == 4:
                            return post_valid, post
            if "window.__additionalDataLoaded(" in html:
                parameters = html.split("window.__additionalDataLoaded(")[1].split(");</script>")[0]
                if parameters and "," in parameters:
                    shared_data = parameters.split(",", 1)[1]
                    post_data = json.loads(shared_data)
                    post["id"] = post_data["graphql"]["shortcode_media"]["id"]
                    post["id_shortcode"] = post_data["graphql"]["shortcode_media"]["shortcode"]
                    post["link"] = "https://www.instagram.com/p/" + post["id_shortcode"]
                    post["username"] = post_data["graphql"]["shortcode_media"]["owner"]["username"]
                    post["user_id"] = post_data["graphql"]["shortcode_media"]["owner"]["id"]
                    post["date_local"] = datetime.fromtimestamp(
                        post_data["graphql"]["shortcode_media"]["taken_at_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    post["datestamp_local"] = datetime.fromtimestamp(
                        post_data["graphql"]["shortcode_media"]["taken_at_timestamp"]).strftime("%Y-%m-%d")
                    post["timestamp_local"] = datetime.fromtimestamp(
                        post_data["graphql"]["shortcode_media"]["taken_at_timestamp"]).strftime("%H:%M:%S")
                    utc_date = datetime.fromtimestamp(mktime(self.local_to_utc(
                        datetime.fromtimestamp(
                            post_data["graphql"]["shortcode_media"]["taken_at_timestamp"]).timetuple())))
                    post["date"] = utc_date.strftime("%Y-%m-%d %H:%M:%S")
                    sincedateobject = datetime.strptime(str(since), self.date_format)
                    timedifference = utc_date - sincedateobject
                    minutes = timedifference.total_seconds() / 60
                    if minutes < 0:
                        return post_valid, post
                    post["datestamp"] = utc_date.strftime("%Y-%m-%d")
                    post["timestamp"] = utc_date.strftime("%H:%M:%S")
                    post["created_at"] = int(utc_date.strftime('%s')) * 1000
                    post["image_url"] = post_data["graphql"]["shortcode_media"]["display_url"]
                    if post["image_url"] is not None:
                        post["image_url"] = post["image_url"].replace("https", "http")
                    post['image_path'] = None
                    post['image_paths'] = None
                    if "location" in post_data["graphql"]["shortcode_media"]:
                        if post_data["graphql"]["shortcode_media"]["location"] is not None:
                            post["location_id"] = post_data["graphql"]["shortcode_media"]["location"]["id"]
                            post["location"] = post_data["graphql"]["shortcode_media"]["location"]["name"]
                    try:
                        post["post"] = \
                            post_data["graphql"]["shortcode_media"]["edge_media_to_caption"]["edges"][0]["node"][
                                "text"]
                    except KeyError:
                        post["post"] = " "
                    post["mentions"] = []
                    post["hashtags"] = []
                    post["hashtags_processed"] = []
                    if post["post"]:
                        mention_regex = re.compile(r"(?:@)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
                        try:
                            tagged_users = [edge['node']['user']['username'].lower() for edge in
                                            post_data["graphql"]["shortcode_media"]["edge_media_to_tagged_user"][
                                                "edges"]]
                        except KeyError:
                            tagged_users = []
                        post["mentions"] = list(
                            set(re.findall(mention_regex, post["post"].lower())).union(set(tagged_users)))
                        hashtag_regex = re.compile(r"(?:#)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
                        post["hashtags"] = re.findall(hashtag_regex, post["post"].lower())
                        post['hashtags_processed'] = [" ".join(x.replace("_", " ").split()) for x in post["hashtags"]]
                    try:
                        post["video_url"] = post_data["graphql"]["shortcode_media"]["video_url"]
                    except KeyError:
                        post["video_url"] = ""
                    post["video_path"] = None
                    try:
                        post["likes_count"] = int(
                            post_data["graphql"]["shortcode_media"]["edge_media_preview_like"]["count"])
                    except KeyError:
                        post["likes_count"] = 0
                        try:
                            comments = post_data["graphql"]["shortcode_media"].get("edge_media_to_parent_comment")
                            if comments and "count" in comments:
                                post["comments_count"] = int(comments["count"])
                            else:
                                comments = post_data["graphql"]["shortcode_media"].get("edge_media_preview_comment")
                                if comments and "count" in comments:
                                    post["comments_count"] = int(comments["count"])
                        except KeyError:
                            post["comments_count"] = 0
                    user_object = dict()
                    user = post_data["graphql"]["shortcode_media"].get('owner')
                    if user:
                        if "id" in user:
                            user_object["id"] = user["id"]
                        if "profile_pic_url" in user:
                            user_object["profile_image_url"] = user["profile_pic_url"]
                        if "username" in user:
                            user_object["username"] = user["username"]
                        if "edge_followed_by" in user:
                            user_object["followers"] = int(user["edge_followed_by"]["count"])
                        if "edge_owner_to_timeline_media" in user:
                            user_object["media_count"] = int(user["edge_owner_to_timeline_media"]["count"])
                        user_object["is_private"] = user["is_private"]
                        user_object["following"] = 0
                        user_object["external_url"] = ""
                        post["user_object"] = user_object
                    post["keyword"] = keyword
                    try:
                        post["image_urls"] = [post["image_url"]]
                    except:
                        post["image_urls"] = []
                    dict_hash = {post['hashtags'][idx]: post['hashtags_processed'][idx] for idx in
                                 range(len(post['hashtags']))}
                    dict_ment = {post['mentions'][idx]: " ".join(post['mentions'][idx].replace("_", " ").split()) for
                                 idx in
                                 range(len(post['mentions']))}
                    post['text'] = cleanse_text(post["post"], dict_hash, dict_ment, True)
                    if post_data["graphql"]["shortcode_media"]["__typename"] == "GraphSidecar":
                        if 'edge_sidecar_to_children' in post_data["graphql"]["shortcode_media"]:
                            if 'edges' in post_data["graphql"]["shortcode_media"]['edge_sidecar_to_children']:
                                for edge in post_data["graphql"]["shortcode_media"]['edge_sidecar_to_children'][
                                    "edges"]:
                                    if not edge["node"]["is_video"]:
                                        img_url = edge["node"]["display_url"].replace("https", "http")
                                        post["image_urls"].append(img_url)
                    post["video_path"] = None
                    post_valid = True
            else:
                print("Unable to find additionalDataLoaded object")
                sys.stdout.flush()
        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("Error on line {}".format(str(e)))
            sys.stdout.flush()
        return post_valid, post

    def quit_driver_and_pickup_children(self):
        self.driver.quit()
        try:
            pid = True
            while pid:
                pid = os.waitpid(-1, os.WNOHANG)
                try:
                    if pid[0] == 0:
                        pid = False
                except Exception as e:
                    print(str(e))
                    pass

        except Exception as e:
            print(str(e))
            pass

    def quit_driver(self):
        if self.driver is None:
            return
        self.driver.quit()

    def kill_process(self):
        try:
            # iterating through each instance of the process
            for line in os.popen("ps -eo pid,etime,command | grep chrome | grep -v grep | awk '{print $1, $2, $3}'"):
                fields = line.split()
                # extracting Process ID from the output
                pid = fields[0]
                time_arr = fields[1].split(":")
                # terminating process
                if len(fields[1].split(":")) > 2:
                    if int(time_arr[0]) > 6:
                        self.quit_driver_and_pickup_children()
                        os.kill(int(pid), signal.SIGKILL)
                        print("Process Successfully terminated")
        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("kill_process ERROR: " + str(e))

    def tearDown(self):
        if self.driver is None:
            return
        self.quit_driver_and_pickup_children()
        # self.kill_process()

    def sql_instagram_logins_fetch(self, interval=None):
        try:
            con = self.db_connection
            cursor_obj = con.cursor()
            if interval is None:
                cursor_obj.execute('SELECT * FROM instagramlogin')
            else:
                query_string = """SELECT * FROM instagramlogin where scraping_interval_range = ? """
                interval = self.sanitize_data(interval)
                cursor_obj.execute(query_string, (interval,))
            rows = cursor_obj.fetchall()
            return rows
        except Exception as e:
            print("Error in getting from db" + str(e))
            sys.stdout.flush()

    def get_auth_object_from_db(self, since):
        print("getting auth from db")
        sys.stdout.flush()
        instagram_logins = self.sql_instagram_logins_fetch()
        for login in instagram_logins:
            valid = self.check_interval_valid(since, login[4], login[5])
            if valid:
                print("valid user ", login[1])
                sys.stdout.flush()
                return login
            else:
                mutable_auth_obj = (login[0], login[1], login[2], "", login[4], login[5], "")
                self.sql_update_instagram_login(mutable_auth_obj)
        print("no valid user found")
        sys.stdout.flush()
        return None

    def sanitize_data(self, data):
        if data is not None:
            return str(re.sub(r"[\"\';\n]", "", data))
        return ""

    def sql_update_instagram_login(self, auth_object):
        con = self.db_connection
        cursor_obj = con.cursor()
        query_string = """UPDATE instagramlogin SET session = ?, executor_url = ? where username = ? """

        session = self.sanitize_data(auth_object[3])
        executor_url = self.sanitize_data(auth_object[6])
        username = self.sanitize_data(auth_object[1])

        cursor_obj.execute(query_string, (session, executor_url,
                                          username,))
        con.commit()

    def get_interval(self, since):
        interval_range = ["1-2", "3-4"]
        sincedateobject = datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')
        date_string = (datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%Y") + "-" + (
            datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%m") + "-" + (
                          datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%d")
        for _ in interval_range:
            if "1-2" in interval_range:
                interval_max_string = date_string + " " + "12:00:00"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes > 0:
                    return "1-2"
            if "3-4" in interval_range:
                interval_max_string = date_string + " " + "22:59:00"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes > 0:
                    return "3-4"

    def check_interval_valid(self, since, interval_range, interval):
        sincedateobject = datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')
        interval_max_string = (datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%Y") + "-" + (
            datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%m") + "-" + (
                                  datetime.strptime(str(since), '%Y-%m-%d %H:%M:%S')).strftime("%d")
        if "1-2" in interval_range:
            if interval == 1:
                interval_max_string = interval_max_string + " " + "06:00:00"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes < 0:
                    return False
                else:
                    return True
            else:
                interval_max_string = interval_max_string + " " + "12:00:00"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes < 0:
                    return False
                else:
                    return True
        if "3-4" in interval_range:
            if interval == 1:
                interval_max_string = interval_max_string + " " + "18:00:00"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes < 0:
                    return False
                else:
                    return True
            if interval == 2:
                interval_max_string = interval_max_string + " " + "23:59:59"
                interval_max = datetime.strptime(interval_max_string, '%Y-%m-%d %H:%M:%S')
                timedifference = interval_max - sincedateobject
                minutes = timedifference.total_seconds() / 60
                if minutes < 0:
                    return False
                else:
                    return True

    def create_driver_session(self, session_id, executor_url):
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
        org_command_execute = RemoteWebDriver.execute

        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return org_command_execute(self, command, params)

        RemoteWebDriver.execute = new_command_execute

        new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        new_driver.session_id = session_id

        RemoteWebDriver.execute = org_command_execute

        return new_driver
