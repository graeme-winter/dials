#!/usr/bin/env python
#
# dials.util.__init__.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import division


class HalError(RuntimeError):
  def __init__(self, string=''):

    # Get the username
    try:
      from getpass import getuser
      username = getuser()
    except Exception:
      username = 'Dave'

    # Put in HAL error text.
    text = 'I\'m sorry {0}. I\'m afraid I can\'t do that. {1}'.format(
        username, string)

    # Init base class
    RuntimeError.__init__(self, text)


def halraiser(e):
  ''' Function to re-raise an exception with a Hal message. '''

  # Get the username
  try:
    from getpass import getuser
    username = getuser()
  except Exception:
    username = 'Humanoid'

  # Put in HAL error text.
  text = 'I\'m sorry {0}. I\'m afraid I can\'t do that.'.format(username)

  # Append to exception
  if len(e.args) == 0:
    e.args = (text,)
  elif len(e.args) == 1:
    e.args = (text + ' ' + str(e.args[0]),)
  else:
    e.args = (text,) + e.args

  # Reraise the exception
  raise


class MPState(object):
  ''' Class to hold global state for multiprocessing. '''
  def __init__(self):
    self.nproc = 1
    self.method = 'multiprocessing'

# Global variable for multiprocessing
mp = MPState()
