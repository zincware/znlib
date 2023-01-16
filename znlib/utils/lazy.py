import collections.abc
import copy
import typing


def item_to_list(item, obj_length) -> typing.List[int]:
    """convert the item of slice/int to a list of ints"""
    if isinstance(item, int):
        return [item]
    elif isinstance(item, slice):
        return list(range(obj_length))[item]
    elif isinstance(item, (list, tuple)):
        return item
    else:
        raise ValueError(f"Unsupported item type: {type(item)}")


def getitem(obj, item, *, obj_length=None):
    """Load from list

    Supports:
    - single indexing obj[5]
    - slices obj[3:5]
    - advanced indexing obj[[3, 4, 5]]

    Returns
    --------
    list|any from obj
    """
    if isinstance(item, int):
        return obj[item]

    if obj_length is None:
        obj_length = len(obj)
    item = item_to_list(item, obj_length)
    # Use advanced indexing if LazyList
    return obj[item] if isinstance(obj, LazyList) else [obj[x] for x in item]


def _get_list_from_index(indices, items) -> dict:
    """Given a list of indices sort the given items into these lists

    The sorting is done by order and length of the respective list.
    The content of the lists do not matter.


    Examples
    --------
    >>> indices = [[0, 10], [4, 5]]
    >>> _get_list_from_index(indices, [0, 1, 2]) == {0: [0, 1], 1:[2]}

    Parameters
    ----------
    indices: list[list[int]]
    items: list[int]

    Returns
    -------
    dict: {idx: []} where idx gives the index of the list 'indices' which e.g. is over
                the number of objects in LazyList._obj. The values are the given 'items'
                sorted into the respective index list.

    """
    max_vals = [len(indices[0])]
    max_vals.extend(len(index) + max_vals[-1] for index in indices[1:])
    vals_to_index = {val: idx for idx, val in enumerate(max_vals)}

    index_dict = {}
    for item in items:
        key = min(x for x in vals_to_index if x > item)
        try:
            index_dict[vals_to_index[key]].append(item)
        except KeyError:
            index_dict[vals_to_index[key]] = [item]

    return index_dict


class LazyList(collections.abc.Sequence):
    def __init__(self, obj=None, indices=None):
        """

        Parameters
        ----------
        obj: any object that implements getitem
        indices: list|slice|int|None
            Given the object 'obj' these are the indices internally selected from
            'obj'. E.g. 'obj = range(10)' and indices = [1, 4, 7] results in
            LazyList[:] == [1, 4, 7]. If None no internal selection is performed.

        Attributes
        ----------
        _obj: list
            The list of objects to gather the data from. These objects should implement
            some lazy method that is called when using self._obj[0][index]
        _data: dict
            A dictionary of {idx: data} where the index is the respective index of
            self[index] == data
        _indices: list[list[int]]
            Only these indices are selected _obj.

        """
        if obj is None:
            obj = []
        self._obj = [obj]
        self._data = {}
        self._indices: typing.List[list]
        if indices is None:
            self._indices = [range(len(obj))]
        elif isinstance(indices, slice):
            self._indices = [range(len(obj))[indices]]
        elif isinstance(indices, (list, tuple)):
            self._indices = [indices]
        else:
            raise ValueError(f"Indices of type '{type(indices)}' not supported")

    def _update(self, items):
        """Update the internal self._data

        Parameters
        ----------
        items: indices that are requested but some or all
                are not available from self._data

        """
        items = item_to_list(items, len(self))
        items = [x for x in items if x not in self._data]  # filter already loaded data
        list_indices = _get_list_from_index(self._indices, items)

        for index, items in list_indices.items():
            prior_index_length = sum(len(x) for x in self._indices[:index])
            index_items = [x - prior_index_length for x in items]
            # subtracting the length of all prior index lists.
            #  thereby, starting again at "zero"
            per_index_items = [self._indices[index][x] for x in index_items]
            # the indices for the current "index"

            try:
                data = self._obj[index][per_index_items]
            except TypeError:
                # does not support advanced slicing
                data = [self._obj[index][x] for x in per_index_items]

            for key, val in zip(items, data):
                self._data[key] = val

    def __getitem__(self, item):
        """Return Items

        Parameters
        ----------
        item: int, list, slice

        Returns
        -------
        Updated self._data and returns the requested items

        """
        if isinstance(item, (list, tuple)) and sorted(item) != item:
            raise ValueError("For performance reasons, the indices must be sorted")
        try:
            return getitem(self._data, item, obj_length=len(self))
        except KeyError:
            self._update(item)
        return self[item]

    def __iter__(self):
        """Enable iterating over the sequence. This will load all data at once"""
        self._update(slice(len(self)))
        for idx in range(len(self)):
            yield self[idx]

    def __len__(self):
        return sum(len(x) for x in self._indices)

    def __add__(self, other):
        """Allow the combination of two LazyList|list

        Parameters
        ----------
        other: LazyList|list
            If other is list, it will return a (non-lazy) list.
            If other is LazyList, it will return a LazyList

        Raises
        ------
        TypeError: if other is neither LazyList nor list
        """
        if isinstance(other, list):
            return self.tolist() + other

        if not isinstance(other, LazyList):
            raise TypeError(
                f"can only concatenate LazyList (not '{type(other)}') to LazyList"
            )
        result = copy.deepcopy(self)
        result._indices.extend(other._indices)
        result._data.update({key + len(other): val for key, val in other._data.items()})
        result._obj.extend(other._obj)

        return result

    def __repr__(self):
        return f"{self.__class__.__name__}({self._obj})"

    def tolist(self) -> list:
        """Convert LazyList to a (non-lazy) list"""
        return list(self)
