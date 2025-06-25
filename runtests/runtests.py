"""Running automated tests.

By default, all modules starting with the `'test_'` prefix will be run.

To run tests in GIMP:

1. Open up the Python-Fu console (Filters -> Python-Fu -> Console).
2. Choose ``Browse...`` and find the ``'plug-in-run-tests'`` procedure.
3. Hit ``Apply``. The procedure call is copied to the console with placeholder
   arguments.
4. Adjust the arguments as needed. The run mode does not matter as the procedure
   is always non-interactive. Make sure to wrap the ``modules`` and
  ``ignored-modules`` arguments in
  ``GObject.Value(GObject.TYPE_STRV, [<module names...>])``, otherwise the
  procedure fails with an error.
5. Run the command.

To repeat the tests, simply call the procedure again.
"""

import importlib
import inspect
import os
import pkgutil
import sys
import unittest
from typing import List, Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

MODULE_DIRPATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
ROOT_DIRPATH = os.path.dirname(MODULE_DIRPATH)
PLUGIN_DIRPATH = os.path.join(ROOT_DIRPATH, 'batcher')

if PLUGIN_DIRPATH not in sys.path:
  sys.path.append(PLUGIN_DIRPATH)

from src import procedure as procedure_
from src import utils

utils.initialize_i18n()


def plug_in_run_tests(
      _procedure: Gimp.Procedure,
      config: Gimp.ProcedureConfig,
      _data: Optional[bytes],
):
  run_tests(
    config.get_property('directory'),
    config.get_property('prefix'),
    config.get_property('modules'),
    config.get_property('ignored-modules'),
    config.get_property('output-stream'),
    config.get_property('verbose'),
  )


def run_tests(
      directory: Gio.File,
      test_module_name_prefix: str = 'test_',
      modules: Optional[List[str]] = None,
      ignored_modules: Optional[List[str]] = None,
      output_stream: str = 'stderr',
      verbose: bool = False,
):
  """Runs all modules containing tests located in the specified directory.

  Modules containing tests are considered those that contain the
  ``test_module_name_prefix`` prefix.

  ``ignored_modules`` is a list of prefixes matching test modules or packages
  to ignore.
  
  If ``modules`` is ``None`` or empty, all modules are included, except those
  specified in ``ignored_modules``. If ``modules`` is not ``None``,
  only modules matching the prefixes specified in ``modules`` are included.
  ``ignored_modules`` can be used to exclude submodules in ``modules``.
  
  ``output_stream`` is the name of the stream to print the output to -
  ``'stdout'``, ``'stderr'`` or a file path.
  """
  module_names = []
  
  if not modules:
    modules = []

  if not ignored_modules:
    ignored_modules = []

  if not modules:
    should_append = (
      lambda name: not any(name.startswith(ignored_module) for ignored_module in ignored_modules))
  else:
    should_append = (
      lambda name: (
        any(name.startswith(module_) for module_ in modules)
        and not any(name.startswith(ignored_module) for ignored_module in ignored_modules)))

  for importer, module_name, is_package in pkgutil.walk_packages(path=[directory.get_path()]):
    if should_append(module_name):
      if is_package:
        if importer.path not in sys.path:
          sys.path.append(importer.path)

      module_names.append(module_name)

  stream = _get_output_stream(output_stream)

  for module_name in module_names:
    if module_name.split('.')[-1].startswith(test_module_name_prefix):
      module = importlib.import_module(module_name)
      run_test(module, stream=stream, verbose=verbose)

  stream.close()


def run_test(module, stream=sys.stderr, verbose=False):
  if verbose:
    test_runner_output_stream = stream
  else:
    test_runner_output_stream = open(os.devnull, 'w')

  test_suite = unittest.TestLoader().loadTestsFromModule(module)

  test_runner = unittest.TextTestRunner(stream=test_runner_output_stream)

  result = test_runner.run(test_suite)

  if not verbose:
    _print_error_output(result, module, stream)


def _print_error_output(result, module, stream):
  if result.testsRun == 0:
    print(80 * '=', file=stream)
    print(f'No tests found in module {module.__name__}', file=stream)
    print(80 * '-' + '\n', file=stream)

  if result.failures or result.errors or result.unexpectedSuccesses:
    if result.failures:
      _print_failure(result.failures, stream, 'FAIL')

    if result.errors:
      _print_failure(result.errors, stream, 'ERROR')

    if result.unexpectedSuccesses:
      _print_failure(result.unexpectedSuccesses, stream, 'UNEXPECTED SUCCESS')


def _print_failure(failures, stream, header=None):
  if header is None:
    processed_header = ''
  else:
    processed_header = f'{header}: '

  for test_case, message in failures:
    print(80 * '=', file=stream)
    print(f'{processed_header}{test_case}', file=stream)
    print(80 * '-', file=stream)
    print(f'{message.strip()}\n', file=stream)


def _get_output_stream(stream_or_filepath):
  if hasattr(sys, stream_or_filepath):
    return _Stream(getattr(sys, stream_or_filepath))
  else:
    return open(stream_or_filepath, 'w')
  

class _Stream:
  
  def __init__(self, stream):
    self.stream = stream
  
  def write(self, data):
    self.stream.write(data)
  
  def flush(self):
    if hasattr(self.stream, 'flush'):
      self.stream.flush()
  
  def close(self):
    pass


procedure_.register_procedure(
  plug_in_run_tests,
  procedure_type=Gimp.Procedure,
  arguments=[
    [
      'enum',
      'run-mode',
      'Run mode',
      'The run mode',
      Gimp.RunMode,
      Gimp.RunMode.NONINTERACTIVE,
      GObject.ParamFlags.READWRITE,
    ],
    [
      'file',
      'directory',
      '_Directory',
      'Directory path containing test modules',
      Gimp.FileChooserAction.SELECT_FOLDER,
      False,
      Gio.file_new_for_path(PLUGIN_DIRPATH),
      GObject.ParamFlags.READWRITE,
    ],
    [
      'string',
      'prefix',
      '_Prefix of test modules',
      'Prefix of test modules',
      'test_',
      GObject.ParamFlags.READWRITE,
    ],
    [
      'string_array',
      'modules',
      'Modules to _include',
      'Modules to include',
      GObject.ParamFlags.READWRITE,
    ],
    [
      'string_array',
      'ignored_modules',
      'Modules to i_gnore',
      'Modules to ignore',
      GObject.ParamFlags.READWRITE,
    ],
    [
      'string',
      'output_stream',
      '_Output stream',
      'Output stream or file path to write output to',
      'stderr',
      GObject.ParamFlags.READWRITE,
    ],
    [
      'boolean',
      'verbose',
      '_Verbose',
      'If True, writes more detailed output',
      False,
      GObject.ParamFlags.READWRITE,
    ],
  ],
  documentation=('Runs automated tests in the specified directory path', ''),
)


procedure_.main()
