# -*- coding: utf-8 -*-.

"""
pygsheets.datarange
~~~~~~~~~~~~~~~~~~~

This module contains DataRange class for storing/manuplating a range of data in spreadsheet. This classs can
be used for group operations, eg changing format of ll cells in a given range. This can also represent, named ranges
protetced ranegs, banned ranges etc.

"""

import warnings

from .utils import format_addr
from .exceptions import InvalidArgumentValue


class DataRange(object):

    def __init__(self, start=None, end=None, worksheet=None, name='', data=None, name_id=None, namedjson=None):
        self._worksheet = worksheet
        if namedjson:
            start = (namedjson['range']['startRowIndex']+1, namedjson['range']['startColumnIndex']+1)
            end = (namedjson['range']['endRowIndex'], namedjson['range']['endColumnIndex'])
            name_id = namedjson['namedRangeId']
        data = [[]]
        self._start_addr = format_addr(start, 'tuple')
        self._end_addr = format_addr(end, 'tuple')
        if data:
            if len(data) != end[0] - start[0] + 1 or len(data[0]) != end[1] - start[1] + 1:
                self._data = data
        self._linked = False

        self._name_id = name_id
        self._name = name

        self._protected = False
        self.protected_properties = ProtectedRange()
        self._banned = False

    @property
    def name(self):
        """name of the named range, setting a name will make this a range a named range
            setting this to '' will delete the named range
        """
        return self._name

    @name.setter
    def name(self, name):
        if type(name) is not str:
            raise InvalidArgumentValue('name should be a string')
        if name == '':
            self._worksheet.delete_named_range(self._name)
            self._name = ''
        else:
            if self._name == '':
                self._worksheet.create_named_range(name, start=self._start_addr, end=self._end_addr)
            else:
                self._name = name
                if self._linked:
                    self.update_named_range()

    @property
    def name_id(self):
        return self._name_id

    @property
    def protect(self):
        """if this range is protected"""
        return self._protected

    # @TODO
    @protect.setter
    def protect(self, value):
        warnings.warn('functionality not implimented')
        if value:
            self._worksheet.create_protected_range()
        else:
            self._worksheet.remove_protected_range()

    @property
    def start_addr(self):
        """topleft adress of the range"""
        return self._start_addr

    @start_addr.setter
    def start_addr(self, addr):
        self._start_addr = format_addr(addr, 'tuple')
        if self._linked:
            self.update_named_range()

    @property
    def end_addr(self):
        """bottomright adress of the range"""
        return self._end_addr

    @end_addr.setter
    def end_addr(self, addr):
        self._end_addr = format_addr(addr, 'tuple')
        if self._linked:
            self.update_named_range()

    def link(self, update=True):
        """link the dstarange so that all propertis are synced right after setting them"""
        self._linked = True
        if update:
            self.update_named_range()

    def unlink(self):
        """unlink the sheet so that all properties are not synced as its changed"""
        self._linked = False

    def fetch(self, only_data=True):
        """
        update the range data/ properties from cloud
        :param only_data: fetch only data

        """
        self._data = self._worksheet.get_values(self._start_addr, self._end_addr, include_all=True, returnas='cells')
        if not only_data:
            pass

    def applay_format(self, cell):
        """
        Change format of all cells in the range
        :param cell: a model :class: Cell whose format will be applied to all cells
        """
        request = {"repeatCell": {
            "range": self._get_gridrange(),
            "cell": cell.get_json(),
            "fields": "*"
            }
        }
        self._worksheet.client.sh_batch_update(self._worksheet.spreadsheet.id, request, None, False)

    def sort(self):
        warnings.warn('Functionality not implimented')

    def update_named_range(self):
        """update the named properties"""
        if self._name_id == '':
            return False
        request = {'updateNamedRange':{
          "namedRange": {
              "namedRangeId": self._name_id,
              "name": self._name,
              "range": self._get_gridrange(),
          },
          "fields": '*',
        }}
        self._worksheet.client.sh_batch_update(self._worksheet.spreadsheet.id, request, batch=self._worksheet.spreadsheet.batch_mode)

    def _get_gridrange(self):
        return {
            "sheetId": self._worksheet.id,
            "startRowIndex": self._start_addr[0]-1,
            "endRowIndex": self._end_addr[0],
            "startColumnIndex": self._start_addr[1]-1,
            "endColumnIndex": self._end_addr[1],
        }

    def __repr__(self):
        crange = format_addr(self._start_addr) + ':' + format_addr(self._end_addr)
        return '<%s %s %s protected:%s>' % (self.__class__.__name__,
                                            str(self._name), str(crange), self._protected)


class ProtectedRange(object):

    def __init__(self):
        self._protected_id = None
        self.description = ''
        self.warningOnly = False
        self.requestingUserCanEdit = False
        self.editors = None