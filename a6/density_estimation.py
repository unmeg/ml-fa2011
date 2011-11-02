# Franklin Hu, Sunil Pedapudi
# CS 194-10 Machine Learning
# Fall 2011
# Assignment 6
import csv
import math
import sys

import numpy as np

import cross_validation

NUM_ARGS = 1
NUM_FOLDS = 5
CURRENT_FOLD = None

# Cache the following since computations are expensive
DISTANCE_CACHE = {}
KERNEL_CACHE = {}
K_NEAREST_CACHE = {}

## Calculates the great circle distance between two point on the earth's
## surface in degrees. loc1 and loc2 are pairs of longitude and latitude. E.g.
## int(dist_deg((10,0), (20, 0))) gives 10
def dist(loc1, loc2):
    loc1,loc2 = map(lambda x: tuple(x) if type(x) is not tuple else x,
                    [loc1, loc2])
    if loc1 > loc2:
        tmp = loc1
        loc1 = loc2
        loc2 = tmp
    key = (loc1, loc2)
    print key
    if key not in DISTANCE_CACHE:
        DEG2RAD = np.pi / 180
        RAD2DEG = 180 / np.pi
        lon1, lat1 = loc1
        lon2, lat2 = loc2
        DISTANCE_CACHE[key] = np.arccos(
                        np.sin(lat1 * DEG2RAD) * np.sin(lat2 * DEG2RAD)
                        + np.cos(lat1 * DEG2RAD) * np.cos(lat2 * DEG2RAD)
                        * np.cos((lon2 - lon1) * DEG2RAD)) * RAD2DEG
    return DISTANCE_CACHE[key]

def dist_k(k, data, query_point):
    k_nearest = k_nearest_neighbors(k, data, query_point)
    k_nearest.sort()
    return k_nearest[k-1]

def k_nearest_neighbors(k, data, query_point):
    """
    Find the k closest points to the query_point, in no particular order
    """
    assert len(data) > k
    key = (query_point, CURRENT_FOLD)
    if key not in K_NEAREST_CACHE:
        h = []
        for d in data:
            distance = dist(query_point, d)
            if len(h) < k:
                heapq.heappush(h, -distance)
            heapq.heappushpop(h, -distance)
        K_NEAREST_CACHE[key] = map(lambda x: -x, h)
    return K_NEAREST_CACHE[key]

def laplacian(d, b):
    ratio = -d/b
    if ratio not in KERNEL_CACHE:
        KERNEL_CACHE[ratio] = math.e ** (-d/b)
    return KERNEL_CACHE[ratio]

def kernel_density_base(kernel, distance, width, data, query_point, k):
    """
    Common function since 3/4 of the densities functions involve same code

    Arguments:
    kernel -- function (in this case Laplacian) that takes a distance d
              and width b parameters
    distance -- function that computes the distance between two points
    width -- function that computes the width b for the kernel function
    data -- list of training data entries
    query_point -- the point in question (x)
    """
    kernels = [kernel(distance(query_point, x_i),
                              width(k, data, x_i, query_point)) 
                       for x_i in data]
    N = len(kernels)
    return math.log(sum(kernels)) - math.log(N)

def log_kernel_density_a(data, query_point, k):
    """
    Kernel density function as given by:
    P(x) = (1/N) * \sum\limits_{i=1}^N K_b(d(x,x_i))
    """
    return kernel_density_base(laplacian, dist, 
                               lambda k,data,x_i,x: 5, 
                               data, query_point, k)

def log_kernel_density_b(data, query_point, k):
    """
    P(x) = k / (2N * d_k(x))
    where d_k(x) is the distance from x to the kth nearest neighbor of x
    """
    N = len(data)
    return math.log(k) - math.log(2 * N * dist_k(data, query_point))

def log_kernel_density_c(data, query_point, k):
    """
    P(x) = (1/N) * \sum\limits_{i=1}^N K_{d_k(x)}(d(x,x_i))
    same as (a) except the kernel width is determined by the kth
    nearest neighbor distance
    """
    return kernel_density_base(laplacian, dist,
                               lambda k,data,x_i,x: dist_k(k, data, x),
                               data, query_point, k)

def log_kernel_density_d(data, query_point, k):
    """
    P(x) = (1/N) * \sum\limits_{i=1}^N K_{d_{ik}(x)}(d(x,x_i))
    same as (c) except the kernel width is the kth nearest neighbor from 
    each x_i to its kth nearest neighbor, rather than from x
    """
    return kernel_density_base(laplacian, dist, 
                               lambda k,data,x_i,x: dist_k(k, data, x_i),
                               data, query_point, k)

if __name__ == "__main__":
    if len(sys.argv) < NUM_ARGS + 1:
        print "Usage: density_estimation.py data_file"
        sys.exit(1)
    data_file = sys.argv[1]
    handle = open(data_file, 'r')
    handle.readline()
    csv_file = csv.reader(handle)
    data = []
    for line in csv_file:
        data.append(map(lambda x: float(x), line[0:2]))

    # Find optimal k
    NUM_FOLDS = 20
    cross_val = cross_validation.CrossValidation(NUM_FOLDS, data)
    densities = [
        log_kernel_density_a,
        log_kernel_density_b,
        log_kernel_density_c,
        log_kernel_density_d]
    ks = range(5, 5 + NUM_FOLDS)
    for i in xrange(NUM_FOLDS):
        CURRENT_FOLD = i

        sum_likelihoods = [0] * len(densities)
        for v_ex in cross_val.validation_examples(i):
            likelihoods = map(lambda x: x(cross_val.training_examples(i),
                                          v_ex, ks[i]),
                              densities)
            for j in xrange(len(densities)):
                sum_likelihoods[j] += likelihoods[j]
        print "k: %d %s" % (i, sum_likelihoods)
            



