from django.core.cache import cache
from celery.decorators import task
import logging

from clustering_settings import CLUSTERING_CACHE_TIME, CLUSTERING_PENDING_CACHE_TIME
from . import CLUSTERING_RESULT_STATUS_PENDING, CLUSTERING_RESULT_STATUS_FAILED

logger = logging.getLogger('clustering')


@task(name="cluster_sounds")
def cluster_sounds(cache_key_hashed, sound_ids, features):
    """ Triggers the clustering of the sounds given as argument with the specified features.

    This is the task that is used for clustering the sounds of a search result asynchronously with Celery.
    The clustering result is stored in cache using the hashed cache key built with the query parameters.

    Args:
        cache_key_hashed (str): hashed key for storing/retrieving the results in cache.
        sound_ids (List[int]): list containing the ids of the sound to cluster.
        features (str): name of the features used for clustering the sounds (defined in the clustering settings file).
    """
    # This ensures that the engine is imported after it is re-assigned in __init__.py
    # There should be a better way to do it to avoid multiple imports that can decrease performance
    from . import engine

    try:
        # perform clustering
        result = engine.cluster_points(cache_key_hashed, features, sound_ids)

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
    from . import engine
    result = engine.k_nearest_neighbors(sound_ids, k, in_sound_ids, features)
    return result


@task(bind=True, name='aggregate_nearest_neighbors_and_cluster_sounds')
def aggregate_nearest_neighbors_and_cluster_sounds(self, args, cache_key_hashed):
    """Aggregates nearest neighbors and triggers the clustering of the sounds.
    
    This task is performed as a callback of the Celery chord task computed in parallele when enabling 
    PARALLELE_NEAREST_NEIGHBORS_COMPUTATION clustering settings.
    TODO: catch possible exceptions
    
    Args:
        args (List[Dict]): dict containing nearest neighbors and associated distances for the sounds to cluster.
        cache_key_hashed (str): hashed key for storing/retrieving the results in cache.
    """
    from . import engine
    d = {}
    for arg in args:
        d.update(arg)
    result = engine.cluster_points_from_nearest_neighbors(d)

    # store result in cache
    cache.set(cache_key_hashed, result, CLUSTERING_CACHE_TIME)
