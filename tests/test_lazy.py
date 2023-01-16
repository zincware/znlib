import pytest

from znlib import utils


def test_getitem():
    data = list(range(10))
    assert utils.lazy.getitem(data, 0) == 0
    assert utils.lazy.getitem(data, slice(3)) == [0, 1, 2]
    assert utils.lazy.getitem(data, [0, 2, 4]) == [0, 2, 4]
    assert utils.lazy.getitem(data, (0, 2, 4)) == [0, 2, 4]


def test_item_to_list():
    assert utils.lazy.item_to_list(1, None) == [1]
    assert utils.lazy.item_to_list(slice(4, 6), 10) == [4, 5]
    assert utils.lazy.item_to_list([1, 2, 3], None) == [1, 2, 3]
    assert utils.lazy.item_to_list((1, 2, 3), None) == (1, 2, 3)

    with pytest.raises(ValueError):
        utils.lazy.item_to_list("data", None)


def test_LazyList():
    range_lst = utils.lazy.LazyList(range(100))
    assert len(range_lst) == 100
    assert len(range_lst._data) == 0

    assert range_lst[0] == 0
    assert len(range_lst._data) == 1

    assert range_lst[:5] == [0, 1, 2, 3, 4]
    assert len(range_lst._data) == 5

    assert range_lst[[10, 12, 15]] == [10, 12, 15]
    assert len(range_lst._data) == 8

    assert range_lst.tolist() == list(range(100))
    with pytest.raises(ValueError):
        _ = range_lst[[4, 2, 1]]


def test_mixed_LazyList():
    range_list = utils.lazy.LazyList(range(100))
    filtered_list = utils.lazy.LazyList(range_list, indices=slice(50, 100))
    assert len(filtered_list) == 50
    assert len(filtered_list._data) == 0

    assert filtered_list[0] == 50
    assert len(filtered_list._data) == 1

    assert filtered_list[:5] == [50, 51, 52, 53, 54]
    assert len(filtered_list._data) == 5

    assert filtered_list[[10, 12, 15]] == [60, 62, 65]
    assert len(filtered_list._data) == 8

    assert range_list.tolist() == list(range(100))
    assert filtered_list.tolist() == list(range(50, 100))


def test_add_LazyList():
    list1 = utils.lazy.LazyList(range(10))
    list2 = utils.lazy.LazyList(range(10, 20))

    assert list1[0] == 0
    assert list2[0] == 10
    assert len(list1._data) == 1
    assert len(list2._data) == 1

    new_lst = list1 + list2

    assert len(new_lst) == 20
    assert len(new_lst._data) == 2

    assert new_lst[0] == 0
    assert new_lst[10] == 10
    assert new_lst[15] == 15
    assert len(new_lst._data) == 3

    assert new_lst._obj == [range(10), range(10, 20)]

    new_lst = utils.lazy.LazyList(range(10), indices=[1, 4, 7]) + utils.lazy.LazyList(
        range(10), indices=[3, 4, 6]
    )
    assert new_lst._indices == [[1, 4, 7], [3, 4, 6]]
    assert new_lst._obj == [range(10), range(10)]
    assert new_lst[[0, 1, 2]] == [1, 4, 7]
    assert new_lst[3] == 3

    assert new_lst.tolist() == [1, 4, 7, 3, 4, 6]

    # You can combine LazyList and list, but the order matters!
    assert list1 + list(range(10, 20)) == list(range(20))

    # inplace
    lista = utils.lazy.LazyList(range(10))
    lista += list(range(10, 20))
    assert lista == list(range(20))

    with pytest.raises(TypeError):
        _ = list(range(10, 20)) + list1

    new_lst = utils.lazy.LazyList() + list2
    assert new_lst.tolist() == list(range(10, 20))

    with pytest.raises(TypeError):
        _ = utils.lazy.LazyList() + 20


def test__get_list_from_index():
    indices = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]
    # assert utils.lazy._get_list_from_index(indices, [1, 3, 6, 9, 11]) == [0, 0, 1, 2, 2]
    assert utils.lazy._get_list_from_index(indices, [1, 3, 6, 9, 11]) == {
        0: [1, 3],
        1: [6],
        2: [9, 11],
    }

    indices = [[0, 10], [4, 5]]
    # assert utils.lazy._get_list_from_index(indices, [0, 1, 2]) == [0, 0, 1]
    assert utils.lazy._get_list_from_index(indices, [0, 1, 2]) == {0: [0, 1], 1: [2]}

    indices = [list(range(10)), list(range(10))]
    assert utils.lazy._get_list_from_index(indices, [15]) == {1: [15]}
