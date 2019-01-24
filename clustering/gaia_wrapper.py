import logging
import os
import time

import yaml
from gaia2 import DataSet, View, DistanceFunctionFactory

import clustering_settings as clust_settings


class GaiaWrapper:
    def __init__(self):
        self.dataset = DataSet()
        self.index_path = clust_settings.INDEX_DIR
        self.view = None
        self.metric = None
        self.__load_dataset()

    def __get_dataset_path(self, ds_name):
        return os.path.join(clust_settings.INDEX_DIR, ds_name + '.db')

    def __load_dataset(self):
        self.dataset.load(self.__get_dataset_path(clust_settings.INDEX_NAME))
        self.view = View(self.dataset)
        self.metric = DistanceFunctionFactory.create('euclidean', self.dataset.layout())

    def search_nearest_neighbors(self, sound_id, k, in_sound_ids=[]):
        if in_sound_ids:
            filter = 'WHERE point.id IN ("' + '", "'.join(in_sound_ids) + '")'
        else:
            filter = None
        return self.view.nnSearch(sound_id, self.metric, filter).get(k)[1:]