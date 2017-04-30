import sys
sys.path.append("/Users/csiu/repo/kick/src/python")

import argparse
import custom
import pandas as pd
import numpy as np
import re
import os

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.utils.extmath import randomized_svd
from sklearn.metrics import pairwise_distances

usage = """
For finding similar documents
"""

def get_args():
    parser = argparse.ArgumentParser(description=usage)

    parser.add_argument('-s', '--num_singular_values', default=100, type=int,
                        help="Number of singular values to use from SVD")

    parser.add_argument('-n', '--num_results', default=None, type=int,
                        help="Number of similar documents to print in the results")

    parser.add_argument('-w', '--term_weight', default="tfidf",
                        choices=["tfidf", "raw"],
                        help="How should terms in document be weighted? 'tfidf' or 'raw' counts")

    parser.add_argument('-i', '--document0_id', default=None, type=int,
                        help="Kickstarter ID of query document")

    parser.add_argument('-c', '--cache_dir', default=".",
                        help="Specify cache dir")

    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    return(args)

def get_data():
    """
    Output dataframe w/ 2 columns: "id", "document"
    """
    # Get data
    dk = custom.DatabaseKick()
    cur = dk.connect()

    cur.execute("SELECT id, concat_ws(name, blurb) FROM info")
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["id", "document"])

    dk.disconnect()

    return(df)

def preprocess_data(df):
    """
    Preprocess 'document' of dataframe by
      - to lowercase
      - remove nonletters
      - tokenize
      - remove stopwords
      - stem
    Dataframe will contain additional 'doc_processed' column
    and df['doc_processed'] will be returned
    """

    def join_output(func):
        """
        Decorator function to join list output to string
        """
        def func_wrapper(text, *arg, **karg):
            return ' '.join(func(text, *arg, **karg))
        return func_wrapper

    def doc_to_string(doc):
        """
        Replace None -> empty string, and
        text newlines (\n, \r) -> whitespace
        """
        if doc == None:
            return("")
        else:
            return(re.sub("[\n\r]", "", doc))

    df['document'] = df['document'].apply(
            lambda x: doc_to_string(x))

    text_processing = join_output(custom.text_processing)
    df['doc_processed'] = df['document'].apply(
            lambda x: text_processing(x, method="stem"))

    return(df['doc_processed'])

def compute_distance(U, i=None, sort=False, top_n=None, metric='euclidean'):
    """
    Compute distance of document U[i] with all documents in U
    """
    if i != None:
        index_document0 = df[df["id"] == i].index.tolist()
    else:
        index_document0 = 0

    document0 = np.asmatrix(U[index_document0])

    dist = pairwise_distances(document0, U, metric=metric)
    df_dist = pd.DataFrame(np.transpose(dist), columns=["dist"])

    if sort:
         df_dist.sort_values(by="dist", inplace=True)

    if top_n != None:
        assert type(top_n) is int
        df_dist = df_dist.head(top_n)

    return(df_dist)


if __name__ == '__main__':
    args = get_args()
    num_singular_values = args.num_singular_values
    document0_id = args.document0_id
    num_results = args.num_results
    cache_dir = args.cache_dir
    verbose = args.verbose
    term_weight = args.term_weight

    preprocess_file = os.path.join(os.path.abspath(cache_dir),
                                   "preprocessed.pkl")


    msg = "# Getting and preprocessing data..."
    if os.path.isfile(preprocess_file):
        if verbose: print(msg, "from cache...")
        df = pd.read_pickle(preprocess_file)
    else:
        if verbose: print(msg)
        df = get_data()
        _ =  preprocess_data(df)

        df.to_pickle(preprocess_file)

    if term_weight == "raw":
        if verbose: print("# Making count matrix...")
        cv = CountVectorizer()
        X = cv.fit_transform(df['doc_processed'])
    else:
        if verbose: print("# Making TF-IDF matrix...")
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(df['doc_processed'])

    if verbose: print("# Computing SVD for %s singular values..." %
                      num_singular_values)
    U, s, Vh = randomized_svd(X, n_components=num_singular_values,
                              n_iter=5, random_state=5)

    if verbose: print("# Computing distances...")
    top_n = compute_distance(U, i=document0_id,
                             sort=True, top_n=num_results)

    if verbose: print("# Printing results...")
    results = []
    counter = 0
    for index, row in df.iloc[top_n.index].iterrows():
        row["dist"] = top_n.iloc[counter]["dist"]
        results.append(row)
        counter += 1

        print('>> %s | %s' % (row['id'], row['doc_processed']),
              row['document'], "\n", sep="\n")
