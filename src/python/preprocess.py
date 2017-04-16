import psycopg2
import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer

class DatabaseKick:
    def __init__(self):
        self.dbname = "kick"
        self.tblname = "info"

    def connect(self):
        self.conn = psycopg2.connect(dbname=self.dbname)
        self.cur = self.conn.cursor()
        return(self.cur)

    def disconnect(self):
        self.cur.close()
        self.conn.close()

def text_processing(text, method=None):
    if text == None: return("")

    # Lower case
    text = text.lower()

    # Remove non-letters &
    # Tokenize
    words = nltk.wordpunct_tokenize(re.sub('[^a-zA-Z_ ]', '', text))

    # Remove stop words
    words = [w for w in words if not w in stopwords.words("english")]

    # Stemming vs Lemmatizing vs do nothing
    if method == "stem":
        port = PorterStemmer()
        words = [port.stem(w) for w in words]
    elif method == "lemm":
        wnl = WordNetLemmatizer()
        words = [wnl.lemmatize(w) for w in words]

    return(words)
