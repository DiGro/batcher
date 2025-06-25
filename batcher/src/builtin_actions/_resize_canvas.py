"""Built-in "Resize canvas" action."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src.procedure_groups import *

from . import _utils as builtin_actions_utils


__all__ = [
  'ResizeModes',
  'resize_canvas',
  'on_after_add_resize_canvas_action',
]


class ResizeModes:
  RESIZE_MODES = (
    RESIZE_FROM_EDGES,
    RESIZE_FROM_POSITION,
    RESIZE_TO_ASPECT_RATIO,
    RESIZE_TO_AREA,
    RESIZE_TO_LAYER_SIZE,
    RESIZE_TO_IMAGE_SIZE,
  ) = (
    'resize_from_edges',
    'resize_from_position',
    'resize_to_aspect_ratio',
    'resize_to_area',
    'resize_to_layer_size',
    'resize_to_image_size',
  )


def resize_canvas(
      batcher,
      object_to_resize,
      resize_mode,
      set_fill_color,
      fill_color,
      resize_from_edges_same_amount_for_each_side,
      resize_from_edges_amount,
      resize_from_edges_top,
      resize_from_edges_bottom,
      resize_from_edges_left,
      resize_from_edges_right,
      resize_from_position_anchor,
      resize_from_position_width,
      resize_from_position_height,
      resize_to_aspect_ratio_ratio,
      resize_to_aspect_ratio_position,
      resize_to_aspect_ratio_position_custom,
      resize_to_area_x,
      resize_to_area_y,
      resize_to_area_width,
      resize_to_area_height,
      resize_to_layer_size_layers,
      resize_to_image_size_image,
):
  if resize_mode == ResizeModes.RESIZE_FROM_EDGES:
    if resize_from_edges_same_amount_for_each_side:
      resize_from_edges_top = resize_from_edges_amount
      resize_from_edges_bottom = resize_from_edges_amount
      resize_from_edges_left = resize_from_edges_amount
      resize_from_edges_right = resize_from_edges_amount

    resize_from_edges_top_pixels = builtin_actions_utils.unit_to_pixels(
      batcher, resize_from_edges_top, 'y')
    resize_from_edges_bottom_pixels = builtin_actions_utils.unit_to_pixels(
      batcher, resize_from_edges_bottom, 'y')
    resize_from_edges_left_pixels = builtin_actions_utils.unit_to_pixels(
      batcher, resize_from_edges_left, 'x')
    resize_from_edges_right_pixels = builtin_actions_utils.unit_to_pixels(
      batcher, resize_from_edges_right, 'x')

    object_to_resize_width = object_to_resize.get_width()
    object_to_resize_height = object_to_resize.get_height()
    offset_x_pixels = resize_from_edges_left_pixels
    offset_y_pixels = resize_from_edges_top_pixels

    width_pixels = (
      object_to_resize_width + resize_from_edges_left_pixels + resize_from_edges_right_pixels)
    width_pixels = _clamp_value(width_pixels, min_value=1)

    height_pixels = (
      object_to_resize_height + resize_from_edges_top_pixels + resize_from_edges_bottom_pixels)
    height_pixels = _clamp_value(height_pixels, min_value=1)

    _do_resize(
      batcher,
      object_to_resize,
      offset_x_pixels,
      offset_y_pixels,
      width_pixels,
      height_pixels,
      set_fill_color,
      fill_color,
    )
  elif resize_mode == ResizeModes.RESIZE_FROM_POSITION:
    object_to_resize_width = object_to_resize.get_width()
    object_to_resize_height = object_to_resize.get_height()

    offset_x_pixels, offset_y_pixels, width_pixels, height_pixels = (
      _get_resize_from_position_area_pixels(
        batcher,
        object_to_resize_width,
        object_to_resize_height,
        resize_from_position_anchor,
        resize_from_position_width,
        resize_from_position_height,
      ))

    width_pixels = _clamp_value(width_pixels, min_value=1)
    height_pixels = _clamp_value(height_pixels, min_value=1)

    _do_resize(
      batcher,
      object_to_resize,
      offset_x_pixels,
      offset_y_pixels,
      width_pixels,
      height_pixels,
      set_fill_color,
      fill_color,
    )
  elif resize_mode == ResizeModes.RESIZE_TO_ASPECT_RATIO:
    object_to_resize_width = object_to_resize.get_width()
    object_to_resize_height = object_to_resize.get_height()

    offset_x_pixels, offset_y_pixels, width_pixels, height_pixels = (
      _get_resize_to_aspect_ratio_pixels(
        batcher,
        object_to_resize_width,
        object_to_resize_height,
        resize_to_aspect_ratio_ratio,
        resize_to_aspect_ratio_position,
        resize_to_aspect_ratio_position_custom,
      ))

    width_pixels = _clamp_value(width_pixels, min_value=1)
    height_pixels = _clamp_value(height_pixels, min_value=1)

    _do_resize(
      batcher,
      object_to_resize,
      offset_x_pixels,
      offset_y_pixels,
      width_pixels,
      height_pixels,
      set_fill_color,
      fill_color,
    )
  elif resize_mode == ResizeModes.RESIZE_TO_AREA:
    offset_x_pixels = builtin_actions_utils.unit_to_pixels(batcher, resize_to_area_x, 'x')
    offset_y_pixels = builtin_actions_utils.unit_to_pixels(batcher, resize_to_area_y, 'y')
    width_pixels = builtin_actions_utils.unit_to_pixels(batcher, resize_to_area_width, 'x')
    height_pixels = builtin_actions_utils.unit_to_pixels(batcher, resize_to_area_height, 'y')

    width_pixels = _clamp_value(width_pixels, min_value=1)
    height_pixels = _clamp_value(height_pixels, min_value=1)

    _do_resize(
      batcher,
      object_to_resize,
      offset_x_pixels,
      offset_y_pixels,
      width_pixels,
      height_pixels,
      set_fill_color,
      fill_color,
    )
  elif resize_mode == ResizeModes.RESIZE_TO_LAYER_SIZE:
    layers = resize_to_layer_size_layers

    if len(layers) == 1:
      layer = layers[0]

      layer_offsets = layer.get_offsets()

      _do_resize(
        batcher,
        object_to_resize,
        -layer_offsets.offset_x,
        -layer_offsets.offset_y,
        layer.get_width(),
        layer.get_height(),
        set_fill_color,
        fill_color,
      )
    elif len(layers) > 1:
      layer_offset_list = [layer.get_offsets() for layer in layers]

      min_x = min(offset.offset_x for offset in layer_offset_list)
      min_y = min(offset.offset_y for offset in layer_offset_list)

      max_x = max(
        offset.offset_x + layer.get_width() for layer, offset in zip(layers, layer_offset_list))
      max_y = max(
        offset.offset_y + layer.get_height() for layer, offset in zip(layers, layer_offset_list))

      _do_resize(
        batcher,
        object_to_resize,
        -min_x,
        -min_y,
        max_x - min_x,
        max_y - min_y,
        set_fill_color,
        fill_color,
      )
  elif resize_mode == ResizeModes.RESIZE_TO_IMAGE_SIZE:
    if isinstance(object_to_resize, Gimp.Image):
      offset_x = 0
      offset_y = 0
    else:
      offsets = object_to_resize.get_offsets()
      offset_x = offsets.offset_x
      offset_y = offsets.offset_y

    _do_resize(
      batcher,
      object_to_resize,
      offset_x,
      offset_y,
      resize_to_image_size_image.get_width(),
      resize_to_image_size_image.get_height(),
      set_fill_color,
      fill_color,
    )


def _get_resize_from_position_area_pixels(
      batcher,
      object_to_resize_width,
      object_to_resize_height,
      resize_from_position_anchor,
      width,
      height,
):
  width_pixels = builtin_actions_utils.unit_to_pixels(batcher, width, 'x')
  height_pixels = builtin_actions_utils.unit_to_pixels(batcher, height, 'y')

  position = [0, 0]

  if resize_from_position_anchor == builtin_actions_utils.AnchorPoints.TOP_LEFT:
    position = [0, 0]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.TOP:
    position = [
      round((width_pixels - object_to_resize_width) / 2),
      0,
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.TOP_RIGHT:
    position = [
      width_pixels - object_to_resize_width,
      0,
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.LEFT:
    position = [
      0,
      round((height_pixels - object_to_resize_height) / 2),
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.CENTER:
    position = [
      round((width_pixels - object_to_resize_width) / 2),
      round((height_pixels - object_to_resize_height) / 2),
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.RIGHT:
    position = [
      width_pixels - object_to_resize_width,
      round((height_pixels - object_to_resize_height) / 2),
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.BOTTOM_LEFT:
    position = [
      0,
      height_pixels - object_to_resize_height,
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.BOTTOM:
    position = [
      round((width_pixels - object_to_resize_width) / 2),
      height_pixels - object_to_resize_height,
    ]
  elif resize_from_position_anchor == builtin_actions_utils.AnchorPoints.BOTTOM_RIGHT:
    position = [
      width_pixels - object_to_resize_width,
      height_pixels - object_to_resize_height,
    ]

  return position[0], position[1], width_pixels, height_pixels


def _get_resize_to_aspect_ratio_pixels(
      batcher,
      object_to_resize_width,
      object_to_resize_height,
      resize_to_aspect_ratio_ratio,
      resize_to_aspect_ratio_position,
      resize_to_aspect_ratio_position_custom,
):
  ratio_width = resize_to_aspect_ratio_ratio['x']
  ratio_height = resize_to_aspect_ratio_ratio['y']

  width_unit_length = object_to_resize_width / ratio_width
  height_pixels = width_unit_length * ratio_height
  if height_pixels > object_to_resize_height:
    width_pixels = object_to_resize_width
    height_pixels = round(height_pixels)
    offset_x_pixels = 0

    offset_y_pixels = 0
    if resize_to_aspect_ratio_position == builtin_actions_utils.Positions.START:
      offset_y_pixels = 0
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.CENTER:
      offset_y_pixels = round((height_pixels - object_to_resize_height) / 2)
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.END:
      offset_y_pixels = height_pixels - object_to_resize_height
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.CUSTOM:
      offset_y_pixels = builtin_actions_utils.unit_to_pixels(
        batcher, resize_to_aspect_ratio_position_custom, 'y')
  else:
    height_unit_length = object_to_resize_height / ratio_height
    width_pixels = round(height_unit_length * ratio_width)
    height_pixels = object_to_resize_height
    offset_y_pixels = 0

    offset_x_pixels = 0
    if resize_to_aspect_ratio_position == builtin_actions_utils.Positions.START:
      offset_x_pixels = 0
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.CENTER:
      offset_x_pixels = round((width_pixels - object_to_resize_width) / 2)
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.END:
      offset_x_pixels = width_pixels - object_to_resize_width
    elif resize_to_aspect_ratio_position == builtin_actions_utils.Positions.CUSTOM:
      offset_x_pixels = builtin_actions_utils.unit_to_pixels(
        batcher, resize_to_aspect_ratio_position_custom, 'x')

  return offset_x_pixels, offset_y_pixels, width_pixels, height_pixels


def _do_resize(
      batcher,
      object_to_resize,
      offset_x_pixels,
      offset_y_pixels,
      width_pixels,
      height_pixels,
      set_fill_color,
      fill_color,
):
  if isinstance(object_to_resize, Gimp.Image):
    orig_object_x = offset_x_pixels
    orig_object_y = offset_y_pixels
  else:
    offsets = object_to_resize.get_offsets()
    orig_object_x = offsets.offset_x
    orig_object_y = offsets.offset_y

  orig_object_width = object_to_resize.get_width()
  orig_object_height = object_to_resize.get_height()

  object_to_resize.resize(width_pixels, height_pixels, offset_x_pixels, offset_y_pixels)

  if set_fill_color:
    _fill_with_color(
      batcher,
      object_to_resize,
      fill_color,
      orig_object_x,
      orig_object_y,
      orig_object_width,
      orig_object_height,
    )


def _fill_with_color(
      batcher,
      object_to_resize,
      fill_color,
      selection_x,
      selection_y,
      selection_width,
      selection_height,
):
  if isinstance(object_to_resize, Gimp.Image):
    color_layer_offset_x = 0
    color_layer_offset_y = 0
  else:
    color_layer_offsets = object_to_resize.get_offsets()
    color_layer_offset_x = color_layer_offsets.offset_x
    color_layer_offset_y = color_layer_offsets.offset_y

  if isinstance(object_to_resize, Gimp.Image):
    drawable_to_fill = builtin_actions_utils.get_best_matching_layer_from_image(
      batcher, object_to_resize)
    image_of_drawable_to_fill = object_to_resize
  else:
    drawable_to_fill = object_to_resize
    image_of_drawable_to_fill = object_to_resize.get_image()

  builtin_actions_utils.add_color_layer(
    fill_color,
    image_of_drawable_to_fill,
    drawable_to_fill,
    color_layer_offset_x,
    color_layer_offset_y,
    object_to_resize.get_width(),
    object_to_resize.get_height(),
    selection_x,
    selection_y,
    selection_width,
    selection_height,
  )


def _clamp_value(value, min_value=None, max_value=None):
  if min_value is not None:
    if value < min_value:
      value = min_value

  if max_value is not None:
    if value > max_value:
      value = max_value

  return value


def on_after_add_resize_canvas_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value == 'resize_canvas':
    action['arguments/resize_from_edges_same_amount_for_each_side'].connect_event(
      'value-changed',
      _set_visible_for_resize_from_edges_settings,
      action['arguments'],
    )

    action['arguments/resize_from_edges_same_amount_for_each_side'].connect_event(
      'gui-visible-changed',
      _set_visible_for_resize_from_edges_settings,
      action['arguments'],
    )

    action['arguments/resize_to_aspect_ratio_position'].connect_event(
      'value-changed',
      _set_visible_for_resize_to_aspect_ratio_position_custom,
      action['arguments/resize_to_aspect_ratio_position_custom'],
    )

    action['arguments/resize_to_aspect_ratio_position'].connect_event(
      'gui-visible-changed',
      _set_visible_for_resize_to_aspect_ratio_position_custom,
      action['arguments/resize_to_aspect_ratio_position_custom'],
    )

    _set_sensitive_for_fill_color(
      action['arguments/set_fill_color'],
      action['arguments/fill_color'],
    )

    action['arguments/set_fill_color'].connect_event(
      'value-changed',
      _set_sensitive_for_fill_color,
      action['arguments/fill_color'],
    )

    _set_visible_for_resize_mode_settings(
      action['arguments/resize_mode'],
      action['arguments'],
    )

    action['arguments/resize_mode'].connect_event(
      'value-changed',
      _set_visible_for_resize_mode_settings,
      action['arguments'],
    )


def _set_visible_for_resize_from_edges_settings(
      resize_from_edges_same_amount_for_each_side_setting,
      resize_arguments_group,
):
  is_visible = resize_from_edges_same_amount_for_each_side_setting.gui.get_visible()
  is_checked = resize_from_edges_same_amount_for_each_side_setting.value

  resize_arguments_group['resize_from_edges_amount'].gui.set_visible(is_visible and is_checked)
  resize_arguments_group['resize_from_edges_top'].gui.set_visible(is_visible and not is_checked)
  resize_arguments_group['resize_from_edges_bottom'].gui.set_visible(is_visible and not is_checked)
  resize_arguments_group['resize_from_edges_left'].gui.set_visible(is_visible and not is_checked)
  resize_arguments_group['resize_from_edges_right'].gui.set_visible(is_visible and not is_checked)


def _set_visible_for_resize_to_aspect_ratio_position_custom(
      resize_to_aspect_ratio_position_setting,
      resize_to_aspect_ratio_position_custom_setting,
):
  is_visible = resize_to_aspect_ratio_position_setting.gui.get_visible()
  is_selected = (
    resize_to_aspect_ratio_position_setting.value == builtin_actions_utils.Positions.CUSTOM)

  resize_to_aspect_ratio_position_custom_setting.gui.set_visible(is_visible and is_selected)


def _set_sensitive_for_fill_color(
      set_fill_color_setting,
      fill_color_setting,
):
  fill_color_setting.gui.set_sensitive(set_fill_color_setting.value)


def _set_visible_for_resize_mode_settings(
      resize_mode_setting,
      resize_arguments_group,
):
  for setting in resize_arguments_group:
    if setting.name in ['object_to_resize', 'resize_mode', 'set_fill_color', 'fill_color']:
      continue

    setting.gui.set_visible(False)

  if resize_mode_setting.value == ResizeModes.RESIZE_FROM_EDGES:
    resize_arguments_group['resize_from_edges_same_amount_for_each_side'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_FROM_POSITION:
    resize_arguments_group['resize_from_position_anchor'].gui.set_visible(True)
    resize_arguments_group['resize_from_position_width'].gui.set_visible(True)
    resize_arguments_group['resize_from_position_height'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_ASPECT_RATIO:
    resize_arguments_group['resize_to_aspect_ratio_ratio'].gui.set_visible(True)
    resize_arguments_group['resize_to_aspect_ratio_position'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_AREA:
    resize_arguments_group['resize_to_area_x'].gui.set_visible(True)
    resize_arguments_group['resize_to_area_y'].gui.set_visible(True)
    resize_arguments_group['resize_to_area_width'].gui.set_visible(True)
    resize_arguments_group['resize_to_area_height'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_LAYER_SIZE:
    resize_arguments_group['resize_to_layer_size_layers'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_IMAGE_SIZE:
    resize_arguments_group['resize_to_image_size_image'].gui.set_visible(True)


RESIZE_CANVAS_DICT = {
  'name': 'resize_canvas',
  'function': resize_canvas,
  'display_name': _('Resize canvas'),
  'description': _('Resizes the image or layer extents.'),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_resize',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'resize_mode',
      'default_value': ResizeModes.RESIZE_FROM_EDGES,
      'items': [
        (ResizeModes.RESIZE_FROM_EDGES, _('Resize from edges (add borders)')),
        (ResizeModes.RESIZE_FROM_POSITION, _('Resize from position')),
        (ResizeModes.RESIZE_TO_ASPECT_RATIO, _('Resize to aspect ratio')),
        (ResizeModes.RESIZE_TO_AREA, _('Resize to area')),
        (ResizeModes.RESIZE_TO_LAYER_SIZE, _('Resize to layer size')),
        (ResizeModes.RESIZE_TO_IMAGE_SIZE, _('Resize to image size')),
      ],
      'display_name': _('How to resize'),
    },
    {
      'type': 'bool',
      'name': 'set_fill_color',
      'default_value': False,
      'display_name': _('Fill added space with color'),
    },
    {
      'type': 'color',
      'name': 'fill_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Color for added space'),
    },
    {
      'type': 'bool',
      'name': 'resize_from_edges_same_amount_for_each_side',
      'default_value': False,
      'display_name': _('Resize by the same amount from each side'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_amount',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Amount'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_top',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Top'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_bottom',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Bottom'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_left',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Left'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_right',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Right'),
    },
    {
      'type': 'anchor',
      'name': 'resize_from_position_anchor',
      'default_value': builtin_actions_utils.AnchorPoints.CENTER,
      'items': [
        (builtin_actions_utils.AnchorPoints.TOP_LEFT, _('Top left')),
        (builtin_actions_utils.AnchorPoints.TOP, _('Top')),
        (builtin_actions_utils.AnchorPoints.TOP_RIGHT, _('Top right')),
        (builtin_actions_utils.AnchorPoints.LEFT, _('Left')),
        (builtin_actions_utils.AnchorPoints.CENTER, _('Center')),
        (builtin_actions_utils.AnchorPoints.RIGHT, _('Right')),
        (builtin_actions_utils.AnchorPoints.BOTTOM_LEFT, _('Bottom left')),
        (builtin_actions_utils.AnchorPoints.BOTTOM, _('Bottom')),
        (builtin_actions_utils.AnchorPoints.BOTTOM_RIGHT, _('Bottom right')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_position_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_position_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
    {
      'type': 'coordinates',
      'name': 'resize_to_aspect_ratio_ratio',
      'default_value': {
        'x': 1.0,
        'y': 1.0,
      },
      'min_x': 1.0,
      'min_y': 1.0,
      'display_name': _('Aspect ratio (width:height)'),
    },
    {
      'type': 'choice',
      'name': 'resize_to_aspect_ratio_position',
      'default_value': builtin_actions_utils.Positions.CENTER,
      'items': [
        (builtin_actions_utils.Positions.START, _('Start')),
        (builtin_actions_utils.Positions.CENTER, _('Center')),
        (builtin_actions_utils.Positions.END, _('End')),
        (builtin_actions_utils.Positions.CUSTOM, _('Custom')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_aspect_ratio_position_custom',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Custom start position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_x',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Offset X'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_y',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Offset Y'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
    {
      'type': 'placeholder_layer_array',
      'name': 'resize_to_layer_size_layers',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers'),
    },
    {
      'type': 'placeholder_image',
      'name': 'resize_to_image_size_image',
      'element_type': 'image',
      'default_value': 'current_image',
      'display_name': _('Image'),
    },
  ],
}
