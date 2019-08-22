import argparse
import os
import pickle
import time

import cv2
import numpy as np
from scipy.cluster.vq import kmeans, vq
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.preprocessing import normalize

from computeFeatures import computeFeatures, computeFeatures_baseline

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_path', type=str, default='/home/gkhnkrhmt/Desktop/images',
                        help='Path of the image database')

    args = parser.parse_args()

    dbpath = args.db_path

    # List of features that stores
    feat = []
    base_feat = []

    for idx in range(500):
        # Load and convert image
        img = cv2.imread(os.path.join(dbpath, str(idx + 1) + ".jpg"))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Compute SIFT features for each keypoints
        feat.append(computeFeatures(img))

        # Compute baseline features for each image
        base_feat.append(computeFeatures_baseline(img))

        print('Extracting features for image #%d' % idx)

    """
    feat.shape=1x500    , her bir elemanı keypointx128 lik dizidir. (her elemanın descriptorx128 'inden dolayı)
    base_feat.shape=1x500 , her bir elemanı 1x192 lik dizidir. (3 tnae 64lük histogramdan dolayı)
    """
    # Stack all features together
    alldes = np.vstack(feat)
    """alldes.shape = 4410913x128 , tüm descriptorların sayısı x128 """
    k = 50

    # Perform K-means clustering
    alldes = np.float32(alldes)  # convert to float, required by kmeans and vq functions
    e0 = time.time()
    codebook, _ = kmeans(alldes, k)
    """codebook.shape=kx128 yani 50x128 oluyor. distortion.shape=1 (result döndürüyor?)
       her 128 sütun için 4410913 tane keypointten 50 merkezi nokta belirliyor."""
    e1 = time.time()
    print("Time to build {}-cluster codebook from {} images: {} seconds".format(k, alldes.shape[0], e1 - e0))

    # Save codebook as pickle file
    pickle.dump(codebook, open("codebook1.pkl", "wb"))
    """
    vstack yaparak 4milyon x128 li bir shape elde ederiz . Bunu yapmamızın sebebi 4milyon yani tüm keypointler
    içerisinden k-means ile 50x128 tane centroid döndürmek . 
    vstack yapmazsak k-means 500x1 lik bir diziden 50x1 'lik shape döndürecektir . 500 tane içinden 50 tane centroid döndüre-
    cektir. 
    """
    # Load cookbook
    codebook = pickle.load(open("codebook1.pkl", "rb"))

    # ====================================================================
    # Bag-of-word Features
    # ====================================================================
    # Create Bag-of-word list
    bow = []

    # Get label for each image, and put into a histogram (BoW)
    for f in feat:
        code, _ = vq(f, codebook)
        """f'teki descriptorlar gruplanıp code'a yazılır . code.shape=1xkeypoint_sayısı"""
        bow_hist, _ = np.histogram(code, k, normed=True)
        """gruplanmış descriptor'lar alınır ve histograma tabii tutulur. bow_hist.shape= bow_hist.shape=1x50"""
        bow.append(bow_hist)

    """bow.shape=1x500"""
    # Stack them together
    all_bow = np.vstack(bow)
    """temparr.shape = 500x50"""

    # pickle your features (bow)
    pickle.dump(all_bow, open("bow1.pkl", "wb"))
    print('')
    print('Bag-of-words features pickled!')


    # ====================================================================
    # TF-IDF Features
    # ====================================================================
    def tfidf(all_bow):
        # td-idf weighting
        transformer = TfidfTransformer(smooth_idf=True)
        t = transformer.fit_transform(all_bow).toarray()

        # normalize by Euclidean (L2) norm before returning
        t = normalize(t, norm='l2', axis=1)

        return t


    t = tfidf(all_bow)

    # pickle your features (tfidf)
    pickle.dump(t, open("tfidf1.pkl", "wb"))
    print('TF-IDF features pickled!')

    # ====================================================================
    # Baseline Features
    # ====================================================================
    # Stack all features together
    base_feat = np.vstack(base_feat)  # shape=500x192

    # pickle your features (baseline)
    pickle.dump(base_feat, open("base1.pkl", "wb"))
    print('Baseline features pickled!')

    # ====================================================================
