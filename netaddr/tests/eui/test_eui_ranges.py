import random
import pytest
from netaddr import EUISet, EUIRange, EUIPrefix, iter_EUIRange
from netaddr import EUI

from .helpers.equality import assert_iterables_equal


@pytest.fixture(scope="module")
def range_1():
    return EUIRange('00:00:00:00:00:00', '00:00:00:00:00:0F')

@pytest.fixture(scope="module")
def range_2():
    return EUIRange('00:00:00:00:A0:00', '00:00:00:00:A0:0F')

@pytest.fixture(scope="module")
def range_3():
    return EUIRange('00:00:00:FF:FF:00', '00:00:00:FF:FF:FF')

@pytest.fixture(scope="module")
def range_4():
    return EUIRange('00:00:00:00:00:00', 'FF:FF:FF:FF:FF:FF')


@pytest.mark.parametrize(
        "start_eui,end_eui,expected_output,step", 
        [
            (
                EUI('00:00:00:00:00:00'), 
                EUI('00:00:00:00:00:05'), 
                [
                    EUI('00:00:00:00:00:00'),
                    EUI('00:00:00:00:00:01'),
                    EUI('00:00:00:00:00:02'),
                    EUI('00:00:00:00:00:03'),
                    EUI('00:00:00:00:00:04'),
                    EUI('00:00:00:00:00:05')
                ],
                1
            ),
            (
                EUI('00:00:00:00:00:05'), 
                EUI('00:00:00:00:00:00'), 
                [
                    EUI('00:00:00:00:00:05'),
                    EUI('00:00:00:00:00:04'),
                    EUI('00:00:00:00:00:03'),
                    EUI('00:00:00:00:00:02'),
                    EUI('00:00:00:00:00:01'),
                    EUI('00:00:00:00:00:00')
                ],
                -1
            ),
            (
                EUI('00:00:00:A0:E3:00'), 
                EUI('00:00:00:A0:E3:05'), 
                [
                    EUI('00:00:00:A0:E3:00'),
                    EUI('00:00:00:A0:E3:01'),
                    EUI('00:00:00:A0:E3:02'),
                    EUI('00:00:00:A0:E3:03'),
                    EUI('00:00:00:A0:E3:04'),
                    EUI('00:00:00:A0:E3:05')
                ],
                1
            ),
            (
                EUI('00:00:00:A0:E3:05'), 
                EUI('00:00:00:A0:E3:00'), 
                [
                    EUI('00:00:00:A0:E3:05'),
                    EUI('00:00:00:A0:E3:04'),
                    EUI('00:00:00:A0:E3:03'),
                    EUI('00:00:00:A0:E3:02'),
                    EUI('00:00:00:A0:E3:01'),
                    EUI('00:00:00:A0:E3:00')
                ],
                -1
            ),
        ])
def test_iterEUIRange(start_eui, end_eui, expected_output, step):
    assert_iterables_equal(iter_EUIRange(start_eui, end_eui, step), expected_output)

def test_constructor():
    valid_constructors = [
        (0, 100000),
        (EUI(0), EUI(100000)),
        (0x001122AABBCC, 0xFFFFFFFFFFFF),
        ('AA:AA:AA:AA:AA:AA', 'BB:BB:BB:BB:BB:BB'),
        ]
    for valid_parameter in valid_constructors:
        assert isinstance(EUIRange(*valid_parameter), EUIRange)

    invalid_constructors = [
        (-1, 100000),
        ('GA:AA:AA:AA:AA:AA', 'BB:BB:BB:BB:BB:BB'),
    ]
    for invalid_parameter in invalid_constructors:
        with pytest.raises(Exception):
            EUIRange(*invalid_parameter)

@pytest.mark.parametrize(
        "fixture_name,expected_output_generator", 
        [
            (
                "range_1", 
                iter_EUIRange(EUI('00:00:00:00:00:00'), EUI('00:00:00:00:00:0F'))
            ),
            (
                "range_2", 
                iter_EUIRange(EUI('00:00:00:00:A0:00'), EUI('00:00:00:00:A0:0F'))
            ),
            (
                "range_3", 
                iter_EUIRange(EUI('00:00:00:FF:FF:00'), EUI('00:00:00:FF:FF:FF'))
            ),
        ])
def test_iter(fixture_name, expected_output_generator, request):
    current_range = request.getfixturevalue(fixture_name)
    assert_iterables_equal(current_range, expected_output_generator)

@pytest.mark.parametrize(
        "fixture_name,contained_object,truthiness", 
        [
            (
                "range_1", 
                EUI('00:00:00:00:00:07'),
                True
            ),
            (
                "range_1", 
                EUI('00:00:00:00:00:10'),
                False
            ),
            (
                "range_1", 
                EUIRange('00:00:00:00:00:00', '00:00:00:00:00:0F'),
                True
            ),
            (
                "range_1", 
                EUIRange('00:00:00:00:00:00', '00:00:00:00:00:10'),
                False
            ),
            (
                "range_2", 
                EUI('00:00:00:00:A0:07'),
                True
            ),
            (
                "range_2", 
                EUI('00:00:00:00:A0:10'),
                False
            ),
            (
                "range_2", 
                EUIRange('00:00:00:00:A0:00', '00:00:00:00:A0:05'),
                True
            ),
            (
                "range_2", 
                EUIRange('00:00:00:00:A0:00', '00:00:00:00:A0:10'),
                False
            ),
            (
                "range_3", 
                EUI('00:00:00:FF:FF:FF'),
                True
            ),
            (
                "range_3", 
                EUI('00:00:01:FF:FF:FF'),
                False
            ),
            (
                "range_3", 
                EUIRange('00:00:00:FF:FF:00', '00:00:00:FF:FF:FF'),
                True
            ),
            (
                "range_3", 
                EUIRange('00:00:00:00:00:00', '00:00:00:FF:FF:FF'),
                False
            ),
        ])
def test_contains(fixture_name, contained_object, truthiness, request):
    current_range = request.getfixturevalue(fixture_name)
    assert (contained_object in current_range) is truthiness

@pytest.mark.parametrize(
        "fixture_name,expected_length", 
        [
            (
                "range_1", 
                16
            ),
            (
                "range_2", 
                16
            ),
            (
                "range_3", 
                256
            ),
            (
                "range_4", 
                281474976710656
            ),
        ])
def test_len(fixture_name, expected_length, request):
    current_range = request.getfixturevalue(fixture_name)
    assert len(current_range) == expected_length

@pytest.mark.parametrize(
        "fixture_name,expected_output,index", 
        [
            ("range_1", EUI('00:00:00:00:00:00'), 0),
            ("range_2", EUI('00:00:00:00:A0:00'), 0),
            ("range_3", EUI('00:00:00:FF:FF:00'), 0),
            ("range_4", EUI('00:00:00:00:00:00'), 0),
            ("range_1", EUI('00:00:00:00:00:0F'), 15),
            ("range_2", EUI('00:00:00:00:A0:0F'), 15),
            ("range_3", EUI('00:00:00:FF:FF:FF'), 255),
            ("range_4", EUI('FF:FF:FF:FF:FF:FF'), 281474976710655),
        ])
def test_getitem_index(fixture_name, expected_output, index, request):
    current_range = request.getfixturevalue(fixture_name)
    assert current_range[index] == expected_output

@pytest.mark.parametrize(
        "fixture_name,comparison_fixture", 
        [
            ("range_1", "range_2"),
            ("range_2", "range_3"),
        ])
def test_equalities(fixture_name, comparison_fixture, request):
    current_range = request.getfixturevalue(fixture_name)
    comparison_range = request.getfixturevalue(comparison_fixture)
    assert current_range == current_range
    assert current_range != comparison_range
    assert current_range < comparison_range
    assert comparison_range > current_range

@pytest.mark.parametrize(
        "fixture_name,expected_size", 
        [
            (
                "range_1", 
                16
            ),
            (
                "range_2", 
                16
            ),
            (
                "range_3", 
                256
            ),
            (
                "range_4", 
                281474976710656
            ),
        ])
def test_size(fixture_name, expected_size, request):
    current_range = request.getfixturevalue(fixture_name)
    assert current_range.size == expected_size

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("range_1", EUI('00:00:00:00:00:00')),
            ("range_2", EUI('00:00:00:00:A0:00')),
            ("range_3", EUI('00:00:00:FF:FF:00')),
            ("range_4", EUI('00:00:00:00:00:00')),
        ])
def test_first(fixture_name, expected_output, request):
    current_range = request.getfixturevalue(fixture_name)
    assert current_range.first == expected_output

@pytest.mark.parametrize(
        "fixture_name,expected_output", 
        [
            ("range_1", EUI('00:00:00:00:00:0F')),
            ("range_2", EUI('00:00:00:00:A0:0F')),
            ("range_3", EUI('00:00:00:FF:FF:FF')),
            ("range_4", EUI('FF:FF:FF:FF:FF:FF')),
        ])
def test_last(fixture_name, expected_output, request):
    current_range = request.getfixturevalue(fixture_name)
    assert current_range.last == expected_output