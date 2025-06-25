"""Widget representing a single command (action/condition) in the GUI."""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from . import editor as command_editor_

from src.gui import messages as gui_messages_
from src.gui import utils as gui_utils_
from src.gui import widgets as gui_widgets_


class CommandItem(gui_widgets_.ItemBoxItem):

  _LABEL_COMMAND_NAME_MAX_WIDTH_CHARS = 50

  _DRAG_ICON_WIDTH = 250
  _DRAG_ICON_BORDER_WIDTH = 4

  def __init__(self, command, attach_editor_widget=True):
    self._command = command
    self._attach_editor_widget = attach_editor_widget

    self._display_warning_message_event_id = None
    self._drag_icon_window = None

    self._button_command = self._command['enabled'].gui.widget

    self._on_command_enabled_changed_event_id = (
      self._command['enabled'].connect_event('value-changed', self._on_command_enabled_changed))

    super().__init__(self._button_command, button_display_mode='always')

    self._init_gui()

    self._button_edit.connect('clicked', self._on_button_edit_clicked)
    self._button_remove.connect('clicked', lambda *args: self.editor.destroy())

    if self._command['display_options_on_create'].value:
      self._command['display_options_on_create'].set_value(False)
      self.widget.connect('realize', lambda *args: self.editor.show_all())

    self.editor.connect('close', self._on_command_edit_dialog_close)
    self.editor.connect('response', self._on_command_edit_dialog_response)

  @property
  def command(self):
    return self._command

  @property
  def editor(self):
    return self._editor

  @property
  def drag_icon(self):
    return self._drag_icon_window

  @property
  def button_edit(self) -> Gtk.Button:
    return self._button_edit

  def is_being_edited(self):
    return self.editor.get_mapped()

  def set_tooltip(self, text):
    self.widget.set_tooltip_text(text)

  def reset_tooltip(self):
    self._set_tooltip_if_label_does_not_fit_text(self._label_command_name)

  def has_warning(self):
    return self._button_warning.get_visible()

  def set_warning(self, show, main_message=None, failure_message=None, details=None, parent=None):
    if show:
      self.set_tooltip(failure_message)

      if self._display_warning_message_event_id is not None:
        self._button_warning.disconnect(self._display_warning_message_event_id)

      self._display_warning_message_event_id = self._button_warning.connect(
        'clicked',
        self._on_button_warning_clicked, main_message, failure_message, details, parent)

      self._button_warning.show()
    else:
      self._button_warning.hide()

      self.reset_tooltip()
      if self._display_warning_message_event_id is not None:
        self._button_warning.disconnect(self._display_warning_message_event_id)
        self._display_warning_message_event_id = None

  def create_drag_icon(self):
    if self._drag_icon_window is not None:
      # We do not destroy the widget on "drag-end" so that an animation
      # indicating failed dragging is played.
      self._drag_icon_window.destroy()
      self._drag_icon_window = None

    button = Gtk.CheckButton(label=self._command['display_name'].value)
    button.get_child().set_xalign(0.0)
    button.get_child().set_yalign(0.5)
    button.get_child().set_ellipsize(Pango.EllipsizeMode.END)
    button.get_child().set_can_focus(False)

    button.set_border_width(self._DRAG_ICON_BORDER_WIDTH)
    button.set_can_focus(False)

    button.set_active(self._command['enabled'].value)

    frame = Gtk.Frame(shadow_type=Gtk.ShadowType.OUT)
    frame.add(button)

    self._drag_icon_window = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      screen=self.widget.get_screen(),
      width_request=self._DRAG_ICON_WIDTH,
    )
    self._drag_icon_window.add(frame)
    self._drag_icon_window.show_all()

    return self._drag_icon_window

  def prepare_command_for_detachment(self):
    self._command['enabled'].remove_event(self._on_command_enabled_changed_event_id)

  def _init_gui(self):
    self._label_command_name = self._command['display_name'].gui.widget.get_child()
    self._label_command_name.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_command_name.set_max_width_chars(self._LABEL_COMMAND_NAME_MAX_WIDTH_CHARS)
    self._label_command_name.connect('size-allocate', self._on_label_command_name_size_allocate)

    self._button_edit = self._setup_item_button(icon=GimpUi.ICON_EDIT, position=0)
    self._button_edit.set_tooltip_text(_('Edit'))

    self._editor = command_editor_.CommandEditor(
      self._command,
      self.widget,
      attach_editor_widget=self._attach_editor_widget,
      title=self._command['display_name'].value,
    )
    self.widget.connect('realize', self._on_command_widget_realize)

    self._button_remove.set_tooltip_text(_('Remove'))

    self._button_warning = self._setup_item_indicator_button(
      icon=GimpUi.ICON_DIALOG_WARNING, position=0)

  def _on_label_command_name_size_allocate(self, label_command_name, _allocation):
    self._set_tooltip_if_label_does_not_fit_text(label_command_name)

  def _on_command_widget_realize(self, _dialog):
    self.editor.set_transient_for(gui_utils_.get_toplevel_window(self.widget))
    self.editor.set_attached_to(gui_utils_.get_toplevel_window(self.widget))

  def _set_tooltip_if_label_does_not_fit_text(self, label_command_name):
    if gui_utils_.label_fits_text(label_command_name):
      self.widget.set_tooltip_text(None)
    else:
      self.widget.set_tooltip_text(label_command_name.get_text())

  def _on_button_edit_clicked(self, _button):
    if self.is_being_edited():
      self.editor.present()
    else:
      self.editor.show_all()

  @staticmethod
  def _on_button_warning_clicked(_button, main_message, short_message, full_message, parent):
    gui_messages_.display_failure_message(main_message, short_message, full_message, parent=parent)

  def _on_command_enabled_changed(self, _setting):
    self._command['arguments'].apply_gui_values_to_settings(force=True)

  def _on_command_edit_dialog_close(self, _dialog):
    self.editor.hide()

  def _on_command_edit_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.CLOSE:
      self.editor.hide()
