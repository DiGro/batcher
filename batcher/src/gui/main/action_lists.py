from typing import Dict, List

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import builtin_actions_common
from src import builtin_constraints
from src import builtin_procedures

from src.gui import messages as messages_
from src.gui.actions import list as action_list_
from src.gui.main import export_settings as export_settings_


class ActionLists:

  _ACTION_LABEL_BOX_SPACING = 5

  _CONSTRAINTS_TOP_MARGIN = 5

  def __init__(self, settings, dialog):
    self._settings = settings
    self._dialog = dialog

    self._procedures_or_constraints_loaded = False

    self._procedure_list = action_list_.ActionList(
      self._settings['main/procedures'],
      builtin_actions=builtin_actions_common.get_filtered_builtin_actions(
        builtin_procedures.BUILTIN_PROCEDURES, [pg.config.PROCEDURE_GROUP]),
      add_action_text=_('Add P_rocedure...'),
      allow_custom_actions=True,
      add_custom_action_text=_('Add Custom Procedure...'),
      action_browser_text=_('Add Custom Procedure'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._constraint_list = action_list_.ActionList(
      self._settings['main/constraints'],
      builtin_actions=builtin_actions_common.get_filtered_builtin_actions(
        builtin_constraints.BUILTIN_CONSTRAINTS, [pg.config.PROCEDURE_GROUP]),
      add_action_text=_('Add C_onstraint...'),
      allow_custom_actions=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._init_gui()

    self._init_setting_gui()

  @property
  def procedure_list(self):
    return self._procedure_list

  @property
  def constraint_list(self):
    return self._constraint_list

  @property
  def vbox_procedures(self):
    return self._vbox_procedures

  @property
  def vbox_constraints(self):
    return self._vbox_constraints

  def display_warnings_and_tooltips_for_actions_and_deactivate_failing_actions(
        self, batcher, clear_previous=True):
    self.set_warnings_and_deactivate_failed_actions(batcher, clear_previous=clear_previous)

    self._set_action_skipped_tooltips(
      self._procedure_list,
      batcher.skipped_procedures,
      _('This procedure is skipped. Reason: {}'),
      clear_previous=clear_previous)

    self._set_action_skipped_tooltips(
      self._constraint_list,
      batcher.skipped_constraints,
      _('This constraint is skipped. Reason: {}'),
      clear_previous=clear_previous)

  def set_warnings_and_deactivate_failed_actions(self, batcher, clear_previous=True):
    action_lists = [self._procedure_list, self._constraint_list]
    failed_actions_dict = [batcher.failed_procedures, batcher.failed_constraints]

    for action_list, failed_actions in zip(action_lists, failed_actions_dict):
      for action_item in action_list.items:
        if action_item.action.name in failed_actions:
          action_item.set_warning(
            True,
            messages_.get_failing_action_message(
              (action_item.action, failed_actions[action_item.action.name][0][0])),
            failed_actions[action_item.action.name][0][1],
            failed_actions[action_item.action.name][0][2],
            parent=self._dialog)

          action_item.action['enabled'].set_value(False)
        else:
          if clear_previous and action_item.action['enabled'].value:
            action_item.set_warning(False)

  def reset_action_tooltips_and_indicators(self):
    for action_list in [self._procedure_list, self._constraint_list]:
      for action_item in action_list.items:
        action_item.reset_tooltip()
        action_item.set_warning(False)

  def close_action_edit_dialogs(self):
    for action_list in [self._procedure_list, self._constraint_list]:
      for action_item in action_list.items:
        action_item.editor.hide()

  def _init_gui(self):
    self._label_procedures = Gtk.Label(
      label='<b>{}</b>'.format(_('Procedures')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_procedures = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
    )
    self._vbox_procedures.pack_start(self._label_procedures, False, False, 0)
    self._vbox_procedures.pack_start(self._procedure_list, True, True, 0)

    self._label_constraints = Gtk.Label(
      label='<b>{}</b>'.format(_('Constraints')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_constraints = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
      margin_top=self._CONSTRAINTS_TOP_MARGIN,
    )
    self._vbox_constraints.pack_start(self._label_constraints, False, False, 0)
    self._vbox_constraints.pack_start(self._constraint_list, True, True, 0)

  def _init_setting_gui(self):
    self._settings['gui/procedure_browser/paned_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
      widget=self._procedure_list.browser.paned,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_position,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_size'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_size,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

    self._procedure_list.connect(
      'action-list-item-added-interactive',
      _on_procedure_item_added,
      self._settings,
      self._constraint_list,
    )

    _set_up_existing_export_procedures(self._procedure_list)
    self._procedure_list.actions.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_export_procedures(self._procedure_list))

    _set_up_existing_rename_procedures(self._procedure_list)
    self._procedure_list.actions.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_rename_procedures(self._procedure_list))

    _set_up_existing_insert_back_foreground_and_related_actions(
      self._procedure_list, self._constraint_list)
    self._procedure_list.actions.connect_event(
      'after-load', self._set_up_existing_insert_back_foreground_and_related_actions_on_load)
    self._constraint_list.actions.connect_event(
      'after-load', self._set_up_existing_insert_back_foreground_and_related_actions_on_load)

    self._constraint_list.connect(
      'action-list-item-added-interactive',
      _on_constraint_item_added,
      self._settings,
    )

    _set_up_existing_matching_text_constraints(self._constraint_list)
    self._constraint_list.actions.connect_event(
      'after-load',
      lambda _constraints: _set_up_existing_matching_text_constraints(self._constraint_list))

  def _set_up_existing_insert_back_foreground_and_related_actions_on_load(self, _actions):
    if self._procedures_or_constraints_loaded:
      _set_up_existing_insert_back_foreground_and_related_actions(
        self._procedure_list, self._constraint_list)

      # This allows setting up the actions again when loading again.
      self._procedures_or_constraints_loaded = False

    self._procedures_or_constraints_loaded = True

  @staticmethod
  def _set_action_skipped_tooltips(
        action_list: action_list_.ActionList,
        skipped_actions: Dict[str, List],
        message: str,
        clear_previous: bool = True,
  ):
    for action_item in action_list.items:
      if not action_item.has_warning():
        if action_item.action.name in skipped_actions:
          skipped_message = skipped_actions[action_item.action.name][0][1]
          action_item.set_tooltip(message.format(skipped_message))
        else:
          if clear_previous:
            action_item.reset_tooltip()


def _on_procedure_item_added(procedure_list, item, settings, constraint_list):
  if item.action['orig_name'].value.startswith('rename_for_'):
    _handle_rename_procedure_item_added(item)

  if item.action['orig_name'].value.startswith('export_for_'):
    _handle_export_procedure_item_added(item)

    if item.action['orig_name'].value != 'export_for_edit_layers':
      _handle_export_procedure_item_added_for_export_mode(item, settings)

  if any(item.action['orig_name'].value.startswith(prefix) for prefix in [
       'insert_background_for_', 'insert_foreground_for_']):
    _handle_insert_background_foreground_procedure_item_added(procedure_list, item, constraint_list)


def _set_up_existing_rename_procedures(procedure_list: action_list_.ActionList):
  for item in procedure_list.items:
    if item.action['orig_name'].value.startswith('rename_for_'):
      _handle_rename_procedure_item_added(item)


def _set_up_existing_export_procedures(procedure_list: action_list_.ActionList):
  for item in procedure_list.items:
    if item.action['orig_name'].value.startswith('export_for_'):
      _handle_export_procedure_item_added(item)


def _handle_insert_background_foreground_procedure_item_added(
      procedure_list, item, constraint_list):
  procedure_list.reorder_item(item, 0)

  merge_item = _add_merge_background_foreground_procedure(procedure_list, item)

  constraint_item = _add_not_background_foreground_constraint(item, constraint_list)

  _hide_internal_arguments_for_insert_background_foreground_procedure(item)
  _set_up_merge_background_foreground_procedure(merge_item)
  _set_up_not_background_foreground_constraint(item, constraint_item)

  if merge_item is not None or constraint_item is not None:
    _set_up_insert_background_foreground_procedure(
      item, merge_item, constraint_item, procedure_list, constraint_list)

  if merge_item is not None:
    item.action['arguments/merge_procedure_name'].set_value(merge_item.action.name)
  if constraint_item is not None:
    item.action['arguments/constraint_name'].set_value(constraint_item.action.name)


def _set_up_existing_insert_back_foreground_and_related_actions(
      procedure_list: action_list_.ActionList,
      constraint_list: action_list_.ActionList,
):
  for item in procedure_list.items:
    if any(item.action['orig_name'].value.startswith(prefix) for prefix in [
         'insert_background_for_', 'insert_foreground_for_']):
      merge_procedure_name = (
        item.action['arguments/merge_procedure_name'].value
        if 'merge_procedure_name' in item.action['arguments'] else None)
      if merge_procedure_name is not None and merge_procedure_name in procedure_list.actions:
        merge_item = next(
          iter(
            item_ for item_ in procedure_list.items if item_.action.name == merge_procedure_name),
          None)
      else:
        merge_item = None

      constraint_name = (
        item.action['arguments/constraint_name'].value
        if 'constraint_name' in item.action['arguments'] else None)
      if constraint_name is not None and constraint_name in constraint_list.actions:
        constraint_item = next(
          iter(item_ for item_ in constraint_list.items if item_.action.name == constraint_name),
          None)
      else:
        constraint_item = None

      _hide_internal_arguments_for_insert_background_foreground_procedure(item)
      _set_up_merge_background_foreground_procedure(merge_item)
      _set_up_not_background_foreground_constraint(item, constraint_item)

      if merge_item is not None or constraint_item is not None:
        _set_up_insert_background_foreground_procedure(
          item, merge_item, constraint_item, procedure_list, constraint_list)


def _hide_internal_arguments_for_insert_background_foreground_procedure(item):
  if 'merge_procedure_name' in item.action['arguments']:
    item.action['arguments/merge_procedure_name'].gui.set_visible(False)
  if 'constraint_name' in item.action['arguments']:
    item.action['arguments/constraint_name'].gui.set_visible(False)


def _set_up_insert_background_foreground_procedure(
      item,
      merge_item,
      constraint_item,
      procedure_list: action_list_.ActionList,
      constraint_list: action_list_.ActionList,
):
  item.action['enabled'].connect_event(
    'value-changed',
    _on_insert_background_foreground_procedure_enabled_changed,
    merge_item.action if merge_item is not None else None,
    constraint_item.action if constraint_item is not None else None,
  )

  procedure_list.connect(
    'action-list-item-removed',
    _on_insert_background_foreground_procedure_removed,
    item,
    merge_item,
    constraint_list,
    constraint_item,
  )


def _add_merge_background_foreground_procedure(procedure_list, item):
  merge_procedure_orig_name_mapping = {
    'insert_background_for_images': 'merge_background',
    'insert_background_for_layers': 'merge_background',
    'insert_foreground_for_images': 'merge_foreground',
    'insert_foreground_for_layers': 'merge_foreground',
  }

  if item.action['orig_name'].value not in merge_procedure_orig_name_mapping:
    return None

  merge_procedure_name = merge_procedure_orig_name_mapping[item.action['orig_name'].value]

  merge_item = procedure_list.add_item(builtin_procedures.BUILTIN_PROCEDURES[merge_procedure_name])

  export_procedure_index = next(
    iter(index for index, item in enumerate(procedure_list.items)
         if item.action['orig_name'].value.startswith('export_for_')),
    None)
  if export_procedure_index is not None:
    procedure_list.reorder_item(merge_item, export_procedure_index)

  return merge_item


def _set_up_merge_background_foreground_procedure(merge_item):
  if merge_item is not None:
    _set_buttons_for_action_item_sensitive(merge_item, False)

    merge_item.action['arguments/last_enabled_value'].gui.set_visible(False)


def _add_not_background_foreground_constraint(item, constraint_list):
  constraint_orig_name_mapping = {
    'insert_background_for_layers': 'not_background',
    'insert_foreground_for_layers': 'not_foreground',
  }

  if item.action['orig_name'].value not in constraint_orig_name_mapping:
    return None

  constraint_name = constraint_orig_name_mapping[item.action['orig_name'].value]

  constraint_item = constraint_list.add_item(
    builtin_constraints.BUILTIN_CONSTRAINTS[constraint_name])

  return constraint_item


def _set_up_not_background_foreground_constraint(item, constraint_item):
  if constraint_item is None:
    return

  def _on_insert_background_foreground_color_tag_changed(color_tag_setting):
    constraint_item.action['arguments/color_tag'].set_value(color_tag_setting.value)

  if constraint_item is not None:
    _set_buttons_for_action_item_sensitive(constraint_item, False)

  constraint_item.action['arguments/color_tag'].gui.set_visible(False)
  constraint_item.action['arguments/last_enabled_value'].gui.set_visible(False)

  item.action['arguments/color_tag'].connect_event(
    'value-changed', _on_insert_background_foreground_color_tag_changed)
  _on_insert_background_foreground_color_tag_changed(item.action['arguments/color_tag'])


def _on_insert_background_foreground_procedure_enabled_changed(
      enabled_setting,
      merge_procedure,
      constraint,
):
  if not enabled_setting.value:
    if merge_procedure is not None:
      merge_procedure['arguments/last_enabled_value'].set_value(merge_procedure['enabled'].value)
      merge_procedure['enabled'].set_value(False)

    if constraint is not None:
      constraint['arguments/last_enabled_value'].set_value(constraint['enabled'].value)
      constraint['enabled'].set_value(False)
  else:
    if merge_procedure is not None:
      merge_procedure['enabled'].set_value(merge_procedure['arguments/last_enabled_value'].value)
    if constraint is not None:
      constraint['enabled'].set_value(constraint['arguments/last_enabled_value'].value)

  if merge_procedure is not None:
    merge_procedure['enabled'].gui.set_sensitive(enabled_setting.value)
  if constraint is not None:
    constraint['enabled'].gui.set_sensitive(enabled_setting.value)


def _on_insert_background_foreground_procedure_removed(
      procedure_list,
      removed_item,
      insert_back_foreground_item,
      merge_item,
      constraint_list,
      constraint_item):
  if removed_item == insert_back_foreground_item:
    if merge_item is not None and merge_item in procedure_list.items:
      procedure_list.remove_item(merge_item)
    if constraint_item is not None and constraint_item in constraint_list.items:
      constraint_list.remove_item(constraint_item)


def _handle_rename_procedure_item_added(item):
  _set_display_name_for_rename_procedure(
    item.action['arguments/pattern'],
    item.action)

  item.action['arguments/pattern'].connect_event(
    'value-changed',
    _set_display_name_for_rename_procedure,
    item.action)


def _set_display_name_for_rename_procedure(pattern_setting, rename_procedure):
  rename_procedure['display_name'].set_value(_('Rename to "{}"').format(pattern_setting.value))


def _handle_export_procedure_item_added(item):
  pg.config.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE.add(
    item.action['arguments/file_extension'])

  item.action['arguments/file_extension'].gui.widget.connect(
    'changed',
    lambda _entry, setting: export_settings_.apply_file_extension_gui_to_setting_if_valid(setting),
    item.action['arguments/file_extension'])

  export_settings_.revert_file_extension_gui_to_last_valid_value(
    item.action['arguments/file_extension'])

  item.action['arguments/file_extension'].gui.widget.connect(
    'focus-out-event',
    lambda _entry, _event, setting: (
      export_settings_.revert_file_extension_gui_to_last_valid_value(setting)),
    item.action['arguments/file_extension'])

  _set_display_name_for_export_procedure(
    item.action['arguments/file_extension'],
    item.action)

  item.action['arguments/file_extension'].connect_event(
    'value-changed',
    _set_display_name_for_export_procedure,
    item.action)


def _set_display_name_for_export_procedure(file_extension_setting, export_procedure):
  file_extension = file_extension_setting.value.upper() if file_extension_setting.value else ''

  export_procedure_name = None
  if export_procedure['orig_name'].value == 'export_for_edit_layers':
    export_procedure_name = _('Export as {}')
  elif export_procedure['orig_name'].value.startswith('export_for_'):
    export_procedure_name = _('Also export as {}')

  if export_procedure_name is not None:
    export_procedure['display_name'].set_value(export_procedure_name.format(file_extension))


def _handle_export_procedure_item_added_for_export_mode(item, settings):
  _copy_setting_values_from_default_export_procedure(settings['main'], item.action)


def _copy_setting_values_from_default_export_procedure(main_settings, export_procedure):
  if main_settings['output_directory'].value:
    export_procedure['arguments/output_directory'].set_value(
      main_settings['output_directory'].value)

  export_procedure['arguments/file_extension'].set_value(main_settings['file_extension'].value)

  for setting in main_settings['export']:
    export_procedure[f'arguments/{setting.name}'].set_value(setting.value)


def _set_buttons_for_action_item_sensitive(item, sensitive):
  item.button_remove.set_sensitive(sensitive)


def _on_constraint_item_added(_constraint_list, item, _settings):
  if item.action['orig_name'].value == 'matching_text':
    _handle_matching_text_constraint_item_added(item)


def _set_up_existing_matching_text_constraints(constraint_list: action_list_.ActionList):
  for item in constraint_list.items:
    if item.action['orig_name'].value == 'matching_text':
      _handle_matching_text_constraint_item_added(item)


def _handle_matching_text_constraint_item_added(item):
  _set_display_name_for_matching_text_constraint(
    item.action['arguments/match_mode'],
    item.action['arguments/text'],
    item.action['arguments/ignore_case_sensitivity'],
    item.action)

  item.action['arguments/match_mode'].connect_event(
    'value-changed',
    _set_display_name_for_matching_text_constraint,
    item.action['arguments/text'],
    item.action['arguments/ignore_case_sensitivity'],
    item.action)

  item.action['arguments/text'].connect_event(
    'value-changed',
    lambda text_setting, match_mode_setting, ignore_case_sensitivity_setting, constraint: (
      _set_display_name_for_matching_text_constraint(
        match_mode_setting, text_setting, ignore_case_sensitivity_setting, constraint)),
    item.action['arguments/match_mode'],
    item.action['arguments/ignore_case_sensitivity'],
    item.action)

  item.action['arguments/ignore_case_sensitivity'].connect_event(
    'value-changed',
    lambda ignore_case_sensitivity_setting, match_mode_setting, text_setting, constraint: (
      _set_display_name_for_matching_text_constraint(
        match_mode_setting, text_setting, ignore_case_sensitivity_setting, constraint)),
    item.action['arguments/match_mode'],
    item.action['arguments/text'],
    item.action)


def _set_display_name_for_matching_text_constraint(
      match_mode_setting, text_setting, ignore_case_sensitivity_setting, constraint):
  display_name = None

  if match_mode_setting.value == builtin_constraints.MatchModes.STARTS_WITH:
    if text_setting.value:
      display_name = _('Starting with "{}"').format(text_setting.value)
    else:
      display_name = _('Starting with any text')
  elif match_mode_setting.value == builtin_constraints.MatchModes.CONTAINS:
    if text_setting.value:
      display_name = _('Containing "{}"').format(text_setting.value)
    else:
      display_name = _('Containing any text')
  elif match_mode_setting.value == builtin_constraints.MatchModes.ENDS_WITH:
    if text_setting.value:
      display_name = _('Ending with "{}"').format(text_setting.value)
    else:
      display_name = _('Ending with any text')
  elif match_mode_setting.value == builtin_constraints.MatchModes.REGEX:
    display_name = _('Matching pattern "{}"').format(text_setting.value)

  if display_name is not None:
    if ignore_case_sensitivity_setting.value:
      # FOR TRANSLATORS: Think of "case-insensitive matching" when translating this
      display_name += _(' (case-insensitive)')

    constraint['display_name'].set_value(display_name)
