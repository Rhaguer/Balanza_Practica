from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from scripts import weight_bridge


class _SilentPort:
    in_waiting = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def reset_input_buffer(self):
        pass

    def read(self, _size):
        return b""


class _FakeSerialModule:
    SEVENBITS = 7
    EIGHTBITS = 8
    PARITY_NONE = "N"
    PARITY_EVEN = "E"
    PARITY_ODD = "O"
    STOPBITS_ONE = 1
    STOPBITS_TWO = 2

    @staticmethod
    def Serial(**_kwargs):
        return _SilentPort()


class WeightBridgeTests(SimpleTestCase):
    def test_extracts_weight_only_from_unit_tagged_frame(self):
        self.assertEqual(
            weight_bridge.extract_weight_kg("\x02S  0.245kgr\x03", Decimal("1000")),
            Decimal("0.245"),
        )

    def test_rejects_number_from_corrupted_serial_frame(self):
        self.assertIsNone(
            weight_bridge.extract_weight_kg("\x08HRo7)\x00", Decimal("1000"))
        )

    @patch.object(weight_bridge.time, "sleep", return_value=None)
    @patch.object(weight_bridge.time, "monotonic", side_effect=[0.0, 1.0, 5.0])
    def test_service_mode_abandons_silent_serial_configuration(self, _clock, _sleep):
        config = {
            "read_seconds": 4,
            "commands": ("",),
            "max_weight_kg": Decimal("1000"),
            "stable_samples": 3,
            "stable_tolerance_kg": Decimal("0.020"),
            "post_cooldown_seconds": 0.9,
            "read_pause_seconds": 0.0,
            "endpoint": "http://127.0.0.1:8000/api/update_weight/",
            "token": "test",
        }

        result = weight_bridge.probe_or_watch_port(
            _FakeSerialModule,
            "COM1",
            9600,
            "8N1",
            "default",
            config,
            once=False,
        )

        self.assertFalse(result)
