# Copyright (c) OpenMMLab. All rights reserved.
import inspect
import math
import random
from numbers import Number
from typing import Dict, Optional, Sequence, Tuple, Union

import mmcv
import numpy as np
from mmcv.transforms import BaseTransform
from mmcv.transforms.utils import cache_randomness

from mmcls.registry import TRANSFORMS
from .compose import Compose

try:
    import albumentations
except ImportError:
    albumentations = None


@TRANSFORMS.register_module()
class RandomCrop(BaseTransform):
    """Crop the given Image at a random location.

    Required Keys:

    - img

    Modified Keys:

    - img
    - img_shape

    Args:
        crop_size (sequence or int): Desired output size of the crop. If
            crop_size is an int instead of sequence like (h, w), a square crop
            (crop_size, crop_size) is made.
        padding (int or sequence, optional): Optional padding on each border
            of the image. If a sequence of length 4 is provided, it is used to
            pad left, top, right, bottom borders respectively.  If a sequence
            of length 2 is provided, it is used to pad left/right, top/bottom
            borders, respectively. Default: None, which means no padding.
        pad_if_needed (boolean): It will pad the image if smaller than the
            desired size to avoid raising an exception. Since cropping is done
            after padding, the padding seems to be done at a random offset.
            Default: False.
        pad_val (Number | Sequence[Number]): Pixel pad_val value for constant
            fill. If a tuple of length 3, it is used to pad_val R, G, B
            channels respectively. Default: 0.
        padding_mode (str): Type of padding. Defaults to "constant". Should
            be one of the following:

            - constant: Pads with a constant value, this value is specified \
                with pad_val.
            - edge: pads with the last value at the edge of the image.
            - reflect: Pads with reflection of image without repeating the \
                last value on the edge. For example, padding [1, 2, 3, 4] \
                with 2 elements on both sides in reflect mode will result \
                in [3, 2, 1, 2, 3, 4, 3, 2].
            - symmetric: Pads with reflection of image repeating the last \
                value on the edge. For example, padding [1, 2, 3, 4] with \
                2 elements on both sides in symmetric mode will result in \
                [2, 1, 1, 2, 3, 4, 4, 3].
    """

    def __init__(self,
                 crop_size: Union[Sequence, int],
                 padding: Optional[Union[Sequence, int]] = None,
                 pad_if_needed: bool = False,
                 pad_val: Union[Number, Sequence[Number]] = 0,
                 padding_mode: str = 'constant') -> None:
        if isinstance(crop_size, Sequence):
            assert len(crop_size) == 2
            assert crop_size[0] > 0 and crop_size[1] > 0
            self.crop_size = crop_size
        else:
            assert crop_size > 0
            self.crop_size = (crop_size, crop_size)
        # check padding mode
        assert padding_mode in ['constant', 'edge', 'reflect', 'symmetric']
        self.padding = padding
        self.pad_if_needed = pad_if_needed
        self.pad_val = pad_val
        self.padding_mode = padding_mode

    @cache_randomness
    def rand_crop_params(self, img: np.ndarray):
        """Get parameters for ``crop`` for a random crop.

        Args:
            img (ndarray): Image to be cropped.

        Returns:
            tuple: Params (offset_h, offset_w, target_h, target_w) to be
                passed to ``crop`` for random crop.
        """
        h, w = img.shape[:2]
        target_h, target_w = self.crop_size
        if w == target_w and h == target_h:
            return 0, 0, h, w
        elif w < target_w or h < target_h:
            target_w = min(w, target_w)
            target_h = min(w, target_h)

        offset_h = np.random.randint(0, h - target_h + 1)
        offset_w = np.random.randint(0, w - target_w + 1)

        return offset_h, offset_w, target_h, target_w

    def transform(self, results: dict) -> dict:
        """Transform function to randomly crop images.

        Args:
            results (dict): Result dict from loading pipeline.

        Returns:
            dict: Randomly cropped results, 'img_shape'
                key in result dict is updated according to crop size.
        """
        img = results['img']
        if self.padding is not None:
            img = mmcv.impad(img, padding=self.padding, pad_val=self.pad_val)

        # pad img if needed
        if self.pad_if_needed:
            h_pad = math.ceil(max(0, self.crop_size[0] - img.shape[0]) / 2)
            w_pad = math.ceil(max(0, self.crop_size[1] - img.shape[1]) / 2)

            img = mmcv.impad(
                img,
                padding=(w_pad, h_pad, w_pad, h_pad),
                pad_val=self.pad_val,
                padding_mode=self.padding_mode)

        offset_h, offset_w, target_h, target_w = self.rand_crop_params(img)
        img = mmcv.imcrop(
            img,
            np.array([
                offset_w,
                offset_h,
                offset_w + target_w - 1,
                offset_h + target_h - 1,
            ]))
        results['img'] = img
        results['img_shape'] = img.shape

        return results

    def __repr__(self):
        """Print the basic information of the transform.

        Returns:
            str: Formatted string.
        """
        repr_str = self.__class__.__name__ + f'(crop_size={self.crop_size}'
        repr_str += f', padding={self.padding}'
        repr_str += f', pad_if_needed={self.pad_if_needed}'
        repr_str += f', pad_val={self.pad_val}'
        repr_str += f', padding_mode={self.padding_mode})'
        return repr_str


@TRANSFORMS.register_module()
class RandomResizedCrop(BaseTransform):
    """Crop the given image to random scale and aspect ratio.

    A crop of random size (default: of 0.08 to 1.0) of the original size and a
    random aspect ratio (default: of 3/4 to 4/3) of the original aspect ratio
    is made. This crop is finally resized to given size.

    Required Keys:

    - img

    Modified Keys:

    - img
    - img_shape

    Args:
        scale (sequence | int): Desired output scale of the crop. If size is an
            int instead of sequence like (h, w), a square crop (size, size) is
            made.
        crop_ratio_range (tuple): Range of the random size of the cropped
            image compared to the original image. Defaults to (0.08, 1.0).
        aspect_ratio_range (tuple): Range of the random aspect ratio of the
            cropped image compared to the original image.
            Defaults to (3. / 4., 4. / 3.).
        max_attempts (int): Maximum number of attempts before falling back to
            Central Crop. Defaults to 10.
        interpolation (str): Interpolation method, accepted values are
            'nearest', 'bilinear', 'bicubic', 'area', 'lanczos'. Defaults to
            'bilinear'.
        backend (str): The image resize backend type, accepted values are
            `cv2` and `pillow`. Defaults to `cv2`.
    """

    def __init__(self,
                 scale: Union[Sequence, int],
                 crop_ratio_range: Tuple[float, float] = (0.08, 1.0),
                 aspect_ratio_range: Tuple[float, float] = (3. / 4., 4. / 3.),
                 max_attempts: int = 10,
                 interpolation: str = 'bilinear',
                 backend: str = 'cv2') -> None:
        if isinstance(scale, Sequence):
            assert len(scale) == 2
            assert scale[0] > 0 and scale[1] > 0
            self.scale = scale
        else:
            assert scale > 0
            self.scale = (scale, scale)
        if (crop_ratio_range[0] > crop_ratio_range[1]) or (
                aspect_ratio_range[0] > aspect_ratio_range[1]):
            raise ValueError(
                'range should be of kind (min, max). '
                f'But received crop_ratio_range {crop_ratio_range} '
                f'and aspect_ratio_range {aspect_ratio_range}.')
        assert isinstance(max_attempts, int) and max_attempts >= 0, \
            'max_attempts mush be int and no less than 0.'
        assert interpolation in ('nearest', 'bilinear', 'bicubic', 'area',
                                 'lanczos')

        self.crop_ratio_range = crop_ratio_range
        self.aspect_ratio_range = aspect_ratio_range
        self.max_attempts = max_attempts
        self.interpolation = interpolation
        self.backend = backend

    @cache_randomness
    def rand_crop_params(self, img: np.ndarray) -> Tuple[int, int, int, int]:
        """Get parameters for ``crop`` for a random sized crop.

        Args:
            img (ndarray): Image to be cropped.

        Returns:
            tuple: Params (offset_h, offset_w, target_h, target_w) to be
                passed to `crop` for a random sized crop.
        """
        h, w = img.shape[:2]
        area = h * w

        for _ in range(self.max_attempts):
            target_area = np.random.uniform(*self.crop_ratio_range) * area
            log_ratio = (math.log(self.aspect_ratio_range[0]),
                         math.log(self.aspect_ratio_range[1]))
            aspect_ratio = math.exp(np.random.uniform(*log_ratio))
            target_w = int(round(math.sqrt(target_area * aspect_ratio)))
            target_h = int(round(math.sqrt(target_area / aspect_ratio)))

            if 0 < target_w <= w and 0 < target_h <= h:
                offset_h = np.random.randint(0, h - target_h + 1)
                offset_w = np.random.randint(0, w - target_w + 1)

                return offset_h, offset_w, target_h, target_w

        # Fallback to central crop
        in_ratio = float(w) / float(h)
        if in_ratio < min(self.aspect_ratio_range):
            target_w = w
            target_h = int(round(target_w / min(self.aspect_ratio_range)))
        elif in_ratio > max(self.aspect_ratio_range):
            target_h = h
            target_w = int(round(target_h * max(self.aspect_ratio_range)))
        else:  # whole image
            target_w = w
            target_h = h
        offset_h = (h - target_h) // 2
        offset_w = (w - target_w) // 2
        return offset_h, offset_w, target_h, target_w

    def transform(self, results: dict) -> dict:
        """Transform function to randomly resized crop images.

        Args:
            results (dict): Result dict from loading pipeline.

        Returns:
            dict: Randomly resized cropped results, 'img_shape'
                key in result dict is updated according to crop size.
        """
        img = results['img']
        offset_h, offset_w, target_h, target_w = self.rand_crop_params(img)
        img = mmcv.imcrop(
            img,
            bboxes=np.array([
                offset_w, offset_h, offset_w + target_w - 1,
                offset_h + target_h - 1
            ]))
        img = mmcv.imresize(
            img,
            tuple(self.scale[::-1]),
            interpolation=self.interpolation,
            backend=self.backend)
        results['img'] = img
        results['img_shape'] = img.shape

        return results

    def __repr__(self):
        """Print the basic information of the transform.

        Returns:
            str: Formatted string.
        """
        repr_str = self.__class__.__name__ + f'(scale={self.scale}'
        repr_str += ', crop_ratio_range='
        repr_str += f'{tuple(round(s, 4) for s in self.crop_ratio_range)}'
        repr_str += ', aspect_ratio_range='
        repr_str += f'{tuple(round(r, 4) for r in self.aspect_ratio_range)}'
        repr_str += f', max_attempts={self.max_attempts}'
        repr_str += f', interpolation={self.interpolation}'
        repr_str += f', backend={self.backend})'
        return repr_str


@TRANSFORMS.register_module()
class RandomGrayscale(object):
    """Randomly convert image to grayscale with a probability of gray_prob.

    Args:
        gray_prob (float): Probability that image should be converted to
            grayscale. Default: 0.1.

    Returns:
        ndarray: Image after randomly grayscale transform.

    Notes:
        - If input image is 1 channel: grayscale version is 1 channel.
        - If input image is 3 channel: grayscale version is 3 channel
          with r == g == b.
    """

    def __init__(self, gray_prob=0.1):
        self.gray_prob = gray_prob

    def __call__(self, results):
        """
        Args:
            img (ndarray): Image to be converted to grayscale.

        Returns:
            ndarray: Randomly grayscaled image.
        """
        for key in results.get('img_fields', ['img']):
            img = results[key]
            num_output_channels = img.shape[2]
            if random.random() < self.gray_prob:
                if num_output_channels > 1:
                    img = mmcv.rgb2gray(img)[:, :, None]
                    results[key] = np.dstack(
                        [img for _ in range(num_output_channels)])
                    return results
            results[key] = img
        return results

    def __repr__(self):
        return self.__class__.__name__ + f'(gray_prob={self.gray_prob})'


@TRANSFORMS.register_module()
class RandomErasing(BaseTransform):
    """Randomly selects a rectangle region in an image and erase pixels.

    Args:
        erase_prob (float): Probability that image will be randomly erased.
            Default: 0.5
        min_area_ratio (float): Minimum erased area / input image area
            Default: 0.02
        max_area_ratio (float): Maximum erased area / input image area
            Default: 0.4
        aspect_range (sequence | float): Aspect ratio range of erased area.
            if float, it will be converted to (aspect_ratio, 1/aspect_ratio)
            Default: (3/10, 10/3)
        mode (str): Fill method in erased area, can be:

            - const (default): All pixels are assign with the same value.
            - rand: each pixel is assigned with a random value in [0, 255]

        fill_color (sequence | Number): Base color filled in erased area.
            Defaults to (128, 128, 128).
        fill_std (sequence | Number, optional): If set and ``mode`` is 'rand',
            fill erased area with random color from normal distribution
            (mean=fill_color, std=fill_std); If not set, fill erased area with
            random color from uniform distribution (0~255). Defaults to None.

    Note:
        See `Random Erasing Data Augmentation
        <https://arxiv.org/pdf/1708.04896.pdf>`_

        This paper provided 4 modes: RE-R, RE-M, RE-0, RE-255, and use RE-M as
        default. The config of these 4 modes are:

        - RE-R: RandomErasing(mode='rand')
        - RE-M: RandomErasing(mode='const', fill_color=(123.67, 116.3, 103.5))
        - RE-0: RandomErasing(mode='const', fill_color=0)
        - RE-255: RandomErasing(mode='const', fill_color=255)
    """

    def __init__(self,
                 erase_prob=0.5,
                 min_area_ratio=0.02,
                 max_area_ratio=0.4,
                 aspect_range=(3 / 10, 10 / 3),
                 mode='const',
                 fill_color=(128, 128, 128),
                 fill_std=None):
        assert isinstance(erase_prob, float) and 0. <= erase_prob <= 1.
        assert isinstance(min_area_ratio, float) and 0. <= min_area_ratio <= 1.
        assert isinstance(max_area_ratio, float) and 0. <= max_area_ratio <= 1.
        assert min_area_ratio <= max_area_ratio, \
            'min_area_ratio should be smaller than max_area_ratio'
        if isinstance(aspect_range, float):
            aspect_range = min(aspect_range, 1 / aspect_range)
            aspect_range = (aspect_range, 1 / aspect_range)
        assert isinstance(aspect_range, Sequence) and len(aspect_range) == 2 \
            and all(isinstance(x, float) for x in aspect_range), \
            'aspect_range should be a float or Sequence with two float.'
        assert all(x > 0 for x in aspect_range), \
            'aspect_range should be positive.'
        assert aspect_range[0] <= aspect_range[1], \
            'In aspect_range (min, max), min should be smaller than max.'
        assert mode in ['const', 'rand']
        if isinstance(fill_color, Number):
            fill_color = [fill_color] * 3
        assert isinstance(fill_color, Sequence) and len(fill_color) == 3 \
            and all(isinstance(x, Number) for x in fill_color), \
            'fill_color should be a float or Sequence with three int.'
        if fill_std is not None:
            if isinstance(fill_std, Number):
                fill_std = [fill_std] * 3
            assert isinstance(fill_std, Sequence) and len(fill_std) == 3 \
                and all(isinstance(x, Number) for x in fill_std), \
                'fill_std should be a float or Sequence with three int.'

        self.erase_prob = erase_prob
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.aspect_range = aspect_range
        self.mode = mode
        self.fill_color = fill_color
        self.fill_std = fill_std

    def _fill_pixels(self, img, top, left, h, w):
        """Fill pixels to the patch of image."""
        if self.mode == 'const':
            patch = np.empty((h, w, 3), dtype=np.uint8)
            patch[:, :] = np.array(self.fill_color, dtype=np.uint8)
        elif self.fill_std is None:
            # Uniform distribution
            patch = np.random.uniform(0, 256, (h, w, 3)).astype(np.uint8)
        else:
            # Normal distribution
            patch = np.random.normal(self.fill_color, self.fill_std, (h, w, 3))
            patch = np.clip(patch.astype(np.int32), 0, 255).astype(np.uint8)

        img[top:top + h, left:left + w] = patch
        return img

    @cache_randomness
    def random_disable(self):
        """Randomly disable the transform."""
        return np.random.rand() > self.erase_prob

    @cache_randomness
    def random_patch(self, img_h, img_w):
        """Randomly generate patch the erase."""
        # convert the aspect ratio to log space to equally handle width and
        # height.
        log_aspect_range = np.log(
            np.array(self.aspect_range, dtype=np.float32))
        aspect_ratio = np.exp(np.random.uniform(*log_aspect_range))
        area = img_h * img_w
        area *= np.random.uniform(self.min_area_ratio, self.max_area_ratio)

        h = min(int(round(np.sqrt(area * aspect_ratio))), img_h)
        w = min(int(round(np.sqrt(area / aspect_ratio))), img_w)
        top = np.random.randint(0, img_h - h) if img_h > h else 0
        left = np.random.randint(0, img_w - w) if img_w > w else 0
        return top, left, h, w

    def transform(self, results):
        """
        Args:
            results (dict): Results dict from pipeline

        Returns:
            dict: Results after the transformation.
        """
        if self.random_disable():
            return results

        img = results['img']
        img_h, img_w = img.shape[:2]

        img = self._fill_pixels(img, *self.random_patch(img_h, img_w))

        results['img'] = img

        return results

    def __repr__(self):
        repr_str = self.__class__.__name__
        repr_str += f'(erase_prob={self.erase_prob}, '
        repr_str += f'min_area_ratio={self.min_area_ratio}, '
        repr_str += f'max_area_ratio={self.max_area_ratio}, '
        repr_str += f'aspect_range={self.aspect_range}, '
        repr_str += f'mode={self.mode}, '
        repr_str += f'fill_color={self.fill_color}, '
        repr_str += f'fill_std={self.fill_std})'
        return repr_str


@TRANSFORMS.register_module()
class Pad(object):
    """Pad images.

    Args:
        size (tuple[int] | None): Expected padding size (h, w). Conflicts with
                pad_to_square. Defaults to None.
        pad_to_square (bool): Pad any image to square shape. Defaults to False.
        pad_val (Number | Sequence[Number]): Values to be filled in padding
            areas when padding_mode is 'constant'. Default to 0.
        padding_mode (str): Type of padding. Should be: constant, edge,
            reflect or symmetric. Default to "constant".
    """

    def __init__(self,
                 size=None,
                 pad_to_square=False,
                 pad_val=0,
                 padding_mode='constant'):
        assert (size is None) ^ (pad_to_square is False), \
            'Only one of [size, pad_to_square] should be given, ' \
            f'but get {(size is not None) + (pad_to_square is not False)}'
        self.size = size
        self.pad_to_square = pad_to_square
        self.pad_val = pad_val
        self.padding_mode = padding_mode

    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            if self.pad_to_square:
                target_size = tuple(
                    max(img.shape[0], img.shape[1]) for _ in range(2))
            else:
                target_size = self.size
            img = mmcv.impad(
                img,
                shape=target_size,
                pad_val=self.pad_val,
                padding_mode=self.padding_mode)
            results[key] = img
            results['img_shape'] = img.shape
        return results

    def __repr__(self):
        repr_str = self.__class__.__name__
        repr_str += f'(size={self.size}, '
        repr_str += f'(pad_val={self.pad_val}, '
        repr_str += f'padding_mode={self.padding_mode})'
        return repr_str


@TRANSFORMS.register_module()
class ResizeEdge(BaseTransform):
    """Resize images along the specified edge.

    Required Keys:

    - img

    Modified Keys:

    - img
    - img_shape

    Added Keys:

    - scale
    - scale_factor

    Args:
        scale (int): The edge scale to resizing.
        edge (str): The edge to resize. Defaults to 'short'.
        backend (str): Image resize backend, choices are 'cv2' and 'pillow'.
            These two backends generates slightly different results.
            Defaults to 'cv2'.
        interpolation (str): Interpolation method, accepted values are
            "nearest", "bilinear", "bicubic", "area", "lanczos" for 'cv2'
            backend, "nearest", "bilinear" for 'pillow' backend.
            Defaults to 'bilinear'.
    """

    def __init__(self,
                 scale: int,
                 edge: str = 'short',
                 backend: str = 'cv2',
                 interpolation: str = 'bilinear') -> None:
        allow_edges = ['short', 'long', 'width', 'height']
        assert edge in allow_edges, \
            f'Invalid edge "{edge}", please specify from {allow_edges}.'
        self.edge = edge
        self.scale = scale
        self.backend = backend
        self.interpolation = interpolation

    def _resize_img(self, results: dict) -> None:
        """Resize images with ``results['scale']``."""

        img, w_scale, h_scale = mmcv.imresize(
            results['img'],
            results['scale'],
            interpolation=self.interpolation,
            return_scale=True,
            backend=self.backend)
        results['img'] = img
        results['img_shape'] = img.shape[:2]
        results['scale'] = img.shape[:2][::-1]
        results['scale_factor'] = (w_scale, h_scale)

    def transform(self, results: Dict) -> Dict:
        """Transform function to resize images.

        Args:
            results (dict): Result dict from loading pipeline.

        Returns:
            dict: Resized results, 'img', 'scale', 'scale_factor',
            'img_shape' keys are updated in result dict.
        """
        assert 'img' in results, 'No `img` field in the input.'

        h, w = results['img'].shape[:2]
        if any([
                # conditions to resize the width
                self.edge == 'short' and w < h,
                self.edge == 'long' and w > h,
                self.edge == 'width',
        ]):
            width = self.scale
            height = int(self.scale * h / w)
        else:
            height = self.scale
            width = int(self.scale * w / h)
        results['scale'] = (width, height)

        self._resize_img(results)
        return results

    def __repr__(self):
        """Print the basic information of the transform.

        Returns:
            str: Formatted string.
        """
        repr_str = self.__class__.__name__
        repr_str += f'(scale={self.scale}, '
        repr_str += f'edge={self.edge}, '
        repr_str += f'backend={self.backend}, '
        repr_str += f'interpolation={self.interpolation})'
        return repr_str


@TRANSFORMS.register_module()
class Normalize(object):
    """Normalize the image.

    Args:
        mean (sequence): Mean values of 3 channels.
        std (sequence): Std values of 3 channels.
        to_rgb (bool): Whether to convert the image from BGR to RGB,
            default is true.
    """

    def __init__(self, mean, std, to_rgb=True):
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)
        self.to_rgb = to_rgb

    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            results[key] = mmcv.imnormalize(results[key], self.mean, self.std,
                                            self.to_rgb)
        results['img_norm_cfg'] = dict(
            mean=self.mean, std=self.std, to_rgb=self.to_rgb)
        return results

    def __repr__(self):
        repr_str = self.__class__.__name__
        repr_str += f'(mean={list(self.mean)}, '
        repr_str += f'std={list(self.std)}, '
        repr_str += f'to_rgb={self.to_rgb})'
        return repr_str


@TRANSFORMS.register_module()
class ColorJitter(object):
    """Randomly change the brightness, contrast and saturation of an image.

    Args:
        brightness (float): How much to jitter brightness.
            brightness_factor is chosen uniformly from
            [max(0, 1 - brightness), 1 + brightness].
        contrast (float): How much to jitter contrast.
            contrast_factor is chosen uniformly from
            [max(0, 1 - contrast), 1 + contrast].
        saturation (float): How much to jitter saturation.
            saturation_factor is chosen uniformly from
            [max(0, 1 - saturation), 1 + saturation].
    """

    def __init__(self, brightness, contrast, saturation):
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation

    def __call__(self, results):
        brightness_factor = random.uniform(0, self.brightness)
        contrast_factor = random.uniform(0, self.contrast)
        saturation_factor = random.uniform(0, self.saturation)
        color_jitter_transforms = [
            dict(
                type='Brightness',
                magnitude=brightness_factor,
                prob=1.,
                random_negative_prob=0.5),
            dict(
                type='Contrast',
                magnitude=contrast_factor,
                prob=1.,
                random_negative_prob=0.5),
            dict(
                type='ColorTransform',
                magnitude=saturation_factor,
                prob=1.,
                random_negative_prob=0.5)
        ]
        random.shuffle(color_jitter_transforms)
        transform = Compose(color_jitter_transforms)
        return transform(results)

    def __repr__(self):
        repr_str = self.__class__.__name__
        repr_str += f'(brightness={self.brightness}, '
        repr_str += f'contrast={self.contrast}, '
        repr_str += f'saturation={self.saturation})'
        return repr_str


@TRANSFORMS.register_module()
class Lighting(object):
    """Adjust images lighting using AlexNet-style PCA jitter.

    Args:
        eigval (list): the eigenvalue of the convariance matrix of pixel
            values, respectively.
        eigvec (list[list]): the eigenvector of the convariance matrix of pixel
            values, respectively.
        alphastd (float): The standard deviation for distribution of alpha.
            Defaults to 0.1
        to_rgb (bool): Whether to convert img to rgb.
    """

    def __init__(self, eigval, eigvec, alphastd=0.1, to_rgb=True):
        assert isinstance(eigval, list), \
            f'eigval must be of type list, got {type(eigval)} instead.'
        assert isinstance(eigvec, list), \
            f'eigvec must be of type list, got {type(eigvec)} instead.'
        for vec in eigvec:
            assert isinstance(vec, list) and len(vec) == len(eigvec[0]), \
                'eigvec must contains lists with equal length.'
        self.eigval = np.array(eigval)
        self.eigvec = np.array(eigvec)
        self.alphastd = alphastd
        self.to_rgb = to_rgb

    def __call__(self, results):
        for key in results.get('img_fields', ['img']):
            img = results[key]
            results[key] = mmcv.adjust_lighting(
                img,
                self.eigval,
                self.eigvec,
                alphastd=self.alphastd,
                to_rgb=self.to_rgb)
        return results

    def __repr__(self):
        repr_str = self.__class__.__name__
        repr_str += f'(eigval={self.eigval.tolist()}, '
        repr_str += f'eigvec={self.eigvec.tolist()}, '
        repr_str += f'alphastd={self.alphastd}, '
        repr_str += f'to_rgb={self.to_rgb})'
        return repr_str


@TRANSFORMS.register_module()
class Albu(object):
    """Albumentation augmentation.

    Adds custom transformations from Albumentations library.
    Please, visit `https://albumentations.readthedocs.io`
    to get more information.
    An example of ``transforms`` is as followed:

    .. code-block::
        [
            dict(
                type='ShiftScaleRotate',
                shift_limit=0.0625,
                scale_limit=0.0,
                rotate_limit=0,
                interpolation=1,
                p=0.5),
            dict(
                type='RandomBrightnessContrast',
                brightness_limit=[0.1, 0.3],
                contrast_limit=[0.1, 0.3],
                p=0.2),
            dict(type='ChannelShuffle', p=0.1),
            dict(
                type='OneOf',
                transforms=[
                    dict(type='Blur', blur_limit=3, p=1.0),
                    dict(type='MedianBlur', blur_limit=3, p=1.0)
                ],
                p=0.1),
        ]

    Args:
        transforms (list[dict]): A list of albu transformations
        keymap (dict): Contains {'input key':'albumentation-style key'}
    """

    def __init__(self, transforms, keymap=None, update_pad_shape=False):
        if albumentations is None:
            raise RuntimeError('albumentations is not installed')
        else:
            from albumentations import Compose

        self.transforms = transforms
        self.filter_lost_elements = False
        self.update_pad_shape = update_pad_shape

        self.aug = Compose([self.albu_builder(t) for t in self.transforms])

        if not keymap:
            self.keymap_to_albu = {
                'img': 'image',
            }
        else:
            self.keymap_to_albu = keymap
        self.keymap_back = {v: k for k, v in self.keymap_to_albu.items()}

    def albu_builder(self, cfg):
        """Import a module from albumentations.

        It inherits some of :func:`build_from_cfg` logic.
        Args:
            cfg (dict): Config dict. It should at least contain the key "type".
        Returns:
            obj: The constructed object.
        """

        assert isinstance(cfg, dict) and 'type' in cfg
        args = cfg.copy()

        obj_type = args.pop('type')
        if mmcv.is_str(obj_type):
            if albumentations is None:
                raise RuntimeError('albumentations is not installed')
            obj_cls = getattr(albumentations, obj_type)
        elif inspect.isclass(obj_type):
            obj_cls = obj_type
        else:
            raise TypeError(
                f'type must be a str or valid type, but got {type(obj_type)}')

        if 'transforms' in args:
            args['transforms'] = [
                self.albu_builder(transform)
                for transform in args['transforms']
            ]

        return obj_cls(**args)

    @staticmethod
    def mapper(d, keymap):
        """Dictionary mapper.

        Renames keys according to keymap provided.
        Args:
            d (dict): old dict
            keymap (dict): {'old_key':'new_key'}
        Returns:
            dict: new dict.
        """

        updated_dict = {}
        for k, v in zip(d.keys(), d.values()):
            new_k = keymap.get(k, k)
            updated_dict[new_k] = d[k]
        return updated_dict

    def __call__(self, results):
        # dict to albumentations format
        results = self.mapper(results, self.keymap_to_albu)

        results = self.aug(**results)

        if 'gt_labels' in results:
            if isinstance(results['gt_labels'], list):
                results['gt_labels'] = np.array(results['gt_labels'])
            results['gt_labels'] = results['gt_labels'].astype(np.int64)

        # back to the original format
        results = self.mapper(results, self.keymap_back)

        # update final shape
        if self.update_pad_shape:
            results['pad_shape'] = results['img'].shape

        return results

    def __repr__(self):
        repr_str = self.__class__.__name__ + f'(transforms={self.transforms})'
        return repr_str
