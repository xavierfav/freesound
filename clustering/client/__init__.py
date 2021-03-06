from clustering.clustering_settings import CLUSTERING_ADDRESS, CLUSTERING_PORT
import json
import urllib2

_BASE_URL                     = 'http://%s:%i/clustering/' % (CLUSTERING_ADDRESS, CLUSTERING_PORT)
_URL_CLUSTER_POINTS           = 'cluster_points'


class ClusteringException(Exception):
    status_code = None

    def __init__(self, *args, **kwargs):
        super(ClusteringException, self).__init__(*args)
        self.status_code = kwargs['status_code']


def _get_url_as_json(url, data=None, timeout=None):
    kwargs = dict()
    if data is not None:
        kwargs['data'] = data
    if timeout is not None:
        kwargs['timeout'] = timeout
    f = urllib2.urlopen(url.replace(" ", "%20"), timeout=60, **kwargs)
    resp = f.read()
    return json.loads(resp)


def _result_or_exception(result):
    if not result['error']:
        return result['result'], result['graph']
    else:
        if 'status_code' in result.keys():
            raise ClusteringException(result['result'], status_code=result['status_code'])
        else:
            raise ClusteringException(result['result'], status_code=500)


class Clustering():

    @classmethod
    def cluster_points(cls, query, sound_ids, features):
        url = _BASE_URL + _URL_CLUSTER_POINTS + '?' + 'query_params=' + str(query) + '&' + 'features=' + features
        return _result_or_exception(_get_url_as_json(url, data='sound_ids='+str(sound_ids)))
