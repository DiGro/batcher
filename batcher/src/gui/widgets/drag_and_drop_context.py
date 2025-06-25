"""Class providing drag-and-drop capability to any GTK widget."""

import collections
from collections.abc import Iterable
from typing import Callable, Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'DragAndDropContext',
]


class DragAndDropContext:
  """Class adding drag-and-drop capability to a `Gtk.Widget`."""
  
  def __init__(self):
    self._drag_type = self._get_unique_drag_type()

    self._widgets_and_event_ids = collections.defaultdict(dict)
  
  def setup_drag(
        self,
        widget: Gtk.Widget,
        get_drag_data_func: Callable,
        drag_data_receive_func: Callable,
        get_drag_data_args: Optional[Iterable] = None,
        drag_data_receive_args: Optional[Iterable] = None,
        get_drag_icon_func: Callable = None,
        get_drag_icon_func_args: Optional[Iterable] = None,
        destroy_drag_icon_func: Callable = None,
        destroy_drag_icon_func_args: Optional[Iterable] = None,
        dest_widget: Optional[Gtk.Widget] = None,
  ):
    """Enables dragging for the specified `Gtk.widget` instance.

    The displayed ``widget`` is used as the drag icon.

    Args:
      widget:
        Widget to enable dragging for.
      get_drag_data_func:
        Function returning data as a string describing the dragged widget.
      drag_data_receive_func:
        Function processing the data returned by ``get_drag_data_func``.
      get_drag_data_args:
        Optional positional arguments for ``get_drag_data_func``.
      drag_data_receive_args:
        Optional positional arguments for ``drag_data_receive_func``.
      get_drag_icon_func:
        Function to generate an icon when the dragging begins. If omitted, the
        default icon assigned by the application will be used.
        This function requires two arguments - the widget for which the dragging
        is initiated (equivalent to ``widget``), and a `Gdk.DragContext`
        instance.
      get_drag_icon_func_args:
        Optional additional positional arguments for ``get_drag_icon_func``.
      destroy_drag_icon_func:
        Function to destroy a drag icon created by ``get_drag_icon_func``. Only
        applicable if ``get_drag_icon_func`` is not ``None``.
      destroy_drag_icon_func_args:
        Optional additional positional arguments for ``destroy_drag_icon_func``.
      dest_widget:
        Optional different widget to use as the drag destination. You may e.g.
        use a child of ``widget`` as a drag destination to limit the area where
        ``widget`` can be dropped.
    """
    if get_drag_data_args is None:
      get_drag_data_args = ()
    
    if drag_data_receive_args is None:
      drag_data_receive_args = ()

    self._widgets_and_event_ids[widget]['drag-data-get'] = widget.connect(
      'drag-data-get',
      self._on_widget_drag_data_get,
      get_drag_data_func,
      get_drag_data_args)
    widget.drag_source_set(
      Gdk.ModifierType.BUTTON1_MASK,
      [Gtk.TargetEntry.new(self._drag_type, 0, 0)],
      Gdk.DragAction.MOVE)

    if dest_widget is None:
      dest_widget = widget

    self._widgets_and_event_ids[widget]['drag-data-received'] = dest_widget.connect(
      'drag-data-received',
      self._on_widget_drag_data_received,
      drag_data_receive_func,
      *drag_data_receive_args)
    dest_widget.drag_dest_set(
      Gtk.DestDefaults.ALL,
      [Gtk.TargetEntry.new(self._drag_type, 0, 0)],
      Gdk.DragAction.MOVE)

    if get_drag_icon_func is not None:
      self._widgets_and_event_ids[widget]['drag-begin'] = widget.connect(
        'drag-begin',
        get_drag_icon_func,
        *(get_drag_icon_func_args if get_drag_icon_func_args is not None else ()))
      if destroy_drag_icon_func is not None:
        self._widgets_and_event_ids[widget]['drag-end'] = widget.connect(
          'drag-end',
          destroy_drag_icon_func,
          *(destroy_drag_icon_func_args if destroy_drag_icon_func_args is not None else ()))

  def remove_drag(self, widget: Gtk.Widget):
    """Removes drag-and-drop capability from the specified `Gtk.widget`
    instance.

    The widget must have its drag-and-drop capability enabled via
    `setup_drag()`. Otherwise, `ValueError` is raised.

    Args:
      widget: Widget to remove drag-and-drop capability from.
    """
    if widget not in self._widgets_and_event_ids:
      raise ValueError(
        f'widget {widget} was not set up with this DragAndDropContext instance: {self}')

    widget_events = self._widgets_and_event_ids.pop(widget)

    widget.disconnect(widget_events['drag-data-get'])
    widget.drag_source_unset()

    widget.disconnect(widget_events['drag-data-received'])
    widget.drag_dest_unset()

    if 'drag-begin' in widget_events:
      widget.disconnect(widget_events['drag-begin'])

    if 'drag-end' in widget_events:
      widget.disconnect(widget_events['drag-end'])

  def _get_unique_drag_type(self):
    return f'{type(self).__qualname__}_{id(self)}'
  
  @staticmethod
  def _on_widget_drag_data_get(
        _widget,
        _drag_context,
        selection_data,
        _info,
        _timestamp,
        get_drag_data_func,
        get_drag_data_args):
    selection_data.set(selection_data.get_target(), 8, get_drag_data_func(*get_drag_data_args))
  
  @staticmethod
  def _on_widget_drag_data_received(
        _widget,
        _drag_context,
        _drop_x,
        _drop_y,
        selection_data,
        _info,
        _timestamp,
        drag_data_receive_func,
        *drag_data_receive_args):
    drag_data_receive_func(selection_data.get_data(), *drag_data_receive_args)
