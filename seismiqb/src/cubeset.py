""" Contains container for storing dataset of seismic crops. """
import dill

import numpy as np

from ..batchflow import Dataset, Sampler
from ..batchflow import HistoSampler, NumpySampler, ConstantSampler
from .geometry import SeismicGeometry
from .crop_batch import SeismicCropBatch

from .utils import read_point_cloud, make_labels_dict


class SeismicCubeset(Dataset):
    """ Stores indexing structure for dataset of seismic cubes along with additional structures.
    """
    def __init__(self, index, batch_class=SeismicCropBatch, preloaded=None, *args, **kwargs):
        """ Initialize additional attributes.
        """
        super().__init__(index, batch_class=batch_class, preloaded=preloaded, *args, **kwargs)
        self.geometries = {ix: SeismicGeometry(self.index.get_fullpath(ix)) for ix in self.indices}
        self.point_clouds = {ix: np.array([]) for ix in self.indices}
        self.labels = {ix: dict() for ix in self.indices}
        self.samplers = {ix: None for ix in self.indices}
        self.sampler = None


    def load_geometries(self, path=None, scalers=False, mode='full', logs=True):
        """ Load geometries into dataset-attribute.

        Parameters
        ----------
        path : str
            Path to load geometries from.

        scalers : bool
            Whether to make callables to scale initial values in .sgy cube to
            [0, 1] range. It takes quite a lot of time.

        mode : one of 'full', 'random'
            Sampler creating mode. Determines amount of trace to check to find
            cube minimum/maximum values.

        logs : bool
            Whether to create logs. If True, .log file is created next to .sgy-cube location.

        Returns
        -------
        SeismicCubeset
            Same instance with loaded geometries.
        """
        if isinstance(path, str):
            with open(path, 'rb') as file:
                self.geometries = dill.load(file)
        else:
            for ix in self.indices:
                self.geometries[ix].load()
                if scalers:
                    self.geometries[ix].make_scalers(mode=mode)
                if logs:
                    self.geometries[ix].log()
        return self


    def save_geometries(self, save_to):
        """ Save dill-serialized geometries for a dataset of seismic-cubes on disk.
        """
        if isinstance(save_to, str):
            with open(save_to, 'wb') as file:
                dill.dump(self.geometries, file)

        return self


    def load_point_clouds(self, paths=None, path=None, **kwargs):
        """ Load point-cloud of labels for each cube in dataset.

        Parameters
        ----------
        paths : dict
            Mapping from indices to txt paths with labels.

        path : str
            Path to load point clouds from.

        Returns
        -------
        SeismicCubeset
            Same instance with loaded point clouds.
        """
        if isinstance(path, str):
            with open(path, 'rb') as file:
                self.point_clouds = dill.load(file)
        else:
            for ix in self.indices:
                self.point_clouds[ix] = read_point_cloud(paths[ix], **kwargs)
        return self


    def save_point_clouds(self, save_to):
        """ Save dill-serialized point clouds for a dataset of seismic-cubes on disk.
        """
        if isinstance(save_to, str):
            with open(save_to, 'wb') as file:
                dill.dump(self.point_clouds, file)

        return self


    def load_labels(self, path=None, transforms=None, src='point_clouds'):
        """ Make labels in inline-xline coordinates using cloud of points and supplied transforms.

        Parameters
        ----------
        path : str
            Path to load labels from.

        transforms : dict
            Mapping from indices to callables. Each callable should define
            way to map point from absolute coordinates (X, Y world-wise) to
            cube specific (ILINE, XLINE) and take array of shape (N, 3) as input.

        src : str
            Attribute with saved point clouds.

        Returns
            Same instance with loaded labels.
        """
        #pylint: disable=unreachable, no-else-raise
        point_clouds = getattr(self, src) if isinstance(src, str) else src
        transforms = transforms or dict()

        if isinstance(path, str):
            raise NotImplementedError("Numba dicts are yet to support serializing")
            with open(path, 'rb') as file:
                self.labels = dill.load(file)
        else:
            for ix in self.indices:
                point_cloud = point_clouds.get(ix)
                geom = getattr(self, 'geometries').get(ix)
                transform = transforms.get(ix) or geom.abs_to_lines
                self.labels[ix] = make_labels_dict(transform(point_cloud))
        return self


    def save_labels(self, save_to):
        """ Save dill-serialized labels for a dataset of seismic-cubes on disk.
        """
        #pylint: disable=unreachable, no-else-raise
        raise NotImplementedError("Numba dicts are yet to support serializing")
        if isinstance(save_to, str):
            with open(save_to, 'wb') as file:
                dill.dump(self.labels, file)

        return self


    def load_samplers(self, path=None, mode='hist', p=None,
                      transforms=None, **kwargs):
        """ Create samplers for every cube and store it in `samplers`
        attribute of passed dataset. Also creates one combined sampler
        and stores it in `sampler` attribute of passed dataset.

        Parameters
        ----------
        path : str
            Path to load samplers from.

        mode : str or Sampler
            Type of sampler to be created.
            If 'hist', then sampler is estimated from given labels.
            If 'numpy', then sampler is created with `kwargs` parameters.
            If instance of Sampler is provided, it must generate points from unit cube.

        p : list
            Weights for each mixture in final sampler.

        transforms : dict
            Mapping from indices to callables. Each callable should define
            way to map point from absolute coordinates (X, Y world-wise) to
            cube local specific and take array of shape (N, 3) as input.

        Note
        ----
        Passed `dataset` must have `geometries` and `labels` attributes if
        you want to create HistoSampler.
        """
        # pylint: disable=cell-var-from-loop
        lowcut, highcut = [0, 0, 0], [1, 1, 1]
        transforms = transforms or dict()

        if isinstance(path, str):
            with open(path, 'rb') as file:
                samplers = dill.load(file)

        else:
            samplers = {}
            if not isinstance(mode, dict):
                mode = {ix:mode for ix in self.indices}

            for ix in self.indices:
                if isinstance(mode[ix], Sampler):
                    sampler = mode[ix]
                elif mode[ix] == 'numpy':
                    sampler = NumpySampler(**kwargs)
                elif mode[ix] == 'hist':
                    point_cloud = getattr(self, 'point_clouds')[ix]

                    geom = getattr(self, 'geometries')[ix]
                    offsets = np.array([geom.ilines_offset, geom.xlines_offset, 0])
                    cube_shape = np.array(geom.cube_shape)
                    to_cube = lambda points: (points - offsets)/cube_shape
                    default = lambda points: to_cube(geom.abs_to_lines(points))

                    transform = transforms.get(ix) or default
                    cube_array = transform(point_cloud)

                    bins = kwargs.get('bins') or 100
                    sampler = HistoSampler(np.histogramdd(cube_array, bins=bins))
                else:
                    sampler = NumpySampler('u', low=0, high=1, dim=3)

                sampler = sampler.truncate(low=lowcut, high=highcut)
                samplers.update({ix: sampler})
        self.samplers = samplers

        # One sampler to rule them all
        p = p or [1/len(self) for _ in self.indices]

        sampler = 0 & NumpySampler('n', dim=4)
        for i, ix in enumerate(self.indices):
            sampler_ = (ConstantSampler(ix)
                        & samplers[ix].apply(lambda d: d.astype(np.object)))
            sampler = sampler | (p[i] & sampler_)
        self.sampler = sampler
        return self


    def save_samplers(self, save_to):
        """ Save dill-serialized samplers for a dataset of seismic-cubes on disk.
        """
        if isinstance(save_to, str):
            with open(save_to, 'wb') as file:
                dill.dump(self.samplers, file)

        return self


    def save_attr(self, name, save_to):
        """ Save attribute of dataset to disk. """
        if isinstance(save_to, str):
            with open(save_to, 'wb') as file:
                dill.dump(getattr(self, name), file)

        return self
