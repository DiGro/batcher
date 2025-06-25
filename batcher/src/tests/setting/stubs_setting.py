"""Stubs primarily to be used in the `test_setting` module."""

from gi.repository import GObject

from src.setting import presenter as presenter_
from src.setting import settings as settings_

from src.tests import stubs_gimp


class GuiWidgetStub:
  
  def __init__(self, value, width=100, height=20):
    self.value = value
    self.sensitive = True
    self.visible = True

    self.width = width
    self.height = height
    
    self._signal = None
    self._event_handler = None
  
  def connect(self, signal, event_handler):
    self._signal = signal
    self._event_handler = event_handler
  
  def disconnect(self):
    self._signal = None
    self._event_handler = None
  
  def set_value(self, value):
    self.value = value
    if self._event_handler is not None:
      self._event_handler()


class CheckButtonStub(GuiWidgetStub):
  pass


class StubPresenter(presenter_.Presenter):
  
  def get_sensitive(self):
    return self._widget.sensitive
  
  def set_sensitive(self, sensitive):
    self._widget.sensitive = sensitive

  def get_visible(self):
    return self._widget.visible
  
  def set_visible(self, visible):
    self._widget.visible = visible
  
  def _create_widget(self, setting, **kwargs):
    return GuiWidgetStub(setting.value)
  
  def get_value(self):
    return self._widget.value
  
  def _set_value(self, value):
    self._widget.value = value
  
  def _connect_value_changed_event(self):
    self._widget.connect(self._VALUE_CHANGED_SIGNAL, self._on_value_changed)
  
  def _disconnect_value_changed_event(self):
    self._widget.disconnect()


class StubWithCustomKwargsInCreateWidgetPresenter(StubPresenter):
  
  def _create_widget(self, setting, width=100, height=20, **kwargs):
    return GuiWidgetStub(setting.value, width=width, height=height)


class StubWithValueChangedSignalPresenter(StubPresenter):

  _VALUE_CHANGED_SIGNAL = 'changed'


class StubWithoutGuiWidgetCreationPresenter(StubPresenter):
  
  def _create_widget(self, setting, **kwargs):
    return None


class CheckButtonStubPresenter(StubPresenter):
  
  def _create_widget(self, setting, **kwargs):
    return CheckButtonStub(setting.value)


class YesNoToggleButtonStubPresenter(StubPresenter):
  pass


class StubSetting(settings_.Setting):
  
  _DEFAULT_DEFAULT_VALUE = 0
  
  def _validate(self, value):
    if value is None:
      return 'value cannot be None', 'invalid_value'


class StubWithCallableDefaultDefaultValueSetting(StubSetting):
  
  _DEFAULT_DEFAULT_VALUE = lambda self: f'_{self.name}'


class StubRegistrableSetting(StubSetting):

  _ALLOWED_PDB_TYPES = [stubs_gimp.StubGObjectType.__gtype__]

  _REGISTRABLE_TYPE_NAME = 'stub_registrable'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._name,
      self._display_name,
      self._description,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]


class StubWithGuiSetting(StubSetting):
  
  _ALLOWED_GUI_TYPES = [
    CheckButtonStubPresenter,
    StubPresenter,
    StubWithCustomKwargsInCreateWidgetPresenter,
    StubWithValueChangedSignalPresenter,
    StubWithoutGuiWidgetCreationPresenter,
  ]


def on_file_extension_changed(file_extension, flatten):
  if file_extension.value == 'png':
    flatten.set_value(False)
    flatten.gui.set_sensitive(True)
  else:
    flatten.set_value(True)
    flatten.gui.set_sensitive(False)


def on_file_extension_changed_with_resize_to_layer_size(file_extension, resize_to_layer_size):
  if file_extension.value == 'png':
    resize_to_layer_size.gui.set_visible(True)
  else:
    resize_to_layer_size.gui.set_visible(False)


def on_resize_to_layer_size_changed(
      resize_to_layer_size, file_extension, file_extension_value='jpg'):
  if resize_to_layer_size.value:
    file_extension.set_value(file_extension_value)
