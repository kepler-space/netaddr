def assert_iterables_equal(first_iterable, second_iterable):
    """Private helper function to assert the equality of two iterable objects."""
    for iter_eui, expected_eui \
    in zip(first_iterable, second_iterable, strict=True):
        assert iter_eui == expected_eui