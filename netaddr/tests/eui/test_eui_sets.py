import random
import pytest
from netaddr import EUISet, EUIRange, EUIPrefix, iter_EUIRange
from netaddr import EUI

from .helpers.equality import assert_iterables_equal


# region: Fixtures

@pytest.fixture(scope="module")
def set_1():
    eui_list = [EUI(i) for i in range(0, 10)]
    return EUISet(eui_list)

@pytest.fixture(scope="module")
def set_2():
    eui_list = [EUI(i) for i in range(0, 1000, 100)]
    return EUISet(eui_list)

@pytest.fixture(scope="module")
def set_3():
    random_start = random.randint(1, 0x888888888888)
    random_end = random.randint(random_start + 0x222222222222, 0xffffffffffff)
    sample_values = random.sample(range(random_start, random_end), random.randint(5, 500))
    eui_list = [EUI(i) for i in sample_values]
    return EUISet(eui_list)

@pytest.fixture(scope="module")
def set_4():
    """Empty set."""
    eui_list = []
    return EUISet(eui_list)

# endregion: Fixtures


@pytest.mark.parametrize(
        "fixture_name", 
        [
            ("set_1"),
            ("set_2"),
            ("set_3"),
            ("set_4"),
        ])
def test_constructor(fixture_name, request):
    current_set = request.getfixturevalue(fixture_name)
    assert isinstance(current_set, EUISet)

@pytest.mark.parametrize(
        "fixture_name,contained_eui", 
        [
            ("set_1", EUI("00:00:00:00:00:00")),
            ("set_2", EUI("00:00:00:00:00:00")),
        ])
def test_contains_true(fixture_name, contained_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    assert contained_eui in current_set

@pytest.mark.parametrize(
        "fixture_name,contained_eui", 
        [
            ("set_3", EUI("00:00:00:00:00:00")),
            ("set_4", EUI("00:00:00:00:00:00")),
        ])
def test_contains_false(fixture_name, contained_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    assert contained_eui not in current_set

@pytest.mark.parametrize(
        "fixture_name,expected_output_generator", 
        [
            ("set_1", iter_EUIRange(EUI(0), EUI(9))),
            ("set_2", iter_EUIRange(EUI(0), EUI(999), 100)),
            ("set_4", iter_EUIRange(EUI(0), EUI(0))),
        ])
def test_iter(fixture_name, expected_output_generator, request):
    current_set = request.getfixturevalue(fixture_name)
    assert_iterables_equal(current_set, expected_output_generator)

@pytest.mark.parametrize(
        "fixture_name,eui_removed", 
        [
            ("set_1", EUI("00:00:00:00:00:00")),
            ("set_2", EUI("00:00:00:00:00:00")),
        ])
def test_random_sample(fixture_name, eui_removed, request):
    current_set: EUISet = request.getfixturevalue(fixture_name)
    assert len(current_set.random_sample(10)) == 10

    current_set_to_remove = current_set.copy()
    current_set_to_remove.remove(eui_removed)
    with pytest.raises(ValueError, match='Sample larger than population.'):
        current_set_to_remove.random_sample(10)

    samples = current_set_to_remove.random_sample(9)
    assert eui_removed not in samples

@pytest.mark.parametrize(
        "fixture_name,additional_eui", 
        [
            ("set_1", EUI("00:00:00:00:00:00")),
            ("set_2", EUI("00:00:00:00:00:00")),
        ])
def test_add_already_exists(fixture_name, additional_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    current_set_to_add = current_set.copy()
    current_set_to_add.add(additional_eui)
    assert current_set == current_set_to_add

@pytest.mark.parametrize(
        "fixture_name,additional_eui", 
        [
            ("set_1", EUI("00:00:00:00:00:0f")),
            ("set_2", EUI("00:00:00:00:00:0f")),
        ])
def test_add_new(fixture_name, additional_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    current_set_to_add = current_set.copy()
    current_set_to_add.add(additional_eui)
    assert current_set != current_set_to_add
    assert additional_eui not in current_set
    assert additional_eui in current_set_to_add

@pytest.mark.parametrize(
        "fixture_name,additional_eui", 
        [
            ("set_1", EUI("00:00:00:00:00:00")),
            ("set_2", EUI("00:00:00:00:00:00")),
        ])
def test_remove_exists(fixture_name, additional_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    current_set_to_remove = current_set.copy()
    current_set_to_remove.remove(additional_eui)
    assert current_set != current_set_to_remove
    assert additional_eui in current_set
    assert additional_eui not in current_set_to_remove

@pytest.mark.parametrize(
        "fixture_name,additional_eui", 
        [
            ("set_1", EUI("00:00:00:00:00:0f")),
            ("set_2", EUI("00:00:00:00:00:0f")),
            ("set_4", EUI("00:00:00:00:00:0f")),
        ])
def test_remove_not_exists(fixture_name, additional_eui, request):
    current_set = request.getfixturevalue(fixture_name)
    current_set_to_remove = current_set.copy()
    current_set_to_remove.remove(additional_eui)
    assert current_set == current_set_to_remove
    assert additional_eui not in current_set
    assert additional_eui not in current_set_to_remove

@pytest.mark.parametrize(
        "fixture_name", 
        [
            ("set_1"),
            ("set_2"),
            ("set_3"),
            ("set_4"),
        ])
def test_eq_true(fixture_name, request):
    current_set = request.getfixturevalue(fixture_name)
    current_set_copy = current_set.copy()
    assert current_set == current_set_copy

@pytest.mark.parametrize(
        "fixture_name,additional_euis", 
        [
            ("set_1", [EUI("00:00:00:00:00:00"), EUI("00:00:00:00:00:09")]),
            ("set_2", [EUI("00:00:00:00:00:00")]),
        ])
def test_is_subset(fixture_name, additional_euis, request):
    current_set = request.getfixturevalue(fixture_name)
    subset_set = EUISet(additional_euis)
    assert subset_set.is_subset(current_set)

@pytest.mark.parametrize(
        "fixture_name,additional_euis", 
        [
            ("set_1", [EUI("00:00:00:00:00:00"), EUI("00:00:00:00:00:09")]),
            ("set_2", [EUI("00:00:00:00:00:00")]),
        ])
def test_difference(fixture_name, additional_euis, request):
    current_set = request.getfixturevalue(fixture_name)
    subset_set = EUISet(additional_euis)
    assert subset_set.is_subset(current_set)

@pytest.mark.parametrize(
        "fixture_name,additional_euis", 
        [
            ("set_1", [EUI("00:00:00:00:00:00"), EUI("00:00:00:00:00:09")]),
            ("set_2", [EUI("00:00:00:00:00:00")]),
        ])
def test_is_superset(fixture_name, additional_euis, request):
    current_set = request.getfixturevalue(fixture_name)
    subset_set = EUISet(additional_euis)
    assert current_set.is_superset(subset_set)
