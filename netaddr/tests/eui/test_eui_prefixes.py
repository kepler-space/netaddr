import random
import pytest
from netaddr import EUISet, EUIRange, EUIPrefix, iter_EUIRange
from netaddr import EUI

from .helpers.equality import assert_iterables_equal


@pytest.fixture(scope="module")
def prefix_1():
    return EUIPrefix('00:00:00:00:00:0')

@pytest.fixture(scope="module")
def prefix_2():
    return EUIPrefix('00:00:00:00:00')

@pytest.fixture(scope="module")
def prefix_3():
    return EUIPrefix('AA:AA:AA:AA:AA:0')

@pytest.fixture(scope="module")
def prefix_4():
    return EUIPrefix('AA:AA:AA:A')

@pytest.fixture(scope="module")
def prefix_5():
    return EUIPrefix('AA:AA:AA:AB:C')

@pytest.mark.parametrize(
        "test_input", 
        [
            ("GG:GG:GG:G"), 
            ("00:11:22:33:44:55:66")
        ])
def test_constructor_incorrect_format(test_input):
    with pytest.raises(Exception, match='Invalid EUI prefix'):
        EUIPrefix(test_input)

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", 16),
            ("prefix_2", 256),
            ("prefix_3", 16),
            ("prefix_4", 1048576),
            ("prefix_5", 4096),
        ])
def test_iter(fixture_name, expected_output, request):
    """This gets the length of the expected iterable for assertion."""
    current_prefix = request.getfixturevalue(fixture_name)
    assert sum(1 for _ in current_prefix) == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output,index", 
        [
            ("prefix_1", EUI('00:00:00:00:00:00'), 0),
            ("prefix_2", EUI('00:00:00:00:00:00'), 0),
            ("prefix_3", EUI('aa:aa:aa:aa:aa:00'), 0),
            ("prefix_4", EUI('aa:aa:aa:a0:00:00'), 0),
            ("prefix_5", EUI('aa:aa:aa:ab:c0:00'), 0),
            ("prefix_1", EUI('00:00:00:00:00:0f'), 15),
            ("prefix_2", EUI('00:00:00:00:00:ff'), 255),
            ("prefix_3", EUI('aa:aa:aa:aa:aa:0f'), 15),
            ("prefix_4", EUI('aa:aa:aa:af:ff:ff'), 1048575),
            ("prefix_5", EUI('aa:aa:aa:ab:cf:ff'), 4095),
        ])
def test_getitem_index(fixture_name, expected_output, index, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix[index] == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output_generator,slice", 
        [
            (
                "prefix_1", 
                iter_EUIRange(EUI('00:00:00:00:00:00'), EUI('00:00:00:00:00:0f')), 
                slice(0, 16)
            ),
            (
                "prefix_2", 
                iter_EUIRange(EUI('00:00:00:00:00:13'), EUI('00:00:00:00:00:23')), 
                slice(19, 36)
            ),
            (
                "prefix_3", 
                iter_EUIRange(EUI('aa:aa:aa:aa:aa:00'), EUI('aa:aa:aa:aa:aa:0f')), 
                slice(0, 32)
            ),
            (
                "prefix_4", 
                iter_EUIRange(EUI('aa:aa:aa:a0:00:00'), EUI('aa:aa:aa:a0:00:1f')), 
                slice(0, 32)
            ),
            (
                "prefix_5", 
                iter_EUIRange(EUI('aa:aa:aa:ab:cf:ff'), EUI('aa:aa:aa:ab:c0:01'), step=-1), 
                slice(4096, 0, -1)
            ),
        ])
def test_getitem_slice(fixture_name, expected_output_generator, slice, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert_iterables_equal(current_prefix[slice], expected_output_generator)

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", 44),
            ("prefix_2", 40),
            ("prefix_3", 44),
            ("prefix_4", 28),
            ("prefix_5", 36),
        ])
def test_prefixlen(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix.prefixlen == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", EUI('00:00:00:00:00:00')),
            ("prefix_2", EUI('00:00:00:00:00:00')),
            ("prefix_3", EUI('aa:aa:aa:aa:aa:00')),
            ("prefix_4", EUI('aa:aa:aa:a0:00:00')),
            ("prefix_5", EUI('aa:aa:aa:ab:c0:00')),
        ])
def test_eui(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix.eui == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", EUI('FF:FF:FF:FF:FF:FF')),
            ("prefix_2", EUI('FF:FF:FF:FF:FF:FF')),
            ("prefix_3", EUI('FF:FF:FF:FF:FF:FF')),
            ("prefix_4", EUI('FF:FF:FF:FF:FF:FF')),
            ("prefix_5", EUI('FF:FF:FF:FF:FF:FF')),
        ])
def test_broadcast(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix.broadcast == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", 0),
            ("prefix_2", 0),
            ("prefix_3", 187649984473600),
            ("prefix_4", 187649983774720),
            ("prefix_5", 187649984544768),
        ])
def test_first(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix.first == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", 15),
            ("prefix_2", 255),
            ("prefix_3", 187649984473615),
            ("prefix_4", 187649984823295),
            ("prefix_5", 187649984548863),
        ])
def test_last(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert current_prefix.last == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", EUI('00:00:00:00:00:00')),
            ("prefix_2", EUI('00:00:00:00:00:00')),
            ("prefix_3", EUI('aa:aa:aa:aa:aa:00')),
            ("prefix_4", EUI('aa:aa:aa:a0:00:00')),
            ("prefix_5", EUI('aa:aa:aa:ab:c0:00')),
            ("prefix_1", EUI('00:00:00:00:00:0a')),
            ("prefix_2", EUI('00:00:00:00:00:b0')),
            ("prefix_3", EUI('aa:aa:aa:aa:aa:0e')),
            ("prefix_4", EUI('aa:aa:aa:af:00:00')),
            ("prefix_5", EUI('aa:aa:aa:ab:c0:3e')),
        ])
def test_contains_true(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert expected_output in current_prefix

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", EUI('00:00:00:00:00:10')),
            ("prefix_2", EUI('00:00:00:0f:00:00')),
            ("prefix_3", EUI('aa:aa:aa:aa:ab:00')),
            ("prefix_4", EUI('aa:aa:aa:b0:00:00')),
            ("prefix_5", EUI('aa:aa:aa:ab:f0:00')),
            ("prefix_3", EUI('aa:aa:aa:aa:a9:00')),
            ("prefix_4", EUI('aa:aa:aa:99:00:00')),
            ("prefix_5", EUI('aa:aa:af:ab:c0:3E')),
        ])
def test_contains_false(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert expected_output not in current_prefix

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("prefix_1", '00:00:00:00:00:0'),
            ("prefix_2", '00:00:00:00:00'),
            ("prefix_3", 'AA:AA:AA:AA:AA:0'),
            ("prefix_4", 'AA:AA:AA:A'),
            ("prefix_5", 'AA:AA:AA:AB:C'),
        ])
def test_str(fixture_name, expected_output, request):
    current_prefix = request.getfixturevalue(fixture_name)
    assert str(current_prefix) == expected_output
