"""utils for transformers."""

from typing import Tuple
import numpy as np

from ..utils.logging import get_logger

logger = get_logger(__name__)
logger.setLevel(verbosity_to_loglevel(3))

class GroupByProcessor:    
    def __init__(self, keys):
        super().__init__()
        
        assert keys is not None
        
        self.index, self.keys_as_int = np.unique(keys, return_inverse = True)
        self.n_keys = max(self.keys_as_int) + 1
        self.set_indices()
    
    def set_indices(self):
        self.indices = [[] for i in range(self.n_keys)]
        for i, k in enumerate(self.keys_as_int):
            self.indices[k].append(i)
        self.indices = [np.array(elt) for elt in self.indices]
            
    def apply(self, functions, vectors):
        assert functions is not None
        assert vectors is not None

        if isinstance(functions, list):
            return [[fun(vec[idx].tolist()) for fun, vec in zip(functions, vectors)] for idx in (self.indices)]
        else:
            return [functions(vectors[idx].tolist()) for idx in (self.indices)]
        
class GroupByFactory:    
    @staticmethod
    def get_GroupBy(kind):
        assert kind is not None
        
        available_classes = [
            GroupByNumDeltaMean, 
            GroupByNumDeltaMedian,
            GroupByNumMin,
            GroupByNumMax,
            GroupByNumStd, 
            GroupByCatMode, 
            GroupByCatIsMode
        ]

        for class_name in available_classes:
            if kind == class_name.class_kind:
                return class_name(class_name.class_kind, class_name.class_fit_func, class_name.class_transform_func)

        raise ValueError(f'Unsupported kind: {kind}, available={[class_name.class_kind for class_name in available_classes]}')        

class GroupByBase:        
    def __init__(self, kind, fit_func, transform_func):
        super().__init__()

        self.kind = kind
        self.fit_func = fit_func
        self.transform_func = transform_func
        
        self._dict = None

    def get_dict(self):
        return self._dict

    def set_dict(self, dict):
        self._dict = dict
        
    def fit(self, data, group_by_processor, feature_column):
        assert data is not None
        assert group_by_processor is not None        
        assert feature_column is not None
        
        assert self.fit_func is not None

        feature_values = data[feature_column].to_numpy()
        self._dict = dict(zip(group_by_processor.index, group_by_processor.apply(self.fit_func, feature_values)))
            
        assert self._dict is not None
        
        return self
    
    def transform(self, data, value):
        assert data is not None
        assert value is not None
        
        assert self.transform_func is not None

        group_values = data[value['group_column']].to_numpy()        
        feature_values = data[value['feature_column']].to_numpy()
        result = self.transform_func(tuple([np.vectorize(self._dict.get)(group_values), feature_values])).reshape(-1, 1)            
            
        assert result is not None
        return result

class GroupByNumDeltaMean(GroupByBase):    
    class_kind = 'delta_mean'    
    class_fit_func = np.nanmean
    class_transform_func = lambda values: (values[1] - values[0])
        
class GroupByNumDeltaMedian(GroupByBase):    
    class_kind = 'delta_median'    
    class_fit_func=np.nanmedian
    class_transform_func=lambda values: (values[1] - values[0])

class GroupByNumMin(GroupByBase):    
    class_kind = 'min'    
    class_fit_func=np.nanmin
    class_transform_func=lambda values: (values[0])
        
class GroupByNumMax(GroupByBase):    
    class_kind = 'max'    
    class_fit_func=np.nanmax
    class_transform_func=lambda values: (values[0])
        
class GroupByNumStd(GroupByBase):    
    class_kind = 'std'    
    class_fit_func=np.nanstd
    class_transform_func=lambda values: (values[0])
        
class GroupByCatMode(GroupByBase):    
    class_kind = 'mode'    
    class_fit_func=GroupByTransformer.get_mode
    class_transform_func=lambda values: (values[0])
        
class GroupByCatIsMode(GroupByBase):    
    class_kind = 'is_mode'    
    class_fit_func=GroupByTransformer.get_mode
    class_transform_func=lambda values: (values[0] == values[1])
  