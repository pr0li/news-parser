#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import unicodedata
import time
from shutil import rmtree
from datetime import datetime
from pymongo import MongoClient
from urllib import FancyURLopener
from bs4 import BeautifulSoup
from selenium import webdriver
import subprocess


# Get a dictionary {word, count} with
# words that already exist in the DB
#######################################
def get_dict_of_words_from_db(database, collection):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    cursor = coll.find()

    result = dict()
    for doc in cursor:
        result[doc['word']] = doc['count']

    return result
#######################################


# Retrieve urls that have already been parsed, from Mongo DB
#################################################################
def get_visited_urls_from_db(database, collection):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    cursor = coll.find()

    result = set()
    for doc in cursor:
        result.add(doc['url'])

    return result
#################################################################


# Get all hrefs from newspaper's main page and
# keep only those that correspond to articles
#######################################################################
def get_news_hrefs_from_main_page(url):
    try:
        if 'infobae' in url:
            return get_infobae_hrefs_from_main_page(url)
        elif 'clarin' in url:
            return get_clarin_hrefs_from_main_page(url)
        else:
            raise
    except:
        raise
#######################################################################


# Get all hrefs for articles from Infobae news site,
# from the main page
#######################################################################
def get_infobae_hrefs_from_main_page(url):
    DOMAIN = 'http://www.infobae.com'
    class MyOpener(FancyURLopener):
        version = 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'

    opener = MyOpener()
    try:
        html = opener.open(url).read()
    except:
        print 'ERROR: Could not read main site'
        raise

    soup = BeautifulSoup(html, 'lxml')
    tags = soup.find_all('div', class_="lazy-wrapper photo-wrapper")
    urls = get_href_from_tags(tags, DOMAIN)

    tags = soup.find_all('h4', class_="left")
    urls = urls.union(get_href_from_tags(tags, DOMAIN))

    return urls
#######################################################################


# Get all hrefs for articles from Clarin news site,
# from the main page
#######################################################################
def get_clarin_hrefs_from_main_page(url):
    DOMAIN = 'http://www.clarin.com'
    try:
        driver = webdriver.Chrome()
        driver.get(url)

        scroll_opened_web_page(driver)

        html = driver.page_source
        driver.close()
    except:
        print 'ERROR: Could not read main site'
        raise

    urls = set()
    soup = BeautifulSoup(html, 'lxml')
    tags = soup.find_all('article')

    urls = get_href_from_tags(tags, DOMAIN)

    return urls
#######################################################################


# Scroll webpage so that dynamic
# elements are loaded
##########################################
def scroll_opened_web_page(driver):
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
##########################################


# Get hrefs from html tags obtained
# by using BeautifulSoup
###############################################
def get_href_from_tags(tags, domain=''):
    urls = set()

    for elem in tags:
        a = elem.find('a')
        if a is None:
            continue
        href = a['href']
        if not ((len(domain) != 0) != (href[0] != '/')): #logic XOR
            continue
        urls.add(domain + href)

    return urls
###############################################


# Gets a set of words from a text file.
# 'mode' allows for 4 possible combinations:
#
# Least significant bit:
# 0: Part of Speech Tagger (PoS): keep only nouns and adjectives, discard the rest
# 1: Named Entity Recognizer (NER): keep names, places or organizations
#
# Most significant bit:
# 0: Parse the entire text (header, subheader, article)
# 1: Parse the header only
#############################################################################
def get_set_of_words_from_news(url, filename, read_dir, dic, mode):
    POS_DIR = 'stanford-postagger-full-2016-10-31'
    POS_SH_FILE = 'stanford-postagger.sh'
    NER_DIR = 'stanford-ner-2016-10-31'
    NER_SH_FILE = 'ner.sh'
    TEMP_FILE = 'temp.txt'
    OUT_FILE = 'infobout.txt'

    try:
        news_buf = read_news_from_file(filename, read_dir, (mode & 0b10) != 0)
    except:
        raise

    orig_wd = os.getcwd()
    if (mode & 0b01) == 0:
        new_wd = POS_DIR
        run_file = POS_SH_FILE
        delimiter = '_'
        tags = '[na]'
    else:
        new_wd = NER_DIR
        run_file = NER_SH_FILE
        delimiter = '/'
        tags = '(?:P|L|OR)'

    os.chdir(new_wd)

    with open(TEMP_FILE, 'w') as f:
        f.write(news_buf)

	# Call external java parser
    try:
        with open(OUT_FILE, 'w') as fa:
            subprocess.check_call(['./' + run_file, TEMP_FILE], stdout=fa)
    except:
        os.chdir(orig_wd)
        raise

    with open(OUT_FILE, 'r') as fb:
        news_buf = fb.read()

    os.chdir(orig_wd)

    return get_set_of_words_from_tagged_buf(news_buf, dic, delimiter, tags)
#############################################################################


# Read news content from a file in disk
###########################################################
def read_news_from_file(filename, read_dir, header_only):
    try:
        with open(read_dir + '/' + filename, 'r') as f:
            if header_only:
                buf = f.readline()
            else:
                buf = f.read()
    except:
        raise

    return buf
###########################################################


# Get the text for a URL with a news article.
# Parsing method is different for each news site.
########################################################
def get_news_text(url):
    try:
        if 'infobae' in url:
            return get_infobae_news_text(url)
        elif 'clarin' in url:
            return get_clarin_news_text(url)
        else:
            raise
    except:
        raise
########################################################


# Get the text for a URL with a news article,
# from Infobae news site.
########################################################
def get_infobae_news_text(url):
    class MyOpener(FancyURLopener):
        version = 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'

    opener = MyOpener()
    try:
        html = opener.open(url).read()
    except:
        print 'ERROR: Could not read url'
        raise

    soup = BeautifulSoup(html, 'lxml')

    header = soup.find('h1')
    subheader = header.find_next_sibling('span')
    body = soup.find_all('p', class_='element element-paragraph')

    buf_ret = header.text.encode('utf-8')
    buf_ret = buf_ret + '\n' + subheader.text.encode('utf-8')

    for p in body:
        buf_ret = buf_ret + '\n' + p.text.encode('utf-8')

    return buf_ret
########################################################


# Get the text for a URL with a news article,
# from Clarin news site.
########################################################
def get_clarin_news_text(url):
    class MyOpener(FancyURLopener):
        version = 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'

    opener = MyOpener()
    try:
        html = opener.open(url).read()
    except:
        print 'ERROR: Could not read url'
        raise

    soup = BeautifulSoup(html, 'lxml')

    header = soup.find('h1')
    subheader = header.find_next_sibling('div')
    body = soup.find(itemprop="articleBody").find_all('p', recursive=False)

    buf_ret = header.text.encode('utf-8')
    buf_ret = buf_ret + '\n' + subheader.text.encode('utf-8')

    for p in body:
        buf_ret = buf_ret + '\n' + p.text.encode('utf-8')

    return buf_ret
########################################################


# Read the text corresponding to each URL
# and write the contents to a file in write_to_dir
########################################################
def write_news_to_file(urls, write_to_dir):
    FILE_EXT = '.txt'
    index = 0
    dict_urls = dict()

    if not os.path.exists(write_to_dir):
        os.makedirs(write_to_dir)

    for url in urls:
        try:
            news_text = get_news_text(url)
        except:
            continue
        print 'Writing %s news body to disk\n' % url
        filename = str(index).zfill(3) + FILE_EXT
        with open(write_to_dir + '/' + filename, 'w') as f:
            f.write(news_text)

        dict_urls[url] = filename
        index = index + 1

    return dict_urls
########################################################


# Parse a buffer that has been tagged by either NER or PoS.
# New words are added to the dictionary 'dic', existent words
# increment count of {word,count}
###################################################################
def get_set_of_words_from_tagged_buf(buf, dic, delimiter, tags):
    hashset = set()

    lst = re.findall('([a-zA-ZáéíóúüÁÉÍÓÚÜñÑ]+)' + delimiter + tags, buf)

    for candidate in lst:
        word = candidate.strip()
        try:
            normalized = replace_tildes(word).lower()
        except:
            continue

        hashset.add(normalized)
        if normalized in dic:
            dic[normalized] = dic[normalized] + 1
        else:
            dic[normalized] = 1

    return hashset
###################################################################


# This is specific to spanish language:
# Replaces letters that have tildes with their
# corresponding vowels. 
# It keeps 'ñ' letters though, as they might be of interest
#
# Also, words are converted to lowercase
############################################################
def replace_tildes(word_orig):
    try:
        word = unicode(word_orig.decode('utf8'))
    except:
        raise

    if u'Ñ' in word:
        word = word.replace(u'Ñ', u'ñ')

    last = 0
    enies = []
    while word.find(u'ñ', last) != -1:
        last = word.find(u'ñ')
        enies.append(last)
        last = last + 1

    s = ''.join((c for c in unicodedata.normalize('NFD', word) if unicodedata.category(c) != 'Mn'))

    for n in enies:
        s = s[:n] + u'ñ' + s[n+1:]

    return s
############################################################


# Parses text files with news articles, tags words according
# with 'mode' and saves new words to Mongo DB
#################################################################
def parse_news_into_db(database, collection, urls_dict, read_dir, mode):
    loaded_dict = get_dict_of_words_from_db(database, collection)
    loaded_words = set(loaded_dict.keys())

    new_words = set()
    for url in urls_dict.keys():
        print 'Processing URL: ' + url
        try:
            new_words = new_words.union(get_set_of_words_from_news(url, urls_dict[url], read_dir, loaded_dict, mode))
        except:
            print 'ERROR: could not read news from file... moving on to the next one'
            continue

    update_words = new_words.intersection(loaded_words)
    update_counts_of_words_in_db(database, collection, update_words, loaded_dict)

    loaded_words = new_words.difference(loaded_words)
    insert_new_words_in_db(database, collection, loaded_words, loaded_dict)

    return (len(new_words), len(loaded_words))
#################################################################


# Update count for words in DB that are repeated
####################################################
def update_counts_of_words_in_db(database, collection, words, dic):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    for word in words:
        selector = {"word" : word}
        update_val = {"count" : dic[word]}

        result = coll.update_one(selector, {"$set" : update_val})
####################################################


# Insert new words into DB
#################################################
def insert_new_words_in_db(database, collection, words, dic):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    lst = list()
    for word in words:
        lst.append({"word" : word, "count" : dic[word]})

    if len(lst) > 0:
        result = coll.insert_many(lst)
#################################################


# Insert new URLs that have been processed into DB
#####################################################
def insert_new_urls_in_db(database, collection, urls):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    lst = list()
    for url in urls:
        lst.append({"url" : url})

    if len(lst) > 0:
        result = coll.insert_many(lst)
#####################################################


# Save log into DB with count of new words added,
# for each method, and urls processed
#################################################
def save_log_to_database(database, collection, words_coll, count_urls, count_words, error):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    insertion = dict({'date' : datetime.now(), 'urls' : count_urls, 'error' : error})

    for i in range(len(count_words)):
        insertion[words_coll[i]] = count_words[i]

    result = coll.insert_one(insertion)
#################################################


# Main routine that parses news
# for specified url and saves words to database
#############################################################################
def parse_news(database, main_url):
    COLLECTION_URLS = 'urls'
    COLLECTION_WORDS = ['words_all', 'words_names', 'words_headlines', 'words_names_hdl']
    COLLECTION_LOG = 'logs'
    TEMP_DIR = 'temp_news'
    ERROR_STATE = 0

    loaded_urls = get_visited_urls_from_db(database, COLLECTION_URLS)

    urls = set()
    total_added_words = [0]*len(COLLECTION_WORDS)
    try:
        urls = get_news_hrefs_from_main_page(main_url)
        urls = urls.difference(loaded_urls)
        print 'Loaded %d new URLs\n' % len(urls)
    except:
        ERROR_STATE = 1

    if ERROR_STATE == 0:
        dict_urls = write_news_to_file(urls, TEMP_DIR)

        for i in range(len(COLLECTION_WORDS)):
            (num_processed, num_added)= parse_news_into_db(database, COLLECTION_WORDS[i], dict_urls, TEMP_DIR, i)
            print '\n%s: Processed %d words; Added %d words\n' % (COLLECTION_WORDS[i], num_processed, num_added)
            total_added_words[i] = num_added

        insert_new_urls_in_db(database, COLLECTION_URLS, dict_urls.keys())

        print '\nProcess finished successfully: Parsed %d news' % len(dict_urls.keys())

        try:
            rmtree(TEMP_DIR)
        except:
            pass

    else:
        print 'Process did not finish successfully. ERROR: %d' % ERROR_STATE

    save_log_to_database(database, COLLECTION_LOG, COLLECTION_WORDS, len(urls), total_added_words, ERROR_STATE)
#############################################################################


# Entry point
# Here you can choose news sites to parse, and DBs to store the data.
#############################################################################
def main():
    DBS = ['infobae', 'infobae_deportes', 'infobae_teleshow', 'infobae_vidriera', 'clarin']
    URLS = ['http://www.infobae.com/', 'http://www.infobae.com/deportes/', 'http://www.infobae.com/teleshow/', 'http://www.infobae.com/la-vidriera-de-infobae/', 'https://www.clarin.com/']
    

    for i in range(len(DBS)):
        parse_news(DBS[i], URLS[i])
#############################################################################


if __name__ == "__main__":
    main()
