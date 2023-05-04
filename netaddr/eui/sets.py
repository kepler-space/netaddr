from collections.abc import Iterable
from random import sample
from typing import Any, Iterator, List, Optional, Set, Tuple, Union

from netaddr import EUI
from netaddr.eui import EUIRange


class EUISet:
    """Represents an unordered collection (set) of unique EUI addresses."""
    __slots__ = ('_euis', '__weakref__')

    def __init__(self, eui_collection: Optional[Iterable[EUI]] = None):
        """The constructor.

        Args:
            iterable (Optional[Union[Set[EUI], Iterable[EUI, str]]], optional): An iterable
            containing EUI addresses.
            Defaults to None.
        """
        self._euis: Set[EUI] = set(eui_collection) if eui_collection is not None else set()

    def __getstate__(self) -> Tuple[Union[EUI, Any], ...]:
        """The pickleable tuple representation of `EUISet` object.

        Returns:
            Tuple[EUI]: Pickled state of an `EUISet` object.
        """
        return tuple([eui for eui in self._euis])

    def __setstate__(self, state: Tuple[EUI]):
        """Unpickles a pickled `EUISet` object from the tuple representation.

        Args:
            state (Tuple[EUI]): The pickled state of the EUI set.
        """
        self._euis = set([eui for eui in state])

    def __hash__(self):
        """Raises `TypeError` if this method is called. `EUISet` objects cannot be used as
        dictionary keys or as members of other sets.

        Raises:
            TypeError: `EUISet` objects are are not hashable.
        """
        raise TypeError('EUI sets are unhashable!')

    def __contains__(self, eui) -> bool:
        return EUI(eui) in self._euis

    def __bool__(self) -> bool:
        """Return True if the EUISet contains at least one EUI, else False.

        Returns:
            bool: Whether the EUISet contains at least one EUI.
        """
        return bool(self._euis)

    def __iter__(self) -> Iterator[EUI]:
        """The iterator magic method for the `EUISet` object. Will iterate over sorted collection of
        the `EUI` objects in this `EUISet`.

        Returns:
            Iterator[EUI]: An iterator over the EUI addresses within this EUI set.
        """
        return iter(sorted(self._euis))
    
    def random_sample(self, sample_size: int) -> List[EUI]:
        """Returns a random sample of EUIs from the current set.

        Args:
            sample_size (int): The size of the random sample of EUIs to be taken.

        Raises:
            ValueError: Raises an error if a sample size is larger than the population.

        Returns:
            List[EUI]: A list of randomly selected EUIs from the current `EUISet`.
        """
        return sample(list(self), sample_size)

    def add(self, addr: Union[EUI, EUIRange, Any]):
        """Adds an EUI address or EUIRange to this EUI set. Has no effect if it is already present.
        Will try to implicitly convert any object into an EUI object if it isn't one.

        Args:
            addr (Union[EUI, EUIRange, Any]): Either a singular EUI object or an EUIRange.
        """
        if isinstance(addr, EUIRange):
            for eui in addr:
                self._euis.add(EUI(eui))
        elif isinstance(addr, EUI):
            self._euis.add(addr)
        else:
            self._euis.add(EUI(addr))

    def remove(self, addr: Union[EUI, EUIRange]):
        """Removes an EUI address or EUIRange from this EUI set. Does nothing if it is not already
        a member.

        Args:
            addr (Union[EUI, EUIRange]): Either a singular EUI object or an EUIRange.
        """
        # TODO: We can probably optimise for the range case for lower/upper bounds outside of set.
        if isinstance(addr, EUIRange):
            for eui in addr:
                self._euis.discard(eui)
        else:
            self._euis.discard(EUI(addr))

    def pop(self) -> EUI:
        """
        Removes and returns an arbitrary EUI address from this EUI set.

        Returns:
            EUI: An EUI object.
        """
        return self._euis.pop()

    def isdisjoint(self, other: 'EUISet') -> bool:
        """Returns a boolean if the current set is disjoint with another `EUISet` object.

        Args:
            other (EUISet): An EUI set.

        Returns:
            bool: `True` if this EUI set has no elements in common with other. Intersection must
            be an empty set.
        """
        result = self.intersection(other)
        return not result

    def copy(self) -> 'EUISet':
        """Copies the current `EUISet`.

        Returns:
            EUISet: A shallow copy of this EUI set.
        """
        obj_copy = self.__class__()
        obj_copy._euis.update(self._euis)
        return obj_copy

    def update(self, iterable: Iterable[EUI]) -> None:
        """Update the contents of this EUI set with the union of itself and another EUI set.

        Args:
            iterable (Union[EUISet, EUIRange, Iterable[EUI]]): An iterable object containing EUIs.

        Raises:
            TypeError: Raises an error if an Iterable object isn't supplied.
        """
        for eui in iterable:
            self.add(eui)

    def clear(self):
        """Remove all EUI addresses from this EUI set."""
        self._euis = set()

    def __eq__(self, other: object) -> bool:
        """Checks for equality between this EUISet and another one.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `True` if this EUI set is equivalent to the `other` EUI set, `False` otherwise.
        """
        if not isinstance(other, EUISet):
            return NotImplemented
        return self._euis == other._euis

    def __ne__(self, other: object) -> bool:
        """Checks for nonequality between this EUISet and another one.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `False` if this EUI set is equivalent to the `other` EUI set, `True` otherwise.
        """
        if not isinstance(other, EUISet):
            return NotImplemented
        return not self  == other 

    def __lt__(self, other: 'EUISet') -> bool:
        """A magic method that checks whether this EUI set is less than another EUI set.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `True` if this EUI set is less than to the `other` EUI set, `False` otherwise.
        """
        if not isinstance(other, EUISet):
            return NotImplemented

        return self.size < other.size and self.is_subset(other)

    def is_subset(self, other: 'EUISet') -> bool:
        """Checks whether the current EUISet is a subset of the `other` EUISet.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `True` if every EUI address in this EUI set is found within `other`.
        """
        for eui in self._euis:
            if eui not in other:
                return False
        return True

    __le__ = is_subset

    def __gt__(self, other: 'EUISet') -> bool:
        """A magic method that checks whether this EUI set is greater than another EUI set.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `True` if this EUI set is greater than to the `other` EUI set, `False` otherwise.
        """
        return other < self

    def is_superset(self, other: 'EUISet') -> bool:
        """Checks whether the current EUISet is a superset of the `other` EUISet.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            bool: `True` if every EUI address in the `other` EUI set is found in this one.
        """
        return other.is_subset(self)

    __ge__ = is_superset

    def union(self, other: 'EUISet') -> 'EUISet':
        """Unions the current EUI set with another one.

        Args:
            other (EUISet): The other EUISet.

        Returns:
            EUISet: The union of this EUI set and another as a new EUI set.
        """
        eui_set = self.copy()
        eui_set.update(other)
        return eui_set

    __or__ = union

    def intersection(self, other: 'EUISet') -> 'EUISet':
        """The intersection of this EUI set and another EUI set.

        Args:
            other (EUISet): The other EUI set.

        Returns:
            EUISet: The `EUISet` object containing EUIs in both this EUI set and the `other` EUI
            set.
        """
        return EUISet(self._euis.intersection(other._euis))

    __and__ = intersection

    def symmetric_difference(self, other: 'EUISet') -> 'EUISet':
        """The symmetric difference of this EUI set and another EUI set.

        Args:
            other (EUISet): The other EUI set.

        Returns:
            EUISet: The `EUISet` object containing EUIs in either this EUI set or the `other` EUI
            set (all EUI addresses that are in exactly one of the sets).
        """
        return EUISet(self._euis.symmetric_difference(other._euis))

    __xor__ = symmetric_difference

    def difference(self, other: 'EUISet') -> 'EUISet':
        """The difference of this EUI set and another EUI set.

        Args:
            other (EUISet): The other EUI set.

        Returns:
            EUISet: The `EUISet` object containing the difference between this EUI set and the
            `other` EUI set (all EUI addresses that are in this EUI set but not found in the other).
        """
        return EUISet(self._euis.difference(other._euis))

    __sub__ = difference

    def __len__(self) -> int:
        """The cardinality of this EUI set (based on the number of individual EUI addresses).

        Returns:
            int: The number of EUIs in the EUISet.
        """
        return self.size

    @property
    def size(self) -> int:
        """
        The cardinality of this EUI set (based on the number of individual EUI
        addresses).

        Returns:
            int: The number of EUIs in the EUISet.
        """
        return len(self._euis)

    def __repr__(self) -> str:
        """Python statement to create an equivalent `EUISet` object.

        Returns:
            str: A string representing the EUI set.
        """
        return self.__class__.__name__

    __str__ = __repr__

    def is_contiguous(self) -> bool:
        """
        Returns True if the members of the set form a contiguous EUI address range (with no gaps),
        False otherwise.

        Returns:
            bool: `True` if the `EUISet` object is contiguous.
        """
        return (not self) or (int(max(self)) - int(min(self)) + 1 == len(self))

    def euirange(self) -> Union[EUIRange, None]:
        """Generates an EUIRange for this EUISet, if all its members form a single contiguous
        sequence.

        Raises:
            ValueError: Raises an error if the set is not contiguous.

        Returns:
            EUIRange: An `EUIRange` for all the EUIs in the EUISet.
        """
        if self.is_contiguous():
            if len(self) == 0:
                return None
            return EUIRange(min(self._euis), max(self._euis))
        else:
            raise ValueError("The EUISet is not contiguous.")
