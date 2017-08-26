from pymongo import MongoClient


# Get all the words
# of a collection
##########################
def get_all_words_from_db(database, collection):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    cursor = coll.find().sort('count', -1)

    result = list()
    for doc in cursor:
        result.append(doc['word'])

    return result
##########################


# Get X most used words
################################
def get_first_words_from_db(database, collection, stop):
    client = MongoClient()
    db = client[database]
    coll = db[collection]

    cursor = coll.find().sort('count', -1).limit(stop)

    result = list()
    for doc in cursor:
        result.append(doc['word'])

    return result
################################


# Write list of words
# to a file
################################
def write_words_to_file(path, file_name, words):
    file_path = path + '/' + file_name

    try:
        with open(file_path, 'a') as f:
            for word in words:
                f.write(word.encode('utf8') + '\n')
    except:
        raise
################################


def main():
    DBS = ['infobae', 'infobae_deportes', 'infobae_teleshow', 'infobae_vidriera']
    COLLS = ['words_all', 'words_names', 'words_headlines', 'words_names_hdl']
    OUT_PATH = 'dict'

    for db in DBS:
        for coll in COLLS:
            words = get_all_words_from_db(db, coll)
            outfile = db + '.' + coll + '.txt'

            try:
                write_words_to_file(OUT_PATH, outfile, words)
            except:
                print 'Error writing file: ' + outfile

if __name__ == "__main__":
    main()
