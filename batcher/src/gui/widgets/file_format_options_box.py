"""Widget for updating file format-specific options."""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from src.gui import utils_grid as gui_utils_grid_


__all__ = [
  'FileFormatOptionsBox',
]


class FileFormatOptionsBox(Gtk.Box):

  def __init__(
        self,
        initial_header_title=None,
        row_spacing=3,
        column_spacing=8,
        header_spacing=8,
        left_margin=12,
  ):
    super().__init__()

    self._initial_header_title = initial_header_title
    self._row_spacing = row_spacing
    self._column_spacing = column_spacing
    self._header_spacing = header_spacing
    self._left_margin = left_margin

    self._grids_per_file_format = {}
    # We use this to detect if a `setting.Group` instance holding
    # file format options changed, in which case we need to create a new
    # `Gtk.Grid`.
    self._file_format_options_dict = {}

    self._init_gui()

  def set_active_file_format(self, active_file_format, file_format_options):
    if len(self.get_children()) > 1:
      self.remove(self.get_children()[-1])

    self._label_header.set_label(
      '<b>' + _('{} options').format(active_file_format.upper()) + '</b>')

    if file_format_options is None:
      self._label_message.set_label('<i>{}</i>'.format(_('File format not recognized')))
      self._label_message.show()

      self.pack_start(self._label_message, False, False, 0)

      return

    if not file_format_options:
      self._label_message.set_label('<i>{}</i>'.format(_('File format has no options')))
      self._label_message.show()

      self.pack_start(self._label_message, False, False, 0)

      return

    self._label_message.hide()

    if (active_file_format not in self._grids_per_file_format
        or file_format_options != self._file_format_options_dict.get(active_file_format)):
      grid = self._create_file_format_options_grid(file_format_options)

      self._grids_per_file_format[active_file_format] = grid
      self._file_format_options_dict[active_file_format] = file_format_options

    self.pack_start(self._grids_per_file_format[active_file_format], False, False, 0)

  def _init_gui(self):
    self._label_header = Gtk.Label(
      label=f'<b>{self._initial_header_title}</b>',
      xalign=0.0,
      use_markup=True,
      use_underline=False,
      ellipsize=Pango.EllipsizeMode.END,
    )

    self._label_message = Gtk.Label(
      xalign=0.5,
      use_markup=True,
      use_underline=False,
      no_show_all=True,
      margin_bottom=self._header_spacing,
      ellipsize=Pango.EllipsizeMode.END,
    )

    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.set_spacing(self._header_spacing)

    self.pack_start(self._label_header, False, False, 0)

    self.show_all()

  def _create_file_format_options_grid(self, file_format_options):
    grid = Gtk.Grid(
      row_spacing=self._row_spacing,
      column_spacing=self._column_spacing,
      margin_start=self._left_margin,
      margin_bottom=self._header_spacing,
    )

    file_format_options.initialize_gui(only_null=True)

    for row_index, setting in enumerate(file_format_options):
      gui_utils_grid_.attach_label_to_grid(grid, setting, row_index)
      gui_utils_grid_.attach_widget_to_grid(grid, setting, row_index)

    grid.show_all()

    return grid


GObject.type_register(FileFormatOptionsBox)
