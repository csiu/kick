import sys
sys.path.append("/Users/csiu/repo/kick/src/python")

import argparse
import custom
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import CountVectorizer
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

    parser.add_argument('-i', '--index_document0', default=0, type=int,
                        help="Index of query document")

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

def compute_distance(U, i=0, sort=False, top_n=None, metric='euclidean'):
    """
    Compute distance of document U[i] with all documents in U
    """
    document0 = np.asmatrix(U[i])

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
    index_document0 = args.index_document0
    num_results = args.num_results

    # Get and preprocess data
    df = get_data()
    _ =  preprocess_data(df)

    # Make count matrix
    cv = CountVectorizer()
    X = cv.fit_transform(df['doc_processed'])

    # SVD
    U, s, Vh = randomized_svd(X, n_components=num_singular_values,
                              n_iter=5, random_state=5)

    # Compute distance and get top results
    top_n = compute_distance(U, i=index_document0,
                             sort=True, top_n=num_results)

    # Print
    results = []
    counter = 0
    for index, row in df.iloc[top_n.index].iterrows():
        row["dist"] = top_n.iloc[counter]["dist"]
        results.append(row)
        counter += 1

        print('>> %s | %s' % (row['id'], row['doc_processed']),
              row['document'], "\n", sep="\n")
