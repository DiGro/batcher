"""Exceptions used in `setting.sources` and `setting.persistor` modules."""

import traceback as traceback_

__all__ = [
  'SourceError',
  'SourceNotFoundError',
  'SourceInvalidFormatError',
  'SourceModifyDataError',
  'SourceReadError',
  'SourceWriteError',
]


class SourceError(Exception):
  
  def __init__(self, message=''):
    super().__init__(message)

    if not hasattr(self, 'message'):
      self.message = message

    self.traceback = traceback_.format_exc()
  
  def __str__(self):
    if self.traceback and not self.message:
      return self.traceback
    else:
      return self.message


class SourceNotFoundError(SourceError):
  pass


class SourceInvalidFormatError(SourceError):
  pass


class SourceModifyDataError(SourceError):
  pass


class SourceReadError(SourceError):
  pass


class SourceWriteError(SourceError):
  pass
