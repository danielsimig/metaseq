# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import numpy as np
import pandas as pd
import json

from metaseq.file_io import PathManager

from metaseq.data import data_utils
from . import BaseWrapperDataset

class FilterDataset(BaseWrapperDataset):
    """Filters dataset by excluding examples that are easy/hard to learn.
    
    Hard/easy to learn are defined by a metric between 0.0 and 1.0, with
    0.0 meaning easy to learn, and 1.0 meaning hard to learn.

    During initialization, this class expects:
    - `frac_data`: how much of the original dataset we want to keep 
    during training. It calculates the closest `frac_data` we can keep
    (keep the hard examples, throw away easy examples, 
    as per https://arxiv.org/abs/2206.14486.
    - `metric_file`: path to jsonl file, where each line should be

        {
            "name": dataset_name, 
            "index": index in dataset jsonl file, 
            "metric": metric value
        }
    where `metric` should be between 0.0 and 1.0 as described above

    """

    def __init__(self, dataset, frac_data, metric_data):
        super().__init__(dataset)
        assert 0.0 <= frac_data <= 1.0
        self.frac_data = frac_data
        self.dataset = dataset
        self.metric_data = metric_data

        # This means we should not be pruning, because not enough datapoints have a computed metric
        limit = int(np.ceil(len(self.dataset) * self.frac_data))
        self.length = limit

        df_final.sort_values('metric', inplace=True, ascending=False)
        self.df_final = df_final[:limit]

    @staticmethod
    def retrieve_metric_df(metric_file, dataset_name_to_index):
        assert PathManager.exists(metric_file), "Error! Provided `metric_file` is not a valid filepath"
        assert PathManager.isfile(metric_file), "Error! Provided `metric_file` is not a valid file"
        assert metric_file.endswith(".jsonl"), "Error! `metric_file` must be a `jsonl` file"

        with open(metric_file, "r") as f:
            lines = f.read().splitlines()

        df = pd.DataFrame(lines)
        df.columns = ['temp']
        df['temp'].apply(json.loads)
        df = pd.json_normalize(df['temp'].apply(json.loads))
        return df

    def __getitem__(self, index):
        assert 0 <= index <= self.length

        metadata = self.metric_data.iloc[index]
        dataset_name = str(metadata["name"])
        sample_idx = int(metadata["index"])

        assert dataset_name in dataset_name_to_index, f"Error: dataset path {dataset_name} not in dataset_index"
        dataset_index = dataset_name_to_index[str(metadata["name"])]

        return self.datasets[dataset_index][sample_idx]

    def __len__(self):
        return self.length