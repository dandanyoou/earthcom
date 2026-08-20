from app.platform.uuid7 import new_uuid7


def test_uuid7_is_monotonic_and_versioned() -> None:
    values = [new_uuid7() for _ in range(100)]

    assert all(value.version == 7 for value in values)
    assert all(value.variant == "specified in RFC 4122" for value in values)
    assert values == sorted(values)
    assert len(set(values)) == len(values)
