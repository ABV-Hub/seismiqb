[![License](https://img.shields.io/github/license/analysiscenter/batchflow.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python](https://img.shields.io/badge/python-3.5-blue.svg)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-1.14-orange.svg)](https://tensorflow.org)

# Seismiqb

`seismiqb` is a framework for deep learning research on seismic data including pre-stack and post-stack `SEG-Y`s, horizons and other
seismic geobodies. The framework allows to

* `sample` and `load` crops of `SEG-Y` cubes for training neural networks
* convert `SEG-Y` cubes to `HDF5`-format for lighting fast `load` - 10x faster compared to `SEG-Y`
* build augmentation pipelines using custom augmentations for seismic data, including `hilbert`-transform and bandpass filtering, as well as classic `rotate`, `noise`, `elastic_transform` and `cutout`
* segment horizons and interlayers using [`UNet`](https://arxiv.org/abs/1505.04597) and [`Tiramisu`](https://arxiv.org/abs/1611.09326)
* extend horizons from a couple of seismic `ilines` in spirit of classic autocorrelation tools but with deep learning
* convert predicted masks into horizons for convenient validation by geophysicists

The application of the framework is not limited to deep learning. One can use it just fine to

* build quality-maps of seismic data
* perform automatic QC of seismic horizons without human involvement, using the range of correlation-based metrics
* conveniently gather all sorts of seismic data statistics, including amplitude and phase distributions for fast evaluation and comparison

## Installation

```
git clone --recursive https://github.com/gazprom-neft/seismiqb.git
```

## Tutorials

## Working with seismic data

### [Seismic `geometry`](tutorials/01_Geometry.ipynb)
Checking out seismic cubes without loading them in memory.

### [Dealing with seismic geobodies](tutorials/02_Horizon.ipynb)
learn to work with different seismic geobodies with focus on seismic horizons.

### [Cube-preprocessing](tutorials/03_Cubeset.ipynb)
Seismic cube preprocessing: `load_cubes`, `create_masks`, `scale`, `cutout_2d`, `rotate` and others.

## Deep learning for seismic horizon detection

### [Horizon segmentations](models/Horizons_detection.ipynb)
Solving a task of binary segmentation to detect seismic horizons.

### [Horizon extension](models/Horizons_extension.ipynb)
Extending picked horizons on the area of interest given marked horizons on a couple of `ilines`/`xlines`.

### [Interlayers segmentation](models/Segmenting_interlayers.ipynb)
Performing multiclass segmentation.


## Citing seismiqb

Please cite `seismicqb` in your publications if it helps your research.

    Khudorozhkov R., Koryagin A., Tsimfer S., Mylzenova D. Seismiqb library for seismic interpretation with deep learning. 2019.

```
@misc{seismiqb_2019,
  author       = {R. Khudorozhkov and A. Koryagin and S. Tsimfer and D. Mylzenova},
  title        = {Seismiqb library for seismic interpretation with deep learning},
  year         = 2019
}
```
