from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import time
import os

from bs4 import BeautifulSoup
import re
import pandas as pd

import requests
import os
import urllib
from urllib.parse import urlparse

import subprocess

from selenium.common.exceptions import NoSuchElementException


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def sync_get_element_by_xpath(driver, wait, xpath):
    wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
    return driver.find_element_by_xpath(xpath)


def sync_get_elements_by_xpath(driver, wait, xpath):
    wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
    return driver.find_elements_by_xpath(xpath)


def sign_in(driver, wait):
    email = sync_get_element_by_xpath(driver, wait, "//input[@data-testid='signin-email']")
    password = sync_get_element_by_xpath(driver, wait, "//input[@data-testid='signin-password']")

    email.send_keys("huohsien.ai@gmail.com")
    password.send_keys("Huo18941256")

    wait.until(ec.visibility_of_element_located(
        (By.CLASS_NAME, "button_primary__1qhjh.button__btn__2MHEg.form_primary-button__37eaW.button_standard__1p9sb")))
    sign_in_btn = driver.find_element_by_class_name(
        "button_primary__1qhjh.button__btn__2MHEg.form_primary-button__37eaW.button_standard__1p9sb")
    sign_in_btn.click()


def check_lesson_complete(item) -> bool:
    e1 = item.find_element_by_xpath("./div/div")
    c = e1.get_attribute('class')
    if c == 'index--lesson-card--mwX1V index--card--3DZMr shared--card--3X88h':
        return True
    else:
        return False


def expand_all_complete_lessons(driver, wait):
    # click open the ones that were marked Complete
    lessons = sync_get_elements_by_xpath(driver, wait, "//div[@data-test='part-syllabus']/ol/li")
    for lesson in lessons:
        if check_lesson_complete(lesson):
            lesson.click()
    element = driver.find_element_by_xpath("//*[h3='lesson 1']")
    driver.execute_script("return arguments[0].scrollIntoView(true);", element)


#     time.sleep(1)

def embed_tag(tag, html_str):
    return '<{}>'.format(tag) + html_str + '</{}>'.format(tag)


def debug_breakpoint(title, message=None):
    if message == None:
        print(title)
    else:
        input(title + ' - ' + message)


def write_to_clipboard(output):
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))


def download_css_files(driver):
    css_folder_path = os.path.join(root_folder, topic_name, lesson_name, part_name, "css")

    if not os.path.exists(css_folder_path):
        os.makedirs(css_folder_path)

    html_src = driver.page_source
    base = driver.current_url
    soup = BeautifulSoup(html_src)
    css_link_elms = soup.find_all('link', {'rel': 'stylesheet'})

    css_links = []
    for idx, css_link_elm in enumerate(css_link_elms, start=1):
        link = css_link_elm['href']
        if link.startswith('/'):
            link = urllib.parse.urljoin(base, link)
        css_links.append(link)
    #         print(idx, ": ", link)

    for css_link in css_links:
        r = requests.get(css_link, allow_redirects=True)
        a = urlparse(css_link)
        file_name = os.path.basename(a.path)
        file_name = os.path.join(css_folder_path, file_name)
        #         print("file_name= ", file_name)

        open(file_name, 'wb').write(r.content)


def make_images_local(soup):
    global root_folder, topic_name, lesson_name, part_name

    images_folder = os.path.join(root_folder, topic_name, lesson_name, part_name, "img")

    img_elms = soup.find_all('img')
    for img_elm in img_elms:
        img_link = img_elm['src']
        r = requests.get(img_link, allow_redirects=True)
        a = urlparse(img_link)
        file_name = os.path.basename(a.path)
        img_path = "./" + images_folder + "/" + file_name

        if not os.path.exists(images_folder):
            os.makedirs(images_folder)

        open(img_path, 'wb').write(r.content)
        #         print("file_name: ", file_name)
        # replace src in img element
        img_elm['src'] = "./img/{}".format(file_name)


def create_head_str(driver):
    css_folder_path = os.path.join(root_folder, topic_name, lesson_name, part_name, "css")
    css_filenames = [f for f in os.listdir(css_folder_path) if os.path.isfile(os.path.join(css_folder_path, f))]

    page_html = driver.page_source
    page_soup = BeautifulSoup(page_html, 'html.parser')
    style_elms = page_soup.find('head').find_all('style')

    meta_elm = '<meta http-equiv="Content-type" content="text/html; charset=utf-8">'
    head_str = '<head>' + meta_elm
    for css_filename in css_filenames:
        link_str = '<link rel="stylesheet" href="./css/{}">'.format(css_filename)
        head_str = head_str + link_str
    for style_elm in style_elms:
        head_str = head_str + str(style_elm)

    head_str = head_str + '</head>'
    #     print("head_str: ", head_str)
    return head_str


def process_content_html(driver, content_html_str):
    download_css_files(driver)

    head_str = create_head_str(driver)
    body_str = embed_tag('body', content_html_str)
    page_html_str = head_str + body_str
    html_str = embed_tag('html', page_html_str)

    # remove unwanted div element
    soup = BeautifulSoup(html_str, 'html.parser')
    div_to_be_remove_class_name = '_main--notification-bar--2AVbT'
    to_be_removed_elms = soup.find_all('div', class_=div_to_be_remove_class_name)
    for to_be_removed_elm in to_be_removed_elms:
        to_be_removed_elm.decompose()

    make_images_local(soup)

    return soup.prettify()


def copy_youtube_link_to_clipboard(video_link):
    write_to_clipboard(video_link)
    time.sleep(1)


def grab_all_youtube_links(content_html_str, download=False):
    content_soup = BeautifulSoup(content_html_str, 'html.parser')
    youtube_iframe_elms = content_soup.find_all('iframe', {'title': 'YouTube video player'})
    video_links = ''
    for idx, youtube_iframe_elm in enumerate(youtube_iframe_elms, start=1):
        video_link = youtube_iframe_elm['src']
        video_link = video_link + '#index={}_{}_{}_{}'.format(topic_name, lesson_name, part_name, idx)
        video_links = video_links + video_link + '\n\n'
        if download == True:
            copy_youtube_link_to_clipboard()

    #     print(idx, ' : ', video_link)
    #     print(video_links)
    with open('all_youtube_video_links.txt', 'a') as fp:
        fp.writelines(video_links)


def save_processed_html(driver, wait):
    contents = sync_get_elements_by_xpath(driver, wait, "//div[@id='content']")
    assert len(contents) == 1

    content_html = contents[0].get_attribute('outerHTML')
    html_str = process_content_html(content_html)
    grab_all_youtube_links(content_html, False)

    file_name = os.path.join(root_folder, topic_name, lesson_name, part_name, "content.html")
    with open(file_name, 'w') as f:
        f.write(html_str)
#     print("html_str= ", html_str)

