"""Wrapper of `setting.sources` module to allow easy loading/saving using
multiple setting sources.
"""

import collections
from collections.abc import Iterable
from typing import Callable, Dict, List, Optional, Union

from . import _sources_errors

__all__ = [
  'Persistor',
  'PersistorResult',
]


class Persistor:
  """Loading and saving settings for multiple settings sources at once.
  
  Settings sources are `setting.Source` instances.
  
  Apart from merely loading or saving settings, this class also triggers events
  before/after loading/saving for each setting and exits gracefully even if
  reading/writing settings to a setting source failed.
  """
  
  _STATUSES = SUCCESS, PARTIAL_SUCCESS, SOURCE_NOT_FOUND, FAIL, NO_SETTINGS = (0, 1, 2, 3, 4)
  
  _DEFAULT_SETTING_SOURCES = {}
  
  @classmethod
  def get_default_setting_sources(
        cls,
  ) -> Dict[str, Union['src.setting.Source', List['src.setting.Source']]]:
    """Returns a dictionary containing default setting sources.

    The returned dictionary is a copy of an internally stored dictionary to
    prevent it from being modified other than via
    `set_default_setting_sources()`.

    See `set_default_setting_sources()` for more information.
    """
    return dict(cls._DEFAULT_SETTING_SOURCES)
  
  @classmethod
  def set_default_setting_sources(
        cls, sources: Optional[Dict[str, Union['src.setting.Source', List['src.setting.Source']]]]):
    """Sets the dictionary of setting sources to use in methods of this class if
    no other setting sources in these methods are specified.
    
    The dictionary must contain ``(key, setting source(s))`` pairs.
    
    The key is a string that identifies a group of sources to load settings
    from/save settings to. This way, you can e.g. use specific subsets of
    sources when loading/saving settings at a certain point in your application.

    If ``sources`` is ``None``, there will be no default setting sources.
    """
    if sources is None:
      sources = {}
    
    if not isinstance(sources, dict):
      raise TypeError('"sources" must be a dictionary')
    
    cls._DEFAULT_SETTING_SOURCES = sources
  
  @classmethod
  def load(
        cls,
        settings_or_groups: Iterable[Union['src.setting.Setting', 'src.setting.Group']],
        setting_sources: Union[
          Dict[str, Union['src.setting.Source', List['src.setting.Source']]],
          List[str],
          None,
        ] = None,
        trigger_events: bool = True,
        modify_data_func: Optional[Callable] = None,
  ) -> 'PersistorResult':
    """Loads values from the specified settings or groups, or creates new
    settings within the specified groups if they do not exist.
    
    The order of setting sources in ``setting_sources`` indicates the
    preference of the sources, beginning with the first source. If not all
    settings could be found in the first source, the second source is read to
    assign values to the remaining settings. This continues until all sources
    are read or all settings are found.
    
    If the setting source(s) contain an invalid value for a setting,
    the default value for the setting will be assigned. Settings not found in
    any of the sources will also have their default values assigned.
    
    The following events are triggered for each `setting.Setting` and
    `setting.Group` instance within ``settings_or_groups``, including child
    settings and groups:
    
    * ``'before-load'``: invoked before loading settings. The event will not be
      triggered for settings present in the source but not in memory as they are
      not loaded yet.

    * ``'after-load'`` - invoked after loading settings. The event will also be
      triggered for settings originally not present in memory as they are loaded
      at this point. This event is triggered even if loading fails for any
      source.

    * events triggered in `setting.Setting.set_value()` when a setting is being
      loaded.

    * events triggered in `setting.Setting.reset()` when loading a setting was
      not successful (occurring when the loaded value was not valid).
    
    Args:
      settings_or_groups:
        `setting.Setting` and `setting.Group` instances whose values are
        loaded from ``setting_sources``. For settings and groups that exist
        in ``settings_or_groups``, only values are loaded. Child settings and
        groups not present in a group in memory but present in the source(s)
        are created within the group.
      setting_sources:
        Dictionary or list of setting sources or ``None``. If a dictionary,
        it must contain (key, setting source) pairs or (key, list of setting
        sources) pairs. See `set_default_setting_sources()` for more
        information on the key. If a list, it must contain keys and all keys
        must have a mapping to one of the default sources as returned by
        `get_default_setting_sources()`. If ``None``, default setting sources
        are used as returned by `get_default_setting_sources()`.
      trigger_events:
        If ``True``, ``'before-load'`` and ``'after-load'`` events are triggered
        for each setting. If ``False``, these events are not triggered.
      modify_data_func:
        See the ``modify_data_func`` parameter in
        `setting.Source.read()`. This function is applied to each
        source separately.

    Returns:
      A `PersistorResult` instance describing the result, particularly in the
      case of a failure. See `PersistorResult` for more information.
    """
    if not settings_or_groups:
      return cls._result(cls.NO_SETTINGS)
    
    if setting_sources is None:
      setting_sources = cls._DEFAULT_SETTING_SOURCES
    
    if not setting_sources:
      return cls._result(cls.FAIL)
    
    processed_setting_sources = cls._process_setting_sources(setting_sources)
    
    if not processed_setting_sources:
      return cls._result(cls.FAIL)
    
    cls._trigger_event(settings_or_groups, 'before-load', trigger_events)
    
    settings_not_loaded, statuses_per_source, messages_per_source = cls._load(
      settings_or_groups, processed_setting_sources, modify_data_func)
    
    cls._trigger_event(settings_or_groups, 'after-load', trigger_events)
    
    return cls._get_return_result(settings_not_loaded, statuses_per_source, messages_per_source)
  
  @classmethod
  def _load(cls, settings_or_groups, setting_sources, modify_data_func):
    settings_not_loaded = settings_or_groups
    
    statuses_per_source = {}
    messages_per_source = {}
    
    for _unused, sources in setting_sources.items():
      for source in sources:
        try:
          source.read(settings_not_loaded, modify_data_func=modify_data_func)
        except _sources_errors.SourceNotFoundError as e:
          statuses_per_source[source] = cls.SOURCE_NOT_FOUND
          messages_per_source[source] = str(e)
        except _sources_errors.SourceError as e:
          statuses_per_source[source] = cls.FAIL
          messages_per_source[source] = str(e)
        else:
          statuses_per_source[source] = cls.SUCCESS
          messages_per_source[source] = ''
          
          if source.settings_not_loaded:
            settings_not_loaded = source.settings_not_loaded
          else:
            return [], statuses_per_source, messages_per_source
    
    return settings_not_loaded, statuses_per_source, messages_per_source
  
  @classmethod
  def save(
        cls,
        settings_or_groups: Iterable[Union['src.setting.Setting', 'src.setting.Group']],
        setting_sources: Union[
          Dict[str, Union['src.setting.Source', List['src.setting.Source']]],
          List[str],
          None,
        ] = None,
        trigger_events: bool = True,
        modify_data_func: Optional[Callable] = None,
  ) -> 'PersistorResult':
    """Saves settings to the specified setting sources.
    
    The following events for each `setting.Setting` instance (including child
    settings in `setting.Group` instances) within ``settings_or_groups`` are
    triggered:
    
    * ``'before-save'``: invoked before saving settings.
    
    * ``'after-save'``: invoked after saving settings. This event is triggered
      even if saving fails for any source.
    
    Args:
      settings_or_groups:
        List of `settings.Setting` or `group.Group` instances whose values
        are saved to ``setting_sources``.
      setting_sources:
        Dictionary or list of setting sources or ``None``. See `load()` for
        more information.
      trigger_events:
        If ``True``, trigger ``'before-save'`` and ``'after-save'`` events
        for each setting. If ``False``, these events are not triggered.
      modify_data_func:
        See the ``modify_data_func`` parameter in
        `setting.Source.write()`. This function is applied to each
        source separately.
    
    Returns:
      A `PersistorResult` instance describing the result, particularly in the
      case of a failure. See `PersistorResult` for more information.
    """
    if not settings_or_groups:
      return cls._result(cls.NO_SETTINGS)
    
    if setting_sources is None:
      setting_sources = cls._DEFAULT_SETTING_SOURCES
    
    if not setting_sources:
      return cls._result(cls.FAIL)
    
    processed_setting_sources = cls._process_setting_sources(setting_sources)
    
    if not processed_setting_sources:
      return cls._result(cls.FAIL)
    
    cls._trigger_event(settings_or_groups, 'before-save', trigger_events)
    
    statuses_per_source, messages_per_source = cls._save(
      settings_or_groups, processed_setting_sources, modify_data_func)
    
    cls._trigger_event(settings_or_groups, 'after-save', trigger_events)
    
    return cls._get_return_result([], statuses_per_source, messages_per_source)
  
  @classmethod
  def _save(cls, settings_or_groups, setting_sources, modify_data_func):
    statuses_per_source = {}
    messages_per_source = {}
    
    for _unused, sources in setting_sources.items():
      for source in sources:
        try:
          source.write(settings_or_groups, modify_data_func=modify_data_func)
        except _sources_errors.SourceError as e:
          statuses_per_source[source] = cls.FAIL
          messages_per_source[source] = str(e)
        else:
          statuses_per_source[source] = cls.SUCCESS
          messages_per_source[source] = ''
    
    return statuses_per_source, messages_per_source
  
  @classmethod
  def clear(
        cls,
        setting_sources: Union[
          Dict[str, Union['src.setting.Source', List['src.setting.Source']]],
          List[str],
          None,
        ] = None
  ):
    """Removes all settings from all specified setting sources.
    
    Args:
      setting_sources:
        Dictionary or list of setting sources or ``None``. See `load()` for
        more information. If there are no sources to clear, this method has
        no effect.
    """
    if setting_sources is None:
      setting_sources = cls._DEFAULT_SETTING_SOURCES
    
    processed_setting_sources = cls._process_setting_sources(setting_sources)
    
    if setting_sources is not None:
      for sources in processed_setting_sources.values():
        for source in sources:
          source.clear()
  
  @classmethod
  def _trigger_event(cls, settings_or_groups, event_name, trigger_events):
    if trigger_events:
      for setting in cls._list_settings(settings_or_groups, include_groups=True):
        setting.invoke_event(event_name)
  
  @staticmethod
  def _result(status, settings_not_loaded=None, statuses_per_source=None, messages_per_source=None):
    if settings_not_loaded is None:
      settings_not_loaded = []
    
    if statuses_per_source is None:
      statuses_per_source = {}
    
    return PersistorResult(status, settings_not_loaded, statuses_per_source, messages_per_source)
  
  @classmethod
  def _get_return_result(cls, settings_not_loaded, statuses_per_source, messages_per_source):
    if (all(status == cls.SUCCESS for status in statuses_per_source.values())
        and not settings_not_loaded):
      return cls._result(cls.SUCCESS)
    elif all(status == cls.FAIL for status in statuses_per_source.values()):
      return cls._result(cls.FAIL, settings_not_loaded, statuses_per_source, messages_per_source)
    else:
      return cls._result(
        cls.PARTIAL_SUCCESS, settings_not_loaded, statuses_per_source, messages_per_source)
  
  @classmethod
  def _process_setting_sources(cls, setting_sources):
    processed_setting_sources = {}
    
    if not isinstance(setting_sources, dict):
      for key in setting_sources:
        if key not in processed_setting_sources:
          processed_setting_sources[key] = []
        
        try:
          source = cls._DEFAULT_SETTING_SOURCES[key]
        except KeyError:
          # Causes `Persistor.load()` or `Persistor.save()` to return `FAIL`
          return []
        else:
          if isinstance(source, Iterable):
            for item in source:
              processed_setting_sources[key].append(item)
          else:
            processed_setting_sources[key].append(source)
    else:
      for key, source in setting_sources.items():
        if key not in processed_setting_sources:
          processed_setting_sources[key] = []
        
        if isinstance(source, Iterable):
          for item in source:
            processed_setting_sources[key].append(item)
        else:
          processed_setting_sources[key].append(source)
    
    return processed_setting_sources
  
  @staticmethod
  def _list_settings(settings_or_groups, **walk_kwargs):
    settings = []
    for setting_or_group in settings_or_groups:
      # HACK: We do not use `isinstance(setting_or_group, Group)` to avoid a circular import.
      if hasattr(setting_or_group, 'walk'):
        group = setting_or_group
        settings.append(group)
        settings.extend(list(group.walk(**walk_kwargs)))
      else:
        setting = setting_or_group
        settings.append(setting)
    return settings


PersistorResult = collections.namedtuple(
  'PersistorResult',
  ['status', 'settings_not_loaded', 'statuses_per_source', 'messages_per_source'])
"""Data describing the result of `Persistor.load()` or `Persistor.save()`.

The names of parameters below are parameters passed to `Persistor.load()` or
`Persistor.save()`.

``settings_not_loaded`` contains all settings not loaded and ``statuses`` 
contains statuses for each source individually.

Args:
  status:
    Value indicating whether loading or saving proceeded with success or some
    form of failure. Possible values:

    * ``SUCCESS`` - All settings were successfully loaded or saved.
    
    * ``PARTIAL_SUCCESS`` - This status is returned when at least one of the
     following occurs:
      
      * Only some settings were successfully loaded.
      
      * At least one source was not found when attempting to read from it.
      
      * Reading from at least one source was successful and failed for at least
        one other source.
      
      * Writing to at least one source was successful and failed for at least
        one other source.
    
  
    * ``FAIL`` - This status is returned when at least one of the following
      occurs:
    
      * Reading from/writing to all sources failed.
      
      * The ``setting_sources`` parameter is ``None`` and the default sources
        returned by `Persistor.get_default_setting_sources()` is an empty
        dictionary.
      
      * The ``setting_sources`` parameter is a list of keys (source names) and
        there is at least one key not present in the default sources as returned
        by `Persistor.get_default_setting_sources()`.
  
    * ``NO_SETTINGS`` - Used when the ``settings_or_groups`` parameter is empty.
  settings_not_loaded
    List of settings and groups that were not loaded when calling 
    `Persistor.load()`. These settings were not found in any setting source. 
    For `Persistor.save()`, this attribute is always empty.
  statuses_per_source
    ``status`` values for each setting source passed to `Persistor.load()` or 
    `Persistor.save()`. It is a dictionary of (setting source, status) pairs. 
    Beside values in the ``status`` attribute, the following values can also 
    appear in ``statuses_per_source``:
    
    * ``SOURCE_NOT_FOUND`` - The source was not found when attempting to load
      settings, either because the corresponding file is missing or the source
      name does not exist.
  messages_per_source
    Messages for each setting source passed to `Persistor.load()` or 
    `Persistor.save()`. It is a dictionary of (setting source, string) pairs.
    Usually, only error messages are included, i.e. if the load/save status is
    ``SUCCESS``, the message is empty.
"""
