import sys
sys.path.append("/Users/csiu/repo/kick/src/python")

import custom
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.utils.extmath import randomized_svd
from sklearn.metrics import pairwise_distances


# Get data
dk = custom.DatabaseKick()
cur = dk.connect()

cur.execute("SELECT id, concat_ws(name, blurb) FROM info")
rows = cur.fetchall()
df = pd.DataFrame(rows, columns=["id", "document"])

dk.disconnect()


# Preprocess text
def join_output(func):
    def func_wrapper(text, *arg, **karg):
        return ' '.join(func(text, *arg, **karg))
    return func_wrapper

text_processing = join_output(custom.text_processing)

def doc_to_string(doc):
    """
    Replace None -> empty string, and
    text newlines (\n, \r) -> whitespace
    """
    if doc == None:
        return("")
    else:
        return(re.sub("[\n\r]", "", doc))

df['document'] = df['document'].apply(lambda x: doc_to_string(x))
df['doc_processed'] = df['document'].apply(lambda x: text_processing(x, method="stem"))


# Make count matrix
cv = CountVectorizer()
X = cv.fit_transform(df['doc_processed'])


# SVD
U, s, Vh = randomized_svd(X, n_components=100, n_iter=5, random_state=5)


# Distance
dist = pairwise_distances(np.asmatrix(U[0]), U, metric='euclidean')
df_dist = pd.DataFrame(np.transpose(dist), columns=["dist"])


# Get top results
top_n = df_dist.sort_values("dist").head()

results = []
counter = 0
for index, row in df.iloc[top_n.index].iterrows():
    row["dist"] = top_n.iloc[counter]["dist"]
    results.append(row)
    counter += 1

    print('>> %s | %s' % (row['id'], row['doc_processed']),
          row['document'], "\n", sep="\n")
