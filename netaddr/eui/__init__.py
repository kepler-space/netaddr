#-----------------------------------------------------------------------------
#   Copyright (c) 2008 by David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
#-----------------------------------------------------------------------------
"""
Classes and functions for dealing with MAC addresses, EUI-48, EUI-64, OUI, IAB
identifiers.
"""

from string import hexdigits
from typing import Any, Iterator, overload, Tuple, Union

from netaddr.core import NotRegisteredError, AddrFormatError, DictDotLookup
from netaddr.strategy import eui48 as _eui48, eui64 as _eui64
from netaddr.strategy.eui48 import mac_eui48
from netaddr.strategy.eui64 import eui64_base
from netaddr.ip import IPAddress
from netaddr.compat import _importlib_resources, _is_int, _is_str


def iter_EUIRange(start: 'EUI',
                  end: 'EUI',
                  step: int = 1) -> Iterator['EUI']:
    """A generator that produces EUI objects between an arbitrary start and stop EUI address with
    intervals of step between them. Sequences produce are inclusive of boundary EUIs. In the case of
    negative stepping, `start` will be greater than `end`.

    Args:
        start (EUI): The starting EUI.
        end (EUI): The ending EUI.
        step (Optional[int], optional): The size of the step between EUIs. Defaults to 1.

    Raises:
        ValueError: The step argument cannot be zero.
    Yields:
        Iterator[EUI]: An iterator of one or more `EUI` objects.
    """
    end = int(end) + 1 if start < end else int(end) - 1
    for i in range(start, end, step):
        yield EUI(i)


class BaseIdentifier(object):
    """Base class for all IEEE identifiers."""
    __slots__ = ('_value', '__weakref__')

    def __init__(self):
        self._value = None

    def __int__(self):
        """:return: integer value of this identifier"""
        return self._value

    def __long__(self):
        """:return: integer value of this identifier"""
        return self._value

    def __oct__(self):
        """:return: octal string representation of this identifier."""
        #   Python 2.x only.
        if self._value == 0:
            return '0'
        return '0%o' % self._value

    def __hex__(self):
        """:return: hexadecimal string representation of this identifier."""
        #   Python 2.x only.
        return '0x%x' % self._value

    def __index__(self):
        """
        :return: return the integer value of this identifier when passed to
            hex(), oct() or bin().
        """
        #   Python 3.x only.
        return self._value


class OUI(BaseIdentifier):
    """
    An individual IEEE OUI (Organisationally Unique Identifier).

    For online details see - http://standards.ieee.org/regauth/oui/

    """
    __slots__ = ('records',)

    def __init__(self, oui):
        """
        Constructor

        :param oui: an OUI string ``XX-XX-XX`` or an unsigned integer. \
            Also accepts and parses full MAC/EUI-48 address strings (but not \
            MAC/EUI-48 integers)!
        """
        super(OUI, self).__init__()

        #   Lazy loading of IEEE data structures.
        from netaddr.eui import ieee

        self.records = []

        if isinstance(oui, str):
            #TODO: Improve string parsing here.
            #TODO: Accept full MAC/EUI-48 addressses as well as XX-XX-XX
            #TODO: and just take /16 (see IAB for details)
            self._value = int(oui.replace('-', ''), 16)
        elif _is_int(oui):
            if 0 <= oui <= 0xffffff:
                self._value = oui
            else:
                raise ValueError('OUI int outside expected range: %r' % (oui,))
        else:
            raise TypeError('unexpected OUI format: %r' % (oui,))

        #   Discover offsets.
        if self._value in ieee.OUI_INDEX:
            fh = _importlib_resources.open_binary(__package__, 'oui.txt')
            for (offset, size) in ieee.OUI_INDEX[self._value]:
                fh.seek(offset)
                data = fh.read(size).decode('UTF-8')
                self._parse_data(data, offset, size)
            fh.close()
        else:
            raise NotRegisteredError('OUI %r not registered!' % (oui,))

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other):
        if not isinstance(other, OUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return self._value == other._value

    def __ne__(self, other):
        if not isinstance(other, OUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return self._value != other._value

    def __getstate__(self):
        """:returns: Pickled state of an `OUI` object."""
        return self._value, self.records

    def __setstate__(self, state):
        """:param state: data used to unpickle a pickled `OUI` object."""
        self._value, self.records = state

    def _parse_data(self, data, offset, size):
        """Returns a dict record from raw OUI record data"""
        record = {
            'idx': 0,
            'oui': '',
            'org': '',
            'address': [],
            'offset': offset,
            'size': size,
        }

        for line in data.split("\n"):
            line = line.strip()
            if not line:
                continue

            if '(hex)' in line:
                record['idx'] = self._value
                record['org'] = line.split(None, 2)[2]
                record['oui'] = str(self)
            elif '(base 16)' in line:
                continue
            else:
                record['address'].append(line)

        self.records.append(record)

    @property
    def reg_count(self):
        """Number of registered organisations with this OUI"""
        return len(self.records)

    def registration(self, index=0):
        """
        The IEEE registration details for this OUI.

        :param index: the index of record (may contain multiple registrations)
            (Default: 0 - first registration)

        :return: Objectified Python data structure containing registration
            details.
        """
        return DictDotLookup(self.records[index])

    def __str__(self):
        """:return: string representation of this OUI"""
        int_val = self._value
        return "%02X-%02X-%02X" % (
                (int_val >> 16) & 0xff,
                (int_val >> 8) & 0xff,
                int_val & 0xff)

    def __repr__(self):
        """:return: executable Python string to recreate equivalent object."""
        return "OUI('%s')" % self


class IAB(BaseIdentifier):
    IAB_EUI_VALUES = (0x0050c2, 0x40d855)

    """
    An individual IEEE IAB (Individual Address Block) identifier.

    For online details see - http://standards.ieee.org/regauth/oui/

    """
    __slots__ = ('record',)

    @classmethod
    def split_iab_mac(cls, eui_int, strict=False):
        """
        :param eui_int: a MAC IAB as an unsigned integer.

        :param strict: If True, raises a ValueError if the last 12 bits of
            IAB MAC/EUI-48 address are non-zero, ignores them otherwise.
            (Default: False)
        """
        if (eui_int >> 12) in cls.IAB_EUI_VALUES:
            return eui_int, 0

        user_mask = 2 ** 12 - 1
        iab_mask = (2 ** 48 - 1) ^ user_mask
        iab_bits = eui_int >> 12
        user_bits = (eui_int | iab_mask) - iab_mask

        if (iab_bits >> 12) in cls.IAB_EUI_VALUES:
            if strict and user_bits != 0:
                raise ValueError('%r is not a strict IAB!' % hex(user_bits))
        else:
            raise ValueError('%r is not an IAB address!' % hex(eui_int))

        return iab_bits, user_bits

    def __init__(self, iab, strict=False):
        """
        Constructor

        :param iab: an IAB string ``00-50-C2-XX-X0-00`` or an unsigned \
            integer. This address looks like an EUI-48 but it should not \
            have any non-zero bits in the last 3 bytes.

        :param strict: If True, raises a ValueError if the last 12 bits \
            of IAB MAC/EUI-48 address are non-zero, ignores them otherwise. \
            (Default: False)
        """
        super(IAB, self).__init__()

        #   Lazy loading of IEEE data structures.
        from netaddr.eui import ieee

        self.record = {
            'idx': 0,
            'iab': '',
            'org': '',
            'address': [],
            'offset': 0,
            'size': 0,
        }

        if isinstance(iab, str):
            #TODO: Improve string parsing here.
            #TODO: '00-50-C2' is actually invalid.
            #TODO: Should be '00-50-C2-00-00-00' (i.e. a full MAC/EUI-48)
            int_val = int(iab.replace('-', ''), 16)
            iab_int, user_int = self.split_iab_mac(int_val, strict=strict)
            self._value = iab_int
        elif _is_int(iab):
            iab_int, user_int = self.split_iab_mac(iab, strict=strict)
            self._value = iab_int
        else:
            raise TypeError('unexpected IAB format: %r!' % (iab,))

        #   Discover offsets.
        if self._value in ieee.IAB_INDEX:
            fh = _importlib_resources.open_binary(__package__, 'iab.txt')
            (offset, size) = ieee.IAB_INDEX[self._value][0]
            self.record['offset'] = offset
            self.record['size'] = size
            fh.seek(offset)
            data = fh.read(size).decode('UTF-8')
            self._parse_data(data, offset, size)
            fh.close()
        else:
            raise NotRegisteredError('IAB %r not unregistered!' % (iab,))

    def __eq__(self, other):
        if not isinstance(other, IAB):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return self._value == other._value

    def __ne__(self, other):
        if not isinstance(other, IAB):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return self._value != other._value

    def __getstate__(self):
        """:returns: Pickled state of an `IAB` object."""
        return self._value, self.record

    def __setstate__(self, state):
        """:param state: data used to unpickle a pickled `IAB` object."""
        self._value, self.record = state

    def _parse_data(self, data, offset, size):
        """Returns a dict record from raw IAB record data"""
        for line in data.split("\n"):
            line = line.strip()
            if not line:
                continue

            if '(hex)' in line:
                self.record['idx'] = self._value
                self.record['org'] = line.split(None, 2)[2]
                self.record['iab'] = str(self)
            elif '(base 16)' in line:
                continue
            else:
                self.record['address'].append(line)

    def registration(self):
        """The IEEE registration details for this IAB"""
        return DictDotLookup(self.record)

    def __str__(self):
        """:return: string representation of this IAB"""
        int_val = self._value << 4

        return "%02X-%02X-%02X-%02X-%02X-00" % (
                (int_val >> 32) & 0xff,
                (int_val >> 24) & 0xff,
                (int_val >> 16) & 0xff,
                (int_val >> 8) & 0xff,
                int_val & 0xff)

    def __repr__(self):
        """:return: executable Python string to recreate equivalent object."""
        return "IAB('%s')" % self


class EUI(BaseIdentifier):
    """
    An IEEE EUI (Extended Unique Identifier).

    Both EUI-48 (used for layer 2 MAC addresses) and EUI-64 are supported.

    Input parsing for EUI-48 addresses is flexible, supporting many MAC
    variants.

    """
    __slots__ = ('_module', '_dialect')

    def __init__(self, addr, version=None, dialect=None):
        """
        Constructor.

        :param addr: an EUI-48 (MAC) or EUI-64 address in string format or \
            an unsigned integer. May also be another EUI object (copy \
            construction).

        :param version: (optional) the explicit EUI address version, either \
            48 or 64. Mainly used to distinguish EUI-48 and EUI-64 identifiers \
            specified as integers which may be numerically equivalent.

        :param dialect: (optional) the mac_* dialect to be used to configure \
            the formatting of EUI-48 (MAC) addresses.
        """
        super(EUI, self).__init__()

        self._module = None

        if isinstance(addr, EUI):
            #   Copy constructor.
            if version is not None and version != addr._module.version:
                raise ValueError('cannot switch EUI versions using '
                    'copy constructor!')
            self._module = addr._module
            self._value = addr._value
            self.dialect = addr.dialect
            return

        if version is not None:
            if version == 48:
                self._module = _eui48
            elif version == 64:
                self._module = _eui64
            else:
                raise ValueError('unsupported EUI version %r' % version)
        else:
        #   Choose a default version when addr is an integer and version is
        #   not specified.
            if _is_int(addr):
                if 0 <= addr <= 0xffffffffffff:
                    self._module = _eui48
                elif 0xffffffffffff < addr <= 0xffffffffffffffff:
                    self._module = _eui64

        self.value = addr

        #   Choose a dialect for MAC formatting.
        self.dialect = dialect

    def __getstate__(self):
        """:returns: Pickled state of an `EUI` object."""
        return self._value, self._module.version, self.dialect

    def __setstate__(self, state):
        """
        :param state: data used to unpickle a pickled `EUI` object.

        """
        value, version, dialect = state

        self._value = value

        if version == 48:
            self._module = _eui48
        elif version == 64:
            self._module = _eui64
        else:
            raise ValueError('unpickling failed for object state: %s' \
                % (state,))

        self.dialect = dialect

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if self._module is None:
            #   EUI version is implicit, detect it from value.
            for module in (_eui48, _eui64):
                try:
                    self._value = module.str_to_int(value)
                    self._module = module
                    break
                except AddrFormatError:
                    try:
                        if 0 <= int(value) <= module.max_int:
                            self._value = int(value)
                            self._module = module
                            break
                    except ValueError:
                        pass

            if self._module is None:
                raise AddrFormatError('failed to detect EUI version: %r'
                    % (value,))
        else:
            #   EUI version is explicit.
            if _is_str(value):
                try:
                    self._value = self._module.str_to_int(value)
                except AddrFormatError:
                    raise AddrFormatError('address %r is not an EUIv%d'
                        % (value, self._module.version))
            else:
                if 0 <= int(value) <= self._module.max_int:
                    self._value = int(value)
                else:
                    raise AddrFormatError('bad address format: %r' % (value,))

    value = property(_get_value, _set_value, None,
        'a positive integer representing the value of this EUI indentifier.')

    def _get_dialect(self):
        return self._dialect

    def _validate_dialect(self, value):
        if value is None:
            if self._module is _eui64:
               return eui64_base
            else:
                return mac_eui48
        else:
            if hasattr(value, 'word_size') and hasattr(value, 'word_fmt'):
                return value
            else:
                raise TypeError('custom dialects should subclass mac_eui48!')

    def _set_dialect(self, value):
        self._dialect = self._validate_dialect(value)

    dialect = property(_get_dialect, _set_dialect, None,
        "a Python class providing support for the interpretation of "
        "various MAC\n address formats.")

    @property
    def oui(self):
        """The OUI (Organisationally Unique Identifier) for this EUI."""
        if self._module == _eui48:
            return OUI(self.value >> 24)
        elif self._module == _eui64:
            return OUI(self.value >> 40)

    @property
    def ei(self):
        """The EI (Extension Identifier) for this EUI"""
        if self._module == _eui48:
            return '%02X-%02X-%02X' % tuple(self[3:6])
        elif self._module == _eui64:
            return '%02X-%02X-%02X-%02X-%02X' % tuple(self[3:8])

    def is_iab(self):
        """:return: True if this EUI is an IAB address, False otherwise"""
        return (self._value >> 24) in IAB.IAB_EUI_VALUES

    @property
    def iab(self):
        """
        If is_iab() is True, the IAB (Individual Address Block) is returned,
        ``None`` otherwise.
        """
        if self.is_iab():
            return IAB(self._value >> 12)

    @property
    def version(self):
        """The EUI version represented by this EUI object."""
        return self._module.version

    def __getitem__(self, idx):
        """
        :return: The integer value of the word referenced by index (both \
            positive and negative). Raises ``IndexError`` if index is out \
            of bounds. Also supports Python list slices for accessing \
            word groups.
        """
        if _is_int(idx):
            #   Indexing, including negative indexing goodness.
            num_words = self._dialect.num_words
            if not (-num_words) <= idx <= (num_words - 1):
                raise IndexError('index out range for address type!')
            return self._module.int_to_words(self._value, self._dialect)[idx]
        elif isinstance(idx, slice):
            words = self._module.int_to_words(self._value, self._dialect)
            return [words[i] for i in range(*idx.indices(len(words)))]
        else:
            raise TypeError('unsupported type %r!' % (idx,))

    def __setitem__(self, idx, value):
        """Set the value of the word referenced by index in this address"""
        if isinstance(idx, slice):
            #   TODO - settable slices.
            raise NotImplementedError('settable slices are not supported!')

        if not _is_int(idx):
            raise TypeError('index not an integer!')

        if not 0 <= idx <= (self._dialect.num_words - 1):
            raise IndexError('index %d outside address type boundary!' % (idx,))

        if not _is_int(value):
            raise TypeError('value not an integer!')

        if not 0 <= value <= self._dialect.max_word:
            raise IndexError('value %d outside word size maximum of %d bits!'
                % (value, self._dialect.word_size))

        words = list(self._module.int_to_words(self._value, self._dialect))
        words[idx] = value
        self._value = self._module.words_to_int(words)

    def __hash__(self):
        """:return: hash of this EUI object suitable for dict keys, sets etc"""
        return hash((self.version, self._value))

    def __eq__(self, other):
        """
        :return: ``True`` if this EUI object is numerically the same as other, \
            ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) == (other.version, other._value)

    def __ne__(self, other):
        """
        :return: ``True`` if this EUI object is numerically the same as other, \
            ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) != (other.version, other._value)

    def __lt__(self, other):
        """
        :return: ``True`` if this EUI object is numerically lower in value than \
            other, ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) < (other.version, other._value)

    def __le__(self, other):
        """
        :return: ``True`` if this EUI object is numerically lower or equal in \
            value to other, ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) <= (other.version, other._value)

    def __gt__(self, other):
        """
        :return: ``True`` if this EUI object is numerically greater in value \
            than other, ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) > (other.version, other._value)

    def __ge__(self, other):
        """
        :return: ``True`` if this EUI object is numerically greater or equal \
            in value to other, ``False`` otherwise.
        """
        if not isinstance(other, EUI):
            try:
                other = self.__class__(other)
            except Exception:
                return NotImplemented
        return (self.version, self._value) >= (other.version, other._value)

    def bits(self, word_sep=None):
        """
        :param word_sep: (optional) the separator to insert between words. \
            Default: None - use default separator for address type.

        :return: human-readable binary digit string of this address.
        """
        return self._module.int_to_bits(self._value, word_sep)

    @property
    def packed(self):
        """The value of this EUI address as a packed binary string."""
        return self._module.int_to_packed(self._value)

    @property
    def words(self):
        """A list of unsigned integer octets found in this EUI address."""
        return self._module.int_to_words(self._value)

    @property
    def bin(self):
        """
        The value of this EUI adddress in standard Python binary
        representational form (0bxxx). A back port of the format provided by
        the builtin bin() function found in Python 2.6.x and higher.
        """
        return self._module.int_to_bin(self._value)

    def eui64(self):
        """
        - If this object represents an EUI-48 it is converted to EUI-64 \
            as per the standard.
        - If this object is already an EUI-64, a new, numerically \
            equivalent object is returned instead.

        :return: The value of this EUI object as a new 64-bit EUI object.
        """
        if self.version == 48:
            # Convert 11:22:33:44:55:66 into 11:22:33:FF:FE:44:55:66.
            first_three = self._value >> 24
            last_three = self._value & 0xffffff
            new_value = (first_three << 40) | 0xfffe000000 | last_three
        else:
            # is already a EUI64
            new_value = self._value
        return self.__class__(new_value, version=64)

    def modified_eui64(self):
        """
        - create a new EUI object with a modified EUI-64 as described in RFC 4291 section 2.5.1

        :return: a new and modified 64-bit EUI object.
        """
        # Modified EUI-64 format interface identifiers are formed by inverting
        # the "u" bit (universal/local bit in IEEE EUI-64 terminology) when
        # forming the interface identifier from IEEE EUI-64 identifiers.  In
        # the resulting Modified EUI-64 format, the "u" bit is set to one (1)
        # to indicate universal scope, and it is set to zero (0) to indicate
        # local scope.
        eui64 = self.eui64()
        eui64._value ^= 0x00000000000000000200000000000000
        return eui64

    def ipv6(self, prefix):
        """
        .. note:: This poses security risks in certain scenarios. \
            Please read RFC 4941 for details. Reference: RFCs 4291 and 4941.

        :param prefix: ipv6 prefix

        :return: new IPv6 `IPAddress` object based on this `EUI` \
            using the technique described in RFC 4291.
        """
        int_val = int(prefix) + int(self.modified_eui64())
        return IPAddress(int_val, version=6)

    def ipv6_link_local(self):
        """
        .. note:: This poses security risks in certain scenarios. \
            Please read RFC 4941 for details. Reference: RFCs 4291 and 4941.

        :return: new link local IPv6 `IPAddress` object based on this `EUI` \
            using the technique described in RFC 4291.
        """
        return self.ipv6(0xfe800000000000000000000000000000)

    @property
    def info(self):
        """
        A record dict containing IEEE registration details for this EUI
        (MAC-48) if available, None otherwise.
        """
        data = {'OUI': self.oui.registration()}
        if self.is_iab():
            data['IAB'] = self.iab.registration()

        return DictDotLookup(data)

    def format(self, dialect=None):
        """
        Format the EUI into the representational format according to the given
        dialect

        :param dialect: the mac_* dialect defining the formatting of EUI-48 \
            (MAC) addresses.

        :return: EUI in representational format according to the given dialect
        """
        validated_dialect = self._validate_dialect(dialect)
        return self._module.int_to_str(self._value, validated_dialect)

    def __str__(self):
        """:return: EUI in representational format"""
        return self._module.int_to_str(self._value, self._dialect)

    def __repr__(self):
        """:return: executable Python string to recreate equivalent object."""
        return "EUI('%s')" % self


class EUIRange:
    """
    An arbitrary EUI address range.

    This is formed from a lower bound EUI address, and an upper bound EUI address.
    The lower bound must be numerically smaller than the upper bound.
    """
    __slots__ = ('_start', '_end', '_module')
    # Ranged EUI objects always represent a sequence of at least one EUI address and are therefore
    # always True in the boolean context.
    __bool__ = True

    def __init__(self, start: Union[EUI, Any], end: Union[EUI, Any]):
        """Constructor for the EUIRange object. Requires a start and end range that will be
        represented within the object.

        Args:
            start (Union[EUI, Any]): The lower boundary of the range.
            end (Union[EUI, Any]): The upper boundary of the range.

        Raises:
            AddrFormatError: Raises an error of the lower bound is greater than the upper bound.
        """
        if start > end:
            raise AddrFormatError(
                'The lower bound MAC address is greater than the upper bound.')
        self._start = EUI(start)
        self._module = self._start._module
        self._end = EUI(end, version=self._start._module.version)

    def __iter__(self) -> EUI:
        """An iterator providing access to all `EUI` objects within range represented by this ranged
        EUI object.

        Yields:
            Iterator[EUI]: The iterator function that yields EUIs.
        """
        start_eui = EUI(self.first, version=self._module.version)
        end_eui = EUI(self.last, version=self._module.version)
        return iter_EUIRange(start_eui, end_eui)

    def __getstate__(self) -> Tuple[int, int, int]:
        """The pickleable tuple representation of `EUIRange` object.

        Returns:
            Tuple[int, int, int]: The pickled state as a tuple of integers.
        """
        return self._start.value, self._end.value, self._module.version

    def __setstate__(self, state: Tuple[int, int, int]):
        """Unpickles a pickled `EUIRange` object from the tuple representation.

        Args:
            state (Tuple[int, int, int]): The pickled state as a tuple of integers.
        """
        start, end, version = state

        self._start = EUI(start, version=version)
        self._module = self._start._module
        self._end = EUI(end, version=version)

    def __contains__(self, other_mac_address: Union[EUI, 'EUIRange', int, str]) -> bool:
        """Checks whether an EUI exists within the current `EUIRange` object.

        Args:
            other_mac_address (Union[EUI, Any]): The EUI whose presence within the current range
            is being checked.

        Returns:
            bool: A boolean indicating the presence of `other_mac_address` in this EUIRange.
        """
        if isinstance(other_mac_address, EUI):
            # You can't compare EUI-48s with EUI-64s.
            if self._module.version != other_mac_address._module.version:
                return False
            if isinstance(other_mac_address, EUI):
                return (self._start._value <= other_mac_address._value # type: ignore
                        and self._end._value >= other_mac_address._value)
        elif isinstance(other_mac_address, EUIRange):
            return (self._start._value <= other_mac_address._start._value # type: ignore
                    and self._end._value >= other_mac_address._end._value)
        # Whatever it is, try to coalesce it to an EUI.
        elif isinstance(other_mac_address, (int, str)):
            return EUI(other_mac_address) in self

        return False

    def __len__(self) -> int:
        """The number of EUI addresses in this ranged EUI object.

        Returns:
            int: The number of EUI addresses in this ranged EUI object.
        """
        return self.size
    
    @overload
    def __getitem__(self, index: int) -> EUI: ...

    @overload
    def __getitem__(self, index: slice) -> Iterator[EUI]: ...

    def __getitem__(self, index: Union[int,
                                       slice]) -> Union[EUI, Iterator[EUI]]:
        """The MAC address(es) in this `EUIRange` object referenced by an index or slice.

        Args:
            index (Union[int, slice]): The index or slice over the `EUIRange`.

        Raises:
            IndexError: Raises index errors if the entered index or slice is beyond the range.

        Returns:
            Union[EUI, Iterator[EUI]]: The MAC address(es) in this `EUIRange` object referenced by
            index or slice. As slicing can produce large sequences of objects an iterator is
            returned instead of the more usual `list`.
        """
        item = None

        if isinstance(index, slice):
            (start, stop, step) = index.indices(self.size)
            if (start + step < 0) or (step > stop):
                #   step value exceeds start and stop boundaries.
                item = iter([EUI(self.first, self._module.version)])
            else:
                start_eui = EUI(self.first + start,
                                version=self._module.version)
                end_eui = EUI(self.first + stop - step,
                              version=self._module.version)
                item = iter_EUIRange(start_eui, end_eui, step)
        else:
            if (-self.size) <= index < 0:
                #   negative index.
                item = EUI(self.last + index + 1,
                            version=self._module.version)
            elif 0 <= index <= (self.size - 1):
                #   Positive index or zero index.
                item = EUI(self.first + index,
                            version=self._module.version)
            else:
                raise IndexError('Index out range for address range size!')

        return item

    def __hash__(self) -> int:
        """A hash value uniquely indentifying this `EUIRange` object.

        Returns:
            int: The hash value.
        """
        return hash(self.key())

    def __eq__(self, other: object) -> bool:
        """Equality magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is equivalent to `other`, `False` otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.key() == other.key()

    def __ne__(self, other: object) -> bool:
        """Non-equality magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is not equivalent to `other`, `False` otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.key() != other.key()

    def __lt__(self, other: 'EUIRange') -> bool:
        """Less-than magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is less than `other`, `False` otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.sort_key() < other.sort_key()

    def __le__(self, other: 'EUIRange') -> bool:
        """Less-than or equal-to magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is less than or equal to `other`, `False`
            otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.sort_key() <= other.sort_key()


    def __gt__(self, other: 'EUIRange') -> bool:
        """Greater-than magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is greater than `other`, `False` otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.sort_key() > other.sort_key()

    def __ge__(self, other: 'EUIRange') -> bool:
        """Greater-than or equal-to magic method for comparing `EUIRange` objects.

        Args:
            other (EUIRange): An `EUIRange` object.

        Returns:
            bool: `True` if this `EUIRange` object is greater than or equal to `other`, `False`
            otherwise.
        """
        if not isinstance(other, EUIRange):
            return NotImplemented
        return self.sort_key() >= other.sort_key()

    @property
    def size(self) -> int:
        """The total number of EUI addresses within this ranged EUI object.

        Returns:
            int: Integer for the size of the `EUIRange` object.
        """
        return int(self.last - self.first + 1)

    @property
    def first(self) -> int:
        """The integer value of first EUI address in this `EUIRange` object.

        Returns:
            int: Integer for the first `EUI` object in this range.
        """
        return int(self._start)

    @property
    def last(self) -> int:
        """The integer value of last EUI address in this `EUIRange` object.

        Returns:
            int: Integer for the last `EUI` object in this range.
        """
        return int(self._end)

    def key(self) -> Tuple[int, EUI, EUI]:
        """A method that returns a key tuple used to uniquely identify this `EUIRange`.

        Returns:
            Tuple[int, EUI, EUI]: The key tuple used to uniquely identify this `EUIRange`.
        """
        return self._module.version, self.first, self.last

    def sort_key(self) -> Tuple[int, int, int]:
        """A method that returns a key tuple used to compare and sort this `EUIRange`.

        Returns:
            Tuple[int, EUI, EUI]: The key tuple used to compare and sort identify this `EUIRange`.
        """
        skey = self._module.width - self.size.bit_length()
        return self._module.version, self._start._value, skey

    def __str__(self) -> str:
        """A string magic method to return a string representation of the current `EUIRange`.

        Returns:
            str: The formatted range string.
        """
        return f"{self._start}<->{self._end}"

    def __repr__(self) -> str:
        """The object representation magic method to return a detailed string rebresentation of
        the current `EUIRange` object.

        Returns:
            str: Python statement to create an equivalent object.
        """
        return self.__class__.__name__


class EUIPrefix:
    """
    An object representing a prefix for an EUI 48 MAC address. This is internally represented
    as a string. Holds objects such as:
    - AA:AA:AA:A
    - BB:BB:BB:BA
    - 00:11:22:33:4A
    """
    __slots__ = ('_value', '_separator')

    def __init__(self, addr: str):
        """Constructs the object.

        Args:
            addr (str): A prefix defined as a string.

        Raises:
            AddrFormatError: Raises an error if an incorrectly formatted prefix is passed.
        """
        ### Parse string
        # Get every third character in the address, except the last one.
        # These characters should all be the separator.
        separators = addr[2:-1:3]

        # Get the remaining part of the string.
        nibble_list = list(addr)
        del nibble_list[2:-1:3]
        addr_stripped = ''.join(nibble_list)

        ### Validate input.
        # Check every separator is valid, consistently used, and the remaining string is hex.
        is_valid = separators[0] in ':-' and \
            all(c == separators[0] for c in separators) and \
            all(c in hexdigits for c in addr_stripped) and \
            len(addr_stripped) <= 12
        # Optionally, add a check for specific prefix lengths.

        if not is_valid:
            raise AddrFormatError(f'Invalid EUI prefix: {addr}')

        ### Populate slots.
        self._value = addr_stripped.upper()
        self._separator = separators[0] if separators else '' # Use '' if too short for separators.


    def __getstate__(self) -> Tuple[str, str]:
        """The pickleable tuple representation of `EUIPrefix` object.

        Returns:
            Tuple[str, int]: The pickled state of the EUIPrefix object.
        """
        return self._value, self._separator

    def __setstate__(self, state: Tuple[str, str]):
        """Unpickles a pickled EUIPrefix object from the tuple representation.

        Args:
            state (Tuple[str, int]): The pickled values of the EUIPrefix object.
        """
        self._value, self._separator = state

    def __iter__(self) -> Union[Iterator[EUI], Any]:
        """An iterator providing access to all `EUI` objects within range represented by this
        ranged EUI object.

        Yields:
            Iterator[EUI]: The iterator containing the EUI objects between the first and last EUI
            within the range.
        """
        for eui in EUIRange(EUI(self.first), EUI(self.last)):
            yield eui

    @property
    def size(self) -> int:
        """The total number of EUI addresses within this ranged EUI object.

        Returns:
            int: The number of addresses as a subset of the prefix.
        """
        return int(self.last - self.first + 1)

    def __len__(self) -> int:
        """The magic method returning the total number of EUI addresses within this ranged EUI
        object.

        Returns:
            int: The number of addresses as a subset of the prefix.
        """
        return self.size
    
    @overload
    def __getitem__(self, index: int) -> EUI: ...

    @overload
    def __getitem__(self, index: slice) -> Iterator[EUI]: ...

    def __getitem__(self, index: Union[int,
                                       slice]) -> Union[EUI, Iterator[EUI]]:
        """The MAC address(es) in this `EUIPrefix` object referenced by an index or slice.

        Args:
            index (Union[int, slice]): The index or slice over the `EUIPrefix`.

        Raises:
            IndexError: Raises index errors if the entered index or slice is beyond the range.

        Returns:
            Union[EUI, Iterator[EUI]]: The MAC address(es) existing as a subset of this `EUIPrefix`
            object referenced by index or slice. As slicing can produce large sequences of objects
            an iterator is returned instead of the more usual `list`.
        """
        return EUIRange(self.first, self.last)[index]

    @property
    def prefixlen(self) -> int:
        """The number of bits in the EUI prefix. For example, AA:AA:AA:A = 28.

        Returns:
            int: The number of bits in the EUI prefix.
        """
        return len(self._value) * 4

    @property
    def eui(self) -> EUI:
        """The EUI address of this prefix, right-padded with 0s.

        Returns:
            EUI: The EUI address of this prefix, right-padded with 0s.
        """
        eui_pad = '000000000000'
        eui = f'{self._value}{eui_pad[len(self._value):]}'
        return EUI(eui)

    @property
    def broadcast(self) -> EUI:
        """The broadcast address of this `EUIPrefix` object. For MAC addresses, this is always the
        same.

        Returns:
            EUI: The EUI object of the broadcast address.
        """
        return EUI('FF:FF:FF:FF:FF:FF')

    @property
    def first(self) -> int:
        """The EUI address of the first EUI found within this prefix's range.

        Returns:
            int: The first EUI address within this prefix as an integer.
        """
        return int(self.eui)

    @property
    def last(self) -> int:
        """The EUI address of the last EUI found within this prefix's range.

        Returns:
            int: The last EUI address within this prefix as an integer.
        """
        eui_pad = 'FFFFFFFFFFFF'
        eui = f'{self._value}{eui_pad[len(self._value):]}'
        return int(EUI(eui))

    def __contains__(self, other_mac_address: Union[EUI, EUIRange, Any]):
        """Checks whether an EUI exists within the current `EUIPrefix` object.

        Args:
            other_mac_address (Union[EUI, EUIRange, Any]): The EUI or EUIRange whose presence
            within the current prefix space is being checked.

        Returns:
            bool: A boolean indicating the presence of `other_mac_address` in this EUIRange.
        """
        if isinstance(other_mac_address, EUIRange):
            return self.first <= other_mac_address.first \
                and other_mac_address.last <= self.last
        elif isinstance(other_mac_address, EUI):
            return self.first <= other_mac_address <= self.last
        else:
            # Whatever it is, try to interpret it as EUIPrefix.
            return EUI(other_mac_address) in self

    def key(self) -> Tuple[int, int]:
        """A key to allow unique identification of this prefix.

        Returns:
            Tuple[int, int]: A tuple containing the first value in the prefix and the last value.
        """
        return self.first, self.last

    def sort_key(self) -> Tuple[int, int]:
        """A key to allow sorting identification of this prefix.

        Returns:
            Tuple[int, int]: A tuple containing the first value in the prefix and the length of the
            prefix.
        """
        return self.first, self.prefixlen

    def __str__(self) -> str:
        """The magic method to return a string for the EUIPrefix class.

        Returns:
            str: The string representation of this MAC Prefix.
        """
        output_string = ':'.join(self._value[i:i+2] for i in range(0, len(self._value), 2))
        return f"{output_string}"

    def __repr__(self) -> str:
        """The magic method to create an equivalent object.

        Returns:
            _type_: The string statement to create an equivalent object.
        """
        return f"{self.__class__.__name__}('{self}')"
