# Python news parser for dictionary attacks

This tool parses news articles and saves words and counts to a database. It makes use of either a **Part of Speech tagger** or **Named Entity Recognizer** to build wordlists for dictionary attacks.

It parses news sites from Argentina and uses spanish models for Natural Language Processing, but it should be easy to add models for other languages, as well as code to handle other news sites.

## Natural Language Processing

In order to select relevant words, two different tools by **The Stanford Natural Language Processing Group** are used. They are not provided here, so you will have to download them from their site. I do include bash scripts that execute these tools.

### Stanford Log-linear Part-Of-Speech Tagger

This is a java tool that assigns parts of speech to each word in a sentence. For our purposes, only nouns and adjectives are kept, every other word (verbs, prepositions, etc) is discarded.

The model used is for spanish words, and is available at Stanford NLP Group's site. It is possible to train and use your own models if you find the default ones to be inaccurate.

*Site: https://nlp.stanford.edu/software/tagger.html

### Stanford Named Entity Recognizer

This is a java tool that labels sequences of words in a text which are the names of things. Names, places and organizations are kept as relevant words. A spanish model has been used. You can change it if needed.

*Site: https://nlp.stanford.edu/software/CRF-NER.html

## Dependencies

 - Python 2.7
 - Java 1.8+
 - [Stanford POS Tagger](https://nlp.stanford.edu/software/tagger.html)
 - [Stanford Named Entity Recognizer](https://nlp.stanford.edu/software/CRF-NER.html)
 - MongoDB and PyMongo
 - Beautiful Soup 4
 - Selenium WebDriver for Python
 - [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) (or your favorite browser)

## Parsing news sites

Some news sites can have their source code retrieved in one shot (such as Infobae, Pagina 12, etc) whereas other sites have their **content loaded dynamically** (Clarin, Ole, etc). For the latter, a **Web Driver** has been used in order to automatically open and **scroll websites** until all the content has been loaded.

To add new websites, you need to:

### 1- Add a routine to parse the main site and get links to news articles
This routine receives a url as argument and returns a set of urls.

For Infobae site, urllib has been used to get html code, which is then manipulated with Beautiful Soup to get all of the hrefs:

![urllib](http://i.imgur.com/PmYS6hF.png)

For Clarin, content is dynamically loaded, so Selenium has been used to get html code, which is then fed to Beautiful Soup:

![selenium](http://i.imgur.com/Yc2mvrJ.png)

### 2- Modify *get_news_hrefs_from_main_page()* to include the new site
![get_news_hrefs_from_main_page](http://i.imgur.com/fcULMQk.png)

### 3- Add the url to the site in *main()* routine
![main](http://i.imgur.com/br0Sfwo.png)

### 4- Add a routine to parse individual news
The routine receives a url as argument and returns a buffer with text. Here's code to get Infobae's text:

![Parse news site](http://i.imgur.com/joTMXc0.png)

### 5- Modify *get_news_text()* to include the new site

## Database

Information is stored in a Mongo database. Every different news site has its own database, which holds the following collections:

 - **words_all**: nouns and adjectives found in articles (header + subheader + body). This is the result of applying PoS Tagger to the whole text. Example:
 
`{'word' : 'obama', 'count' : 174}`

 - **words_names**: names, places and organizations found in the whole text of the article. This is the result of applying NER.

 - **words_headlines**: nouns and adjectives found in the header (title) of the news article. The content of the article is not parsed, only the title.

 - **words_names_hdl**: names found in the headlines.

 - **urls**: all the urls that have already been parsed. Example:
 
`{'url' : 'http://www.infobae.com/politica/2017/08/25/causa-hotesur-el-juez-ercolini-cito-a-indagatoria-a-cristina-kirchner/'}`

 - **logs**: counts of words and urls that were added on a particular time.
 
`{'words_all' : 5990, 'words_names' : 1451, 'words_headlines' : 429, 'words_names_hdl' : 126, 'urls' : 83, 'date' : datetime.datetime(2017, 8, 15, 16, 49, 18, 87000)}`

## Periodicity and hanging processes

You'll find a crontab included in the main directory. I run the parser every 6 hours, but you can customize this if needed.

Sometimes java processes for NER or PoS Tagger never finish. Instead of analyzing why this happens, I just created a bash script that checks for these processes running over 5 minutes and kills them. This means that the rogue article does not get processed; execution moves on to the next article to parse.

That bash script is included here as ***hippie_killer.sh*** and is also included in ***.crontab***.

## Dictionaries

If you don't really care about the code and just came here for the dictionaries, you'll find them under ***dict*** subdirectory.

Just bear in mind that these dictionaries are only step 1. You'll have to massage them, combine them, mask them and use some rules in order to have any success.

More dictionaries will be added as long as there's new code for other news sites.

## Ideas and improvements

I don't think I'll be adding new code, so I entirely hope for you to **collaborate!!**

Code, ideas and suggestions are welcome. Here are some:

 - It would be interesting to store in the database whether the word is a name, a place, an organization, etc. That way, you can have a dictionary with people's names only, or places or whatever. It is very common to see 'name' + 'teamo' (I love you) passwords in spanish.

 - The same, but having a dictionary for nouns, another one for adjectives, and so on. That way, it is easier to make valid combinations.
