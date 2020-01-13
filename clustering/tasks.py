from django.core.cache import cache
from celery.decorators import task
import logging

from clustering_settings import CLUSTERING_CACHE_TIME, CLUSTERING_PENDING_CACHE_TIME
from . import CLUSTERING_RESULT_STATUS_PENDING, CLUSTERING_RESULT_STATUS_FAILED
from . import get_clustering_engine

logger = logging.getLogger('clustering')


@task(name="cluster_sounds")
def cluster_sounds(cache_key_hashed, cache_key, sound_ids, features):
    """ Triggers the clustering of the sounds given as argument with the specified features.

    This is the task that is used for clustering the sounds of a search result asynchronously with Celery.
    The clustering result is stored in cache using the hashed cache key built with the query parameters.

    Args:
        cache_key_hashed (str): hashed key for storing/retrieving the results in cache.
        sound_ids (List[int]): list containing the ids of the sound to cluster.
        features (str): name of the features used for clustering the sounds (defined in the clustering settings file).
    """
    # Get the engine using this function defined in __init__.py where the engine gets initialized once the app is ready.
    engine = get_clustering_engine()
    try:
        # perform clustering
        result = engine.cluster_points(cache_key, features, sound_ids)

        # store result in cache
        cache.set(cache_key_hashed, result, CLUSTERING_CACHE_TIME)

    except Exception as e:  
        # delete pending state if exception raised during clustering
        cache.set(cache_key_hashed, CLUSTERING_RESULT_STATUS_FAILED, CLUSTERING_PENDING_CACHE_TIME)
        logger.error("Exception raised while clustering sounds", exc_info=True)


@task(name="nearest_neighbors")
def nearest_neighbors(sound_ids, k, in_sound_ids, features):
    """Performs a K-Nearest Neighbors search on the sounds given as input.

    This task is performed multiple times in parallele when enabling PARALLELE_NEAREST_NEIGHBORS_COMPUTATION 
    clustering settings.
    TODO: catch possible exceptions

    Args: 
        sound_ids (List[int]): List containing sound ids.
        k (str): number of nearest neighbors to get.
        in_sound_ids (List[str]): subset of sounds to perform the searches on.
        features (str): name of the features used for clustering the sounds.

    Returns:
        dict: Dict containing the nearest neighbors and their associated distances for each sound given as input.
    """
    # Get the engine using this function defined in __init__.py where the engine gets initialized once the app is ready.
    engine = get_clustering_engine()
    result = engine.k_nearest_neighbors(sound_ids, k, in_sound_ids, features)
    return result


@task(bind=True, name='aggregate_nearest_neighbors_and_cluster_sounds')
def aggregate_nearest_neighbors_and_cluster_sounds(self, args, cache_key_hashed, cache_key, features, sound_ids):
    """Aggregates nearest neighbors and triggers the clustering of the sounds.
    
    This task is performed as a callback of the Celery chord task computed in parallele when enabling 
    PARALLELE_NEAREST_NEIGHBORS_COMPUTATION clustering settings.
    TODO: catch possible exceptions
    
    Args:
        args (List[Dict]): dict containing nearest neighbors and associated distances for the sounds to cluster.
        cache_key_hashed (str): hashed key for storing/retrieving the results in cache.
    """
    # Get the engine using this function defined in __init__.py where the engine gets initialized once the app is ready.
    engine = get_clustering_engine()

    # When there are not enough retrieved sounds to use more than one task for nearest neighbor searches
    # (the number of nearest neighbor searches to do in each worker is defined in the clustering settings), 
    # this task used as a chord callback recieves a dictionary instead of a list of dictionaries. 
    if isinstance(args, dict):
        d = args
    else:
        d = {}
        for arg in args:
            d.update(arg)

    result = engine.cluster_points_from_nearest_neighbors(d, cache_key, features, sound_ids)

    # store result in cache
    cache.set(cache_key_hashed, result, CLUSTERING_CACHE_TIME)
