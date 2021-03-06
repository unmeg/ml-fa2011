# Franklin Hu, Sunil Pedapudi
# CS 194-10 Machine Learning
# Fall 2011
# Assignment 4
from collections import defaultdict
import math
import pickle
import random
import sys
import time

import NBmodel

NUM_ARGS = 4
NUM_RANDOM_FEATURES = 4000
BOOL_MODEL_FILE = "Boolean.model"
NTF_MODEL_FILE = "NTF.model"

def train_dir(directory, cls, bool_model, bool_feat, ntf_model, ntf_feat):
    for f in NBmodel.get_files(directory):
        bool_ex = NBmodel.munge_Boolean(f, bool_feat)
        ntf_ex = NBmodel.munge_NTF(f, ntf_feat)

        bool_model.train(bool_ex, cls)
        ntf_model.train(ntf_ex, cls)

def dump_obj(filename, obj):
    handle = open(filename, 'wb')
    pickle.dump(obj, handle)
    handle.close()

def _get_features_list(spam_dir, ham_dir):
    def process_email(freq, filename, cls):
        email = open(filename, 'r')
        for line in email:
            tok = line.rstrip("\n").rstrip("\r").strip(" ").split(" ")
            for t in tok:
                freq[(cls,t)] = [freq[(cls,t)][0]+1, 
                                 freq[(cls,t)][0]+float(1/len(tok))]
        email.close()

    freq = defaultdict(lambda: list([0,0]))
    for email_file in NBmodel.get_files(spam_dir):
        process_email(freq, email_file, 'SPAM')

    for email_file in NBmodel.get_files(ham_dir):
        process_email(freq, email_file, 'HAM')

    return freq
def _write_features(features_file, spam_dir, ham_dir, borntf):
    freq = _get_features_list(spam_dir, ham_dir)
    features = [x[1] for x in freq.keys()]
    infogain = []
    for f in features:
        sfreq, sig = freq[('SPAM', f)][borntf], 0
        hfreq, hig = freq[('HAM', f)][borntf], 0
        if sfreq > 0:
            sig = sfreq*math.log(sfreq)
        if hfreq > 0:
            hig = hfreq*math.log(hfreq)
        ig = -1*(sig+hig)
        infogain.append((ig, f))
    infogain.sort()
    features = [x[1] for x in infogain][:NUM_RANDOM_FEATURES]
    # random.shuffle(features)
    # features = features[:NUM_RANDOM_FEATURES]
    dump_obj(features_file, features)
    return features

def _write_bool_features(features_file, spam_dir, ham_dir):
    return _write_features(features_file, spam_dir, ham_dir, 0)

def _write_ntf_features(features_file, spam_dir, ham_dir):
    return _write_features(features_file, spam_dir, ham_dir, 1)

if __name__ == "__main__":
    if len(sys.argv) < NUM_ARGS + 1:
        print "Usage: train.py spamdir hamdir bool_features ntf_features"
        sys.exit(1)
    spamdir = sys.argv[1]
    hamdir = sys.argv[2]
    bool_features_file = sys.argv[3]
    ntf_features_file = sys.argv[4]

    bool_features = _write_bool_features(bool_features_file, spamdir, hamdir)
    ntf_features = bool_features

    #bool_features = pickle.load(open(bool_features_file, 'rb'))
    #ntf_features = pickle.load(open(ntf_features_file, 'rb'))

    bool_model = NBmodel.NB_Boolean(bool_features_file)
    ntf_model = NBmodel.NB_NTF(bool_features_file)

    t = time.time()

    print "+ Begin SPAM"
    train_dir(spamdir, NBmodel.SPAM, bool_model, bool_features, 
              ntf_model, ntf_features)
    print "++ End SPAM %f" % (time.time() - t)

    t = time.time()
    print "+ Begin HAM"
    train_dir(hamdir, NBmodel.HAM, bool_model, bool_features,
              ntf_model, ntf_features)
    print "+ End HAM %f" % (time.time() - t)

    t = time.time()
    print "+ Begin Boolean finalize"
    bool_model.finalize_training()
    print "+ %f" % (time.time() - t)

    t = time.time()
    print "+ Begin NTF finalize"
    ntf_model.finalize_training()
    print "+ %f" % (time.time() - t)
    
    print "+ Dumping objects"
    dump_obj(BOOL_MODEL_FILE, bool_model)
    dump_obj(NTF_MODEL_FILE, ntf_model)

