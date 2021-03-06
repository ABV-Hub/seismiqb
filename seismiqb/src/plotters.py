""" Plot functions. """
import numpy as np

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def channelize_image(image, total_channels, n_channel=0, greyscale=False, opacity=None):
    """ Channelize an image. Can be used to make an opaque rgb or grayscale image.
    """
    # case of a partially channelized image
    if image.ndim == 3:
        if image.shape[-1] == total_channels:
            return image

        background = np.zeros((*image.shape[:-1], total_channels))
        background[:, :, :image.shape[-1]] = image

        if opacity is not None:
            background[:, :, -1] = opacity
        return background

    # case of non-channelized image
    background = np.zeros((*image.shape, total_channels))
    background[:, :, n_channel] = image

    # in case of greyscale make all 3 channels equal to supplied image
    if greyscale:
        for i in range(3):
            background[:, :, i] = image

    # add opacity if needed
    if opacity is not None:
        background[:, :, -1] = opacity * (image != 0).astype(int)

    return background


def convert_kwargs(mode, backend, kwargs):
    """ Update kwargs-dict to match chosen backend: update keys of the dict and
    values in some cases.
    """
    if backend == 'matplotlib':
        # make conversion-dict for kwargs-keys
        if mode in ['single', 'rgb', 'overlap', 'histogram', 'curve', 'histogram']:
            keys_converter = {'title': 'label', 't':'label'}
        elif mode in ['separate']:
            keys_converter = {'title': 't', 'label': 't'}

        keys_converter = {
            **keys_converter,
            'zmin': 'vmin', 'zmax': 'vmax',
            'xaxis': 'xlabel', 'yaxis': 'ylabel'
        }
        # make conversion-procedure for key-value pairs
        def converter(k, v):
            if k in ('xaxis', 'yaxis'):
                return keys_converter[k], v['title_text']
            return keys_converter[k], v
    else:
        # make conversion-dict for kwargs-keys
        keys_converter = {
            'label': 'title', 't': 'title',
            'xlabel': 'xaxis', 'ylabel': 'yaxis',
            'vmin': 'zmin', 'vmax': 'zmax',
        }

        # make conversion-procedure for key-value pairs
        def converter(k, v):
            if k == 'xlabel':
                return keys_converter[k], {'title_text': v,
                                           'automargin': True,
                                           'titlefont': {'size': kwargs.get('fontsize', 30)}}
            if k == 'ylabel':
                return keys_converter[k], {'title_text': v,
                                           'titlefont': {'size': kwargs.get('fontsize', 30)},
                                           'automargin': True,
                                           'autorange': 'reversed'}
            return keys_converter[k], v

    # perform conversion inplace
    for key in keys_converter:
        if key in kwargs:
            value = kwargs.get(key)
            new_k, new_v = converter(key, value)
            kwargs[new_k] = new_v


def filter_kwargs(kwargs, keys):
    """ Filter the dict of kwargs leaving only supplied keys.
    """
    return {key: kwargs[key] for key in keys if key in kwargs}


def plot_image(image, mode='single', backend='matplotlib', **kwargs):
    """ Overall plotter function, converting kwarg-names to match chosen backend and redirecting
    plotting task to one of the methods of backend-classes.
    """
    convert_kwargs(mode, backend, kwargs)
    if backend in ('matplotlib', 'plt', 'mpl', 'm', 'mp'):
        getattr(MatplotlibPlotter(), mode)(image, **kwargs)
    elif backend in ('plotly', 'go'):
        getattr(PlotlyPlotter(), mode)(image, **kwargs)
    else:
        raise ValueError('{} backend is not supported!'.format(backend))


def plot_loss(*data, title=None, **kwargs):
    """ Shorthand for loss plotting. """
    kwargs = {
        'xlabel': 'Iterations',
        'ylabel': 'Loss',
        'label': title or 'Loss graph',
        **kwargs
    }
    plot_image(*data, mode='curve', backend='mpl', **kwargs)


class MatplotlibPlotter:
    """ Plotting backend for matplotlib.
    """
    @staticmethod
    def save_and_show(fig, show=True, savepath=None, **kwargs):
        """ Save and show plot if needed.
        """
        save_kwargs = dict(bbox_inches='tight', pad_inches=0, dpi=100)
        save_kwargs.update(kwargs.get('save', dict()))

        # save if necessary and render
        if savepath is not None:
            fig.savefig(savepath, **save_kwargs)
        if show:
            fig.show()
        else:
            plt.close()

    def single(self, image, **kwargs):
        """ Plot single image/heatmap using matplotlib.

        Parameters
        ----------
        image : np.ndarray
            2d-array for plotting.
        kwargs : dict
            figsize : tuple
                tuple of two ints containing the size of the rendered image.
            label : str
                title of rendered image.
            vmin : float
                the lowest brightness-level to be rendered.
            vmax : float
                the highest brightness-level to be rendered.
            cmap : str
                colormap of rendered image.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            alpha : float
                transparency-level of the rendered image
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # update defaults
        defaults = {'figsize': (12, 7),
                    'cmap': 'viridis_r',
                    'colorbar': True,
                    'fontsize': 20,
                    'fraction': 0.022, 'pad': 0.07,
                    'labeltop': True, 'labelright': True, 'direction': 'inout',
                    'facecolor': 'white',
                    'label': '', 'title': '', 'xlabel': '', 'ylabel': '',
                    'order_axes': (1, 0)}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        figure_kwargs = filter_kwargs(updated, ['figsize', 'facecolor', 'dpi'])
        render_kwargs = filter_kwargs(updated, ['cmap', 'vmin', 'vmax', 'alpha', 'interpolation'])
        label_kwargs = filter_kwargs(updated, ['label', 'y', 'fontsize', 'family', 'color'])
        xaxis_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        yaxis_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])
        tick_params = filter_kwargs(updated, ['labeltop', 'labelright', 'labelcolor', 'direction'])
        colorbar_kwargs = filter_kwargs(updated, ['fraction', 'pad'])

        cm = plt.get_cmap(render_kwargs['cmap'])
        cm.set_bad(color=updated.get('bad_color', updated.get('fill_color', 'white')))
        render_kwargs['cmap'] = cm

        # Create figure and axes
        if 'ax' in kwargs:
            ax = kwargs['ax']
            fig = ax.figure
        else:
            fig, ax = plt.subplots(**figure_kwargs)

        # channelize and plot the image
        img = np.transpose(image.squeeze(), axes=updated['order_axes'])
        xticks, yticks = updated.get('xticks', [0, img.shape[1]]), updated.get('yticks', [img.shape[0], 0])
        extent = [xticks[0], xticks[-1], yticks[0], yticks[-1]]

        ax_img = ax.imshow(img, extent=extent, **render_kwargs)

        # add titles and labels
        ax.set_title(**label_kwargs)
        ax.set_xlabel(**xaxis_kwargs)
        ax.set_ylabel(**yaxis_kwargs)

        if 'xticks' in updated:
            ax.set_xticks(xticks)
        if 'yticks' in updated:
            ax.set_yticks(yticks)

        if updated['colorbar']:
            cb = fig.colorbar(ax_img, **colorbar_kwargs)
            cb.ax.yaxis.set_tick_params(color=yaxis_kwargs.get('color', 'black'))
        ax.set_facecolor(updated['facecolor'])
        ax.tick_params(**tick_params)

        self.save_and_show(fig, **updated)

    def overlap(self, images, **kwargs):
        """ Plot several images on one canvas using matplotlib: render the first one in greyscale
        and the rest ones in 'rgb' channels, one channel for each image.
        Supports up to four images in total.

        Parameters
        ----------
        images : tuple or list
            sequence of 2d-arrays for plotting. Supports up to 4 images.
        kwargs : dict
            figsize : tuple
                tuple of two ints containing the size of the rendered image.
            label : str
                title of rendered image.
            y : float
                height of the title
            cmap : str
                colormap to render the first image in.
            vmin : float
                the lowest brightness-level to be rendered.
            vmax : float
                the highest brightness-level to be rendered.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        defaults = {'figsize': (12, 7),
                    'y' : 1.1,
                    'cmap': 'gray',
                    'fontsize': 20,
                    'opacity': 1.0,
                    'label': '', 'title': '', 'xlabel': '', 'ylabel': '',
                    'order_axes': (1, 0)}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        figure_kwargs = filter_kwargs(updated, ['figsize', 'facecolor', 'dpi'])
        render_kwargs = filter_kwargs(updated, ['cmap', 'vmin', 'vmax', 'interpolation'])
        label_kwargs = filter_kwargs(updated, ['label', 'fontsize', 'family', 'color', 'y'])
        xaxis_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        yaxis_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])

        # Create figure and axes
        if 'ax' in kwargs:
            ax = kwargs['ax']
            fig = ax.figure
        else:
            fig, ax = plt.subplots(**figure_kwargs)

        # channelize images and put them on a canvas
        img = np.transpose(images[0].squeeze(), axes=updated['order_axes'])
        xticks, yticks = updated.get('xticks', [0, img.shape[1]]), updated.get('yticks', [img.shape[0], 0])
        extent = [xticks[0], xticks[-1], yticks[0], yticks[-1]]

        ax.imshow(img, extent=extent, **render_kwargs)
        ax.set_xlabel(**xaxis_kwargs)
        ax.set_ylabel(**yaxis_kwargs)

        if 'xticks' in updated:
            ax.set_xticks(xticks)
        if 'yticks' in updated:
            ax.set_yticks(yticks)

        for img, n_channel in zip(images[1:], (0, 1, 2)):
            ax.imshow(channelize_image(np.transpose(img.squeeze(), axes=updated['order_axes']), total_channels=4,
                                       n_channel=n_channel, opacity=updated['opacity']),
                      extent=extent, **render_kwargs)
        plt.title(**label_kwargs)

        self.save_and_show(fig, **updated)

    def rgb(self, image, **kwargs):
        """ Plot one image in 'rgb' using matplotlib.

        Parameters
        ----------
        image : np.ndarray
            3d-array containing channeled rgb-image.
        kwargs : dict
            figsize : tuple
                tuple of two ints containing the size of the rendered image.
            label : str
                title of rendered image.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # update defaults
        defaults = {'figsize': (12, 7),
                    'fontsize': 20,
                    'labeltop': True,
                    'labelright': True,
                    'order_axes': (1, 0, 2)}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        render_kwargs = filter_kwargs(updated, [])
        figure_kwargs = filter_kwargs(updated, ['figsize', 'facecolor', 'dpi'])
        label_kwargs = filter_kwargs(updated, ['label', 'fontsize', 'family', 'color'])
        xaxis_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        yaxis_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])
        tick_params = filter_kwargs(updated, ['labeltop', 'labelright'])

        # channelize and plot the image
        image = channelize_image(image, total_channels=3)
        plt.figure(**figure_kwargs)
        _ = plt.imshow(np.transpose(image.squeeze(), axes=updated['order_axes']), **render_kwargs)

        # add titles and labels
        plt.title(y=1.1, **label_kwargs)
        plt.xlabel(**xaxis_kwargs)
        plt.ylabel(**yaxis_kwargs)
        plt.tick_params(**tick_params)

        self.save_and_show(plt, **updated)

    def separate(self, images, **kwargs):
        """ Plot several images on a row of canvases using matplotlib.
        TODO: add grid support.

        Parameters
        ----------
        images : tuple or list
            sequence of 2d-arrays for plotting. Supports up to 4 images.
        kwargs : dict
            figsize : tuple
                tuple of two ints containing the size of the rendered image.
            t : str
                overal title of rendered image.
            label : list or tuple
                sequence of titles for each image.
            cmap : str
                colormap to render the first image in.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # embedded params
        defaults = {'figsize': (6 * len(images), 7),
                    'cmap': 'gray',
                    'fontsize': 20,
                    'y': 0.9,
                    'label': ''*len(images), 'title': '', 'xlabel': '', 'ylabel': '',
                    'order_axes': (1, 0)}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        figure_kwargs = filter_kwargs(updated, ['figsize', 'facecolor', 'dpi'])
        render_kwargs = filter_kwargs(updated, ['cmap', 'vmin', 'vmax', 'interpolation'])
        label_kwargs = filter_kwargs(updated, ['t', 'y', 'fontsize', 'family', 'color'])
        xaxis_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        yaxis_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])
        titles_kwargs = filter_kwargs(updated, ['label', 'fontsize', 'family', 'color'])

        grid = (1, len(images))
        fig, ax = plt.subplots(*grid, **figure_kwargs)

        # plot image
        for i, img in enumerate(images):
            args = {key: (value[i] if isinstance(value, list) else value)
                    for key, value in render_kwargs.items()}
            ax[i].imshow(np.transpose(img.squeeze(), axes=updated['order_axes']), **args)

            ax[i].set_xlabel(**xaxis_kwargs)
            ax[i].set_ylabel(**yaxis_kwargs)
            ax[i].set_title(**dict(titles_kwargs, **{'label': updated.get('titles', ' '*(len(images)+1))[i]}))

        fig.suptitle(**label_kwargs)

        self.save_and_show(plt, **updated)

    def histogram(self, image, **kwargs):
        """ Plot histogram using matplotlib.

        Parameters
        ----------
        image : np.ndarray
            2d-image for plotting.
        kwargs : dict
            label : str
                title of rendered image.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            bins : int
                the number of bins to use.
            other
        """
        # update defaults
        defaults = {'figsize': (8, 5),
                    'bins': 50,
                    'density': True,
                    'alpha': 0.75,
                    'facecolor': 'b',
                    'fontsize': 15,
                    'label': '',
                    'xlabel': 'values', 'ylabel': ''}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        figure_kwargs = filter_kwargs(updated, ['figsize', 'dpi'])
        histo_kwargs = filter_kwargs(updated, ['bins', 'density', 'alpha', 'facecolor', 'log'])
        label_kwargs = filter_kwargs(updated, ['label', 'fontsize', 'family', 'color'])
        xlabel_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        ylabel_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])
        xaxis_kwargs = filter_kwargs(updated, ['xlim'])
        yaxis_kwargs = filter_kwargs(updated, ['ylim'])

        # plot the histo
        plt.figure(**figure_kwargs)
        _, _, _ = plt.hist(image.flatten(), **histo_kwargs)
        plt.xlabel(**xlabel_kwargs)
        plt.ylabel(**ylabel_kwargs)
        plt.title(**label_kwargs)
        plt.xlim(xaxis_kwargs.get('xlim'))  # these are positional ones
        plt.ylim(yaxis_kwargs.get('ylim'))

        self.save_and_show(plt, **updated)

    def curve(self, *args, **kwargs):
        """ Plot a curve.

        Parameters
        ----------
        args : tuple
            a sequence containing curves for plotting along with, possibly, specification of
            plot formats. Must at least contain an array of ys, but may also be comprised of
            triples of (xs, ys, fmt) for an arbitrary number of curves.
        kwargs : dict
            label : str
                title of rendered image.
            xlabel : str
                xaxis-label.
            ylabel : str
                yaxis-label.
            fontsize : int
                fontsize of labels and titles.
            curve_labels : list or tuple
                list/tuple of curve-labels
            other
        """
        # defaults
        defaults = {'figsize': (8, 5),
                    'label': 'Curve plot',
                    'xlabel': 'x',
                    'ylabel': 'y',
                    'fontsize': 15,
                    'grid': True,
                    'legend': True}
        updated = {**defaults, **kwargs}

        # form groups of kwargs
        figure_kwargs = filter_kwargs(updated, ['figsize', 'facecolor', 'dpi'])
        label_kwargs = filter_kwargs(updated, ['label', 'fontsize', 'family', 'color'])
        xlabel_kwargs = filter_kwargs(updated, ['xlabel', 'fontsize', 'family', 'color'])
        ylabel_kwargs = filter_kwargs(updated, ['ylabel', 'fontsize', 'family', 'color'])

        # plot the curves
        plt.figure(**figure_kwargs)
        curves = plt.plot(*args)
        if 'curve_labels' in updated:
            plt.legend(curves, updated['curve_labels'])

        plt.xlabel(**xlabel_kwargs)
        plt.ylabel(**ylabel_kwargs)
        plt.title(**label_kwargs)
        plt.grid(updated['grid'])

        self.save_and_show(plt, **updated)




class PlotlyPlotter:
    """ Plotting backend for plotly.
    """
    @staticmethod
    def save_and_show(fig, show=True, savepath=None, **kwargs):
        """ Save and show plot if needed.
        """
        save_kwargs = kwargs.get('save', dict())

        # save if necessary and render
        if savepath is not None:
            fig.write_image(savepath, **save_kwargs)
        if show:
            fig.show()
        else:
            fig.close()

    def single(self, image, **kwargs):
        """ Plot single image/heatmap using plotly.

        Parameters
        ----------
        image : np.ndarray
            2d-array for plotting.
        kwargs : dict
            max_size : int
                maximum size of a rendered image.
            title : str
                title of rendered image.
            zmin : float
                the lowest brightness-level to be rendered.
            zmax : float
                the highest brightness-level to be rendered.
            opacity : float
                transparency-level of the rendered image
            xaxis : dict
                controls the properties of xaxis-labels; uses plotly-format.
            yaxis : dict
                controls the properties of yaxis-labels; uses plotly-format.
            slice : tuple
                sequence of slice-objects for slicing the image to a lesser one.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # update defaults to make total dict of kwargs
        defaults = {'reversescale': True,
                    'colorscale': 'viridis',
                    'opacity' : 1.0,
                    'max_size' : 600,
                    'order_axes': (1, 0),
                    'slice': (slice(None, None), slice(None, None))}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        render_kwargs = filter_kwargs(updated, ['reversescale', 'colorscale', 'opacity', 'showscale'])
        label_kwargs = filter_kwargs(updated, ['xaxis', 'yaxis', 'coloraxis_colorbar', 'title'])
        slc = updated['slice']

        # calculate canvas sizes
        width, height = image.shape[1], image.shape[0]
        coeff = updated['max_size'] / max(width, height)
        width = coeff * width
        height = coeff * height

        # plot the image and set titles
        plot_data = go.Heatmap(z=np.transpose(image, axes=updated['order_axes'])[slc], **render_kwargs)
        fig = go.Figure(data=plot_data)
        fig.update_layout(width=width, height=height, **label_kwargs)

        self.save_and_show(fig, **updated)

    def overlap(self, images, **kwargs):
        """ Plot several images on one canvas using plotly: render the first one in greyscale
        and the rest ones in opaque 'rgb' channels, one channel for each image.
        Supports up to four images in total.

        Parameters
        ----------
        images : list/tuple
            sequence of 2d-arrays for plotting. Can store up to four images.
        kwargs : dict
            max_size : int
                maximum size of a rendered image.
            title : str
                title of rendered image.
            opacity : float
                opacity of 'rgb' channels.
            xaxis : dict
                controls the properties of xaxis-labels; uses plotly-format.
            yaxis : dict
                controls the properties of yaxis-labels; uses plotly-format.
            slice : tuple
                sequence of slice-objects for slicing the image to a lesser one.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # update defaults to make total dict of kwargs
        defaults = {'coloraxis_colorbar': {'title': 'amplitude'},
                    'opacity' : 1.0,
                    'title': 'Seismic inline',
                    'max_size' : 600,
                    'order_axes': (1, 0),
                    'slice': (slice(None, None), slice(None, None))}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        render_kwargs = filter_kwargs(updated, ['zmin', 'zmax'])
        label_kwargs = filter_kwargs(updated, ['xaxis', 'yaxis', 'coloraxis_colorbar', 'title'])
        slc = updated['slice']

        # calculate canvas sizes
        width, height = images[0].shape[1], images[0].shape[0]
        coeff = updated['max_size'] / max(width, height)
        width = coeff * width
        height = coeff * height

        # manually combine first image in greyscale and the rest ones colored differently
        combined = channelize_image(255 * np.transpose(images[0], axes=updated['order_axes']),
                                    total_channels=4, greyscale=True)
        for img, n_channel in zip(images[1:], (0, 1, 2)):
            combined += channelize_image(255 * np.transpose(img, axes=updated['order_axes']),
                                         total_channels=4, n_channel=n_channel, opacity=updated['opacity'])
        plot_data = go.Image(z=combined[slc], **render_kwargs) # plot manually combined image

        # plot the figure
        fig = go.Figure(data=plot_data)
        fig.update_layout(width=width, height=height, **label_kwargs)

        self.save_and_show(fig, **updated)

    def rgb(self, image, **kwargs):
        """ Plot one image in 'rgb' using plotly.

        Parameters
        ----------
        image : np.ndarray
            3d-array containing channeled rgb-image.
        kwargs : dict
            max_size : int
                maximum size of a rendered image.
            title : str
                title of the rendered image.
            xaxis : dict
                controls the properties of xaxis-labels; uses plotly-format.
            yaxis : dict
                controls the properties of yaxis-labels; uses plotly-format.
            slice : tuple
                sequence of slice-objects for slicing the image to a lesser one.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # update defaults to make total dict of kwargs
        defaults = {'coloraxis_colorbar': {'title': 'depth'},
                    'max_size' : 600,
                    'order_axes': (1, 0, 2),
                    'slice': (slice(None, None), slice(None, None))}
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        render_kwargs = filter_kwargs(updated, [])
        label_kwargs = filter_kwargs(updated, ['xaxis', 'yaxis', 'coloraxis_colorbar', 'title'])
        slc = updated['slice']

        # calculate canvas sizes
        width, height = image.shape[1], image.shape[0]
        coeff = updated['max_size'] / max(width, height)
        width = coeff * width
        height = coeff * height

        # plot the image and set titles
        plot_data = go.Image(z=np.transpose(image, axes=updated['order_axes'])[slc], **render_kwargs)
        fig = go.Figure(data=plot_data)
        fig.update_layout(width=width, height=height, **label_kwargs)

        self.save_and_show(fig, **updated)

    def separate(self, images, **kwargs):
        """ Plot several images on a row of canvases using plotly.
        TODO: add grid support.

        Parameters
        ----------
        images : list/tuple
            sequence of 2d-arrays for plotting.
        kwargs : dict
            max_size : int
                maximum size of a rendered image.
            title : str
                title of rendered image.
            xaxis : dict
                controls the properties of xaxis-labels; uses plotly-format.
            yaxis : dict
                controls the properties of yaxis-labels; uses plotly-format.
            slice : tuple
                sequence of slice-objects for slicing the image to a lesser one.
            order_axes : tuple
                tuple of ints; defines the order of axes for transposition operation
                applied to the image.
            other
        """
        # defaults
        defaults = {'max_size' : 600,
                    'order_axes': (1, 0),
                    'slice': (slice(None, None), slice(None, None))}
        grid = (1, len(images))
        updated = {**defaults, **kwargs}

        # form different groups of kwargs
        render_kwargs = filter_kwargs(updated, [])
        label_kwargs = filter_kwargs(updated, ['title'])
        xaxis_kwargs = filter_kwargs(updated, ['xaxis'])
        yaxis_kwargs = filter_kwargs(updated, ['yaxis'])
        slc = updated['slice']

        # make sure that the images are greyscale and put them each on separate canvas
        fig = make_subplots(rows=grid[0], cols=grid[1])
        for i in range(grid[1]):
            img = channelize_image(255 * np.transpose(images[i], axes=updated['order_axes']),
                                   total_channels=4, greyscale=True, opacity=1)
            fig.add_trace(go.Image(z=img[slc], **render_kwargs), row=1, col=i + 1)
            fig.update_xaxes(row=1, col=i + 1, **xaxis_kwargs['xaxis'])
            fig.update_yaxes(row=1, col=i + 1, **yaxis_kwargs['yaxis'])
        fig.update_layout(**label_kwargs)

        self.save_and_show(fig, **updated)
