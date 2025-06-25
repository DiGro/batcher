"""Placeholder objects replaced with real GIMP objects during batch processing.

The placeholder objects are defined in the `PLACEHOLDERS` dictionary.
"""

import inspect
from typing import Callable, List, Optional, Union, Type

from gi.repository import GObject

from src import exceptions
from src import setting as setting_
from src import utils
from src.gui import placeholders as gui_placeholders


class Placeholder:
  
  def __init__(self, name: str, display_name: str, replacement_func: Callable):
    self._name = name
    self._display_name = display_name
    self._replacement_func = replacement_func

  @property
  def name(self) -> str:
    return self._name
  
  @property
  def display_name(self) -> str:
    return self._display_name
  
  def replace_args(self, *args):
    return self._replacement_func(*args)


def get_current_image(_setting, batcher):
  return batcher.current_image


def get_current_layer(_setting, batcher):
  return batcher.current_layer


def get_current_layer_for_array(setting, batcher):
  return (get_current_layer(setting, batcher),)


def get_background_layer(_setting, batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position < num_layers - 1,
    1,
    ['insert_background_for_images', 'insert_background_for_layers'],
    'color_tag',
    _('There are no background layers.'))


def get_background_layer_for_array(setting, batcher):
  return (get_background_layer(setting, batcher),)


def get_foreground_layer(_setting, batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position > 0,
    -1,
    ['insert_foreground_for_images', 'insert_foreground_for_layers'],
    'color_tag',
    _('There are no foreground layers.'))


def get_foreground_layer_for_array(setting, batcher):
  return (get_foreground_layer(setting, batcher),)


def get_none_object(_setting, _batcher):
  return None


def get_all_top_level_layers(_setting, batcher):
  return batcher.current_image.get_layers()


def get_value_for_unsupported_parameter(setting, _batcher):
  return getattr(setting, 'default_param_value', None)


def _get_adjacent_layer(
      batcher,
      position_cond_func,
      adjacent_position_increment,
      insert_builtin_action_names,
      color_tag_argument_name_for_builtin_actions,
      skip_message,
):
  image = batcher.current_image
  layer = batcher.current_layer

  if layer.get_parent() is None:
    children = image.get_layers()
  else:
    children = layer.get_parent().get_children()

  adjacent_layer = None

  num_layers = len(children)

  if num_layers > 1:
    position = image.get_item_position(layer)
    if position_cond_func(position, num_layers):
      next_layer = children[position + adjacent_position_increment]
      # A `None` element represents a background/foreground layer inserted
      # via other means than color tags (e.g. from a file). If there are no
      # matching color tags and `None` is present at least once, we always
      # consider `next_layer` to be the background/foreground.
      color_tags = []
      for action in _get_previous_enabled_actions(batcher, batcher.current_action):
        if any(action['orig_name'].value == orig_name
               for orig_name in insert_builtin_action_names):
          if color_tag_argument_name_for_builtin_actions in action['arguments']:
            color_tags.append(
              action[f'arguments/{color_tag_argument_name_for_builtin_actions}'].value)
        else:
          color_tags.append(None)

      if None in color_tags or next_layer.get_color_tag() in color_tags:
        adjacent_layer = next_layer

  if adjacent_layer is not None:
    # This is necessary for some commands relying on selected layers.
    image.set_selected_layers([adjacent_layer])
    return adjacent_layer
  else:
    raise exceptions.SkipCommand(skip_message)


def _get_previous_enabled_actions(batcher, current_command):
  previous_enabled_actions = []

  for action in batcher.actions:
    if action == current_command:
      return previous_enabled_actions

    if action['enabled'].value:
      previous_enabled_actions.append(action)

  return previous_enabled_actions


_PLACEHOLDERS_LIST = [
  ('current_image', _('Current Image'), get_current_image),
  ('current_layer', _('Current Layer'), get_current_layer),
  ('current_layer_for_array', _('Current Layer'), get_current_layer_for_array),
  ('background_layer', _('Layer Below (Background)'), get_background_layer),
  ('background_layer_for_array', _('Layer Below (Background)'), get_background_layer_for_array),
  ('foreground_layer', _('Layer Above (Foreground)'), get_foreground_layer),
  ('foreground_layer_for_array', _('Layer Above (Foreground)'), get_foreground_layer_for_array),
  ('all_top_level_layers', _('All Layers'), get_all_top_level_layers),
  ('none', _('None'), get_none_object),
  ('unsupported_parameter', '', get_value_for_unsupported_parameter),
]


PLACEHOLDERS = {args[0]: Placeholder(*args) for args in _PLACEHOLDERS_LIST}
"""Mapping of a placeholder name to a placeholder object.

The following placeholder objects are defined:

* ``PLACEHOLDERS['current_image']``: The image currently being processed.

* ``PLACEHOLDERS['current_layer']``: The layer currently being processed in the
  current image. This placeholder is used for commands containing
  `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item` parameters.

* ``PLACEHOLDERS['current_layer_for_array']``: The layer currently being
  processed in the current image. This placeholder is used for commands
  containing the `Gimp.CoreObjectArray` parameter whose object type is
  `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item`.

* ``PLACEHOLDERS['background_layer']``: The layer positioned immediately after
  the currently processed layer.

* ``PLACEHOLDERS['background_layer_for_array']``: The layer positioned 
  immediately after the currently processed layer. This placeholder is used for 
  commands containing the `Gimp.CoreObjectArray` parameter whose object 
  type is `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item`.

* ``PLACEHOLDERS['foreground_layer']``: The layer positioned immediately before
  the currently processed layer.

* ``PLACEHOLDERS['foreground_layer_for_array']``: The layer positioned 
  immediately before the currently processed layer. This placeholder is used 
  for commands containing the `Gimp.CoreObjectArray` parameter whose 
  object type is `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item`.

* ``PLACEHOLDERS['all_top_level_layers']``: All layers in the currently 
  processed image. This placeholder is used for commands containing the 
  `Gimp.CoreObjectArray` parameter whose object type is `Gimp.Layer`, 
  `Gimp.Drawable` or `Gimp.Item`.

* ``PLACEHOLDERS['unsupported_parameter']``: Indicates that the parameter
  is not supported by this plug-in and cannot be modified.
"""


ATTRIBUTES = {
  'width': _('Width'),
  'height': _('Height'),
  'x_offset': _('X-offset'),
  'y_offset': _('Y-offset'),
}
"""Attributes that can be obtained from objects substituted for placeholders.

Not all attributes can be obtained from all objects. `PLACEHOLDER_ATTRIBUTE_MAP`
specifies the allowed objects per a group of attributes.
"""


PLACEHOLDER_ATTRIBUTE_MAP = {
  ('current_image',): ('width', 'height'),
  ('current_layer', 'background_layer', 'foreground_layer'): (
    'width', 'height', 'x_offset', 'y_offset'),
}
"""Mapping of placeholders to applicable attributes."""


class PlaceholderSetting(setting_.Setting):
   
  _ALLOWED_GUI_TYPES = [gui_placeholders.PlaceholdersComboBoxPresenter]

  _DEFAULT_PLACEHOLDERS = []

  def __init__(self, name, **kwargs):
    self._placeholder_names = list(self._DEFAULT_PLACEHOLDERS)

    self._process_kwargs_before_parent_init(kwargs)

    super().__init__(name, **kwargs)

  def _process_kwargs_before_parent_init(self, kwargs):
    parent_class_parameters = inspect.signature(super().__init__).parameters

    # This ensures that extra arguments not specified in
    # `setting.Setting.__init__` are not passed there.
    keys_to_delete = []
    for key, value in kwargs.items():
      if key not in parent_class_parameters:
        utils.create_read_only_property(self, key, value)
        keys_to_delete.append(key)

    for key in keys_to_delete:
      del kwargs[key]

  def _get_pdb_type(self, pdb_type):
    # This avoids errors when creating placeholder settings. Placeholders
    # cannot be registered to the PDB anyway.
    return None

  def get_placeholder_names(self) -> List[str]:
    """Returns a list of names of placeholders applicable for this setting
    class.
    """
    return list(self._placeholder_names)

  def get_placeholders(self) -> List[Placeholder]:
    """Returns a list of placeholder objects applicable for this setting class.
    """
    return [
      placeholder for placeholder_name, placeholder in PLACEHOLDERS.items()
      if placeholder_name in self._placeholder_names]

  def _validate(self, value):
    if value not in self._placeholder_names:
      return 'invalid placeholder', 'invalid_value'


class PlaceholderGimpObjectSetting(PlaceholderSetting):

  def __init__(self, name, none_ok: bool = False, **kwargs):
    self._none_ok = none_ok

    super().__init__(name, **kwargs)

    if none_ok:
      self._placeholder_names.append('none')


class PlaceholderImageOrLayerSetting(PlaceholderGimpObjectSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_image'
  _DEFAULT_PLACEHOLDERS = ['current_image', 'current_layer', 'background_layer', 'foreground_layer']


class PlaceholderImageSetting(PlaceholderGimpObjectSetting):

  _DEFAULT_DEFAULT_VALUE = 'current_image'
  _DEFAULT_PLACEHOLDERS = ['current_image']


class PlaceholderDrawableSetting(PlaceholderGimpObjectSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _DEFAULT_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderLayerSetting(PlaceholderGimpObjectSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _DEFAULT_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderItemSetting(PlaceholderGimpObjectSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _DEFAULT_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderArraySetting(PlaceholderSetting):

  def __init__(self, name, element_type, **kwargs):
    super().__init__(name, **kwargs)

    self._element_type = setting_.process_setting_type(element_type)

  @property
  def element_type(self) -> Type[setting_.Setting]:
    return self._element_type

  def to_dict(self):
    settings_dict = super().to_dict()

    settings_dict['element_type'] = setting_.SETTING_TYPES[self._element_type]

    return settings_dict


class PlaceholderDrawableArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _DEFAULT_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
    'all_top_level_layers',
  ]


class PlaceholderLayerArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _DEFAULT_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
    'all_top_level_layers',
  ]


class PlaceholderItemArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _DEFAULT_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
    'all_top_level_layers',
  ]


class PlaceholderUnsupportedParameterSetting(PlaceholderSetting):

  _DEFAULT_DEFAULT_VALUE = 'unsupported_parameter'
  _ALLOWED_GUI_TYPES = [gui_placeholders.UnsupportedParameterPresenter]
  _DEFAULT_PLACEHOLDERS = [
    'unsupported_parameter',
  ]

  def __init__(self, name, default_param_value=None, **kwargs):
    self._default_param_value = default_param_value

    super().__init__(name, **kwargs)

  @property
  def default_param_value(self):
    return self._default_param_value


def get_replaced_value(setting: PlaceholderSetting, batcher: 'src.core.Batcher'):
  """Returns a valid value replacing the placeholder value.

  ``setting`` is the placeholder setting whose ``value`` property is replaced.

  ``batcher`` is a `core.Batcher` instance holding data that may be used
  depending on the subclass of ``setting``.

  `KeyError` is raised if the placeholder value is not one of the keys in
  `PLACEHOLDERS`.
  """
  try:
    placeholder = PLACEHOLDERS[setting.value]
  except KeyError:
    raise ValueError(f'invalid placeholder value "{setting.value}"')
  else:
    return placeholder.replace_args(setting, batcher)


def get_placeholder_type_name_from_pdb_type(
      pdb_type: Union[GObject.GType, Type[GObject.GObject]],
      pdb_param_info: Optional[GObject.ParamSpec] = None,
) -> Union[str, None]:
  """Returns the name of a `setting.Setting` subclass representing a
  placeholder from the given GIMP PDB parameter type.

  Args:
    pdb_type:
      A `GObject.GObject` subclass or a `GObject.GType` instance representing a
      GIMP PDB parameter.
    pdb_param_info:
      Object representing PDB parameter information, obtainable via
      `pypdb.PDBProcedure.arguments`. This is used to infer the element type
      for an object array argument (images, layers, etc.).

  Returns:
    String as a human-readable name of a `setting.Setting` subclass
    representing a placeholder if ``pdb_type`` matches an identifier, or
    ``None`` otherwise.
  """
  processed_pdb_type = pdb_type

  if hasattr(pdb_type, '__gtype__'):
    processed_pdb_type = pdb_type.__gtype__

  try:
    pdb_type_name = processed_pdb_type.name
  except AttributeError:
    return None

  if pdb_type_name == 'GimpCoreObjectArray' and pdb_param_info is not None:
    _array_type, setting_dict = (
      setting_.get_array_setting_type_from_gimp_core_object_array(pdb_param_info))
    key = (pdb_type_name, setting_dict['element_type'])
  else:
    key = pdb_type_name

  try:
    placeholder_type_name = _PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES[key]
  except (KeyError, TypeError):
    return None
  else:
    return placeholder_type_name


_PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES = {
  'GimpImage': setting_.SETTING_TYPES[PlaceholderImageSetting],
  'GimpItem': setting_.SETTING_TYPES[PlaceholderItemSetting],
  'GimpDrawable': setting_.SETTING_TYPES[PlaceholderDrawableSetting],
  'GimpLayer': setting_.SETTING_TYPES[PlaceholderLayerSetting],
  ('GimpCoreObjectArray', setting_.LayerSetting): (
    setting_.SETTING_TYPES[PlaceholderLayerArraySetting]),
  ('GimpCoreObjectArray', setting_.DrawableSetting): (
    setting_.SETTING_TYPES[PlaceholderDrawableArraySetting]),
  ('GimpCoreObjectArray', setting_.ItemSetting): (
    setting_.SETTING_TYPES[PlaceholderItemArraySetting]),
}
