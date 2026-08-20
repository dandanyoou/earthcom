from app.envelope import ok


def test_success_envelope_has_exactly_one_data_layer() -> None:
    assert ok({"value": 1}).model_dump() == {
        "ok": True,
        "data": {"value": 1},
        "meta": None,
    }
