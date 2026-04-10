"""SMS UPS serial client.

Handles USB serial communication with the UPS device.
Protocol and constants extracted from smsUPS.py by dmslabs.
"""

from __future__ import annotations

import logging
import struct
import time
from typing import Any

import serial

_LOGGER = logging.getLogger(__name__)

# Q command: query all UPS status data (from smsUPS.py cmd['Q'])
_CMD_Q = bytes.fromhex("51ffffffff b30d".replace(" ", ""))

_BAUD_RATE = 2400
_BYTE_DELAY = 0.1  # 100 ms between bytes — required by the UPS protocol
_READ_BYTES = 32
_SERIAL_TIMEOUT = 10  # seconds

# Response layout for the Q command (18 bytes total):
#   [0]      0x3D  start marker
#   [1-2]    uint16 BE  lastInputVac  (raw / 10 = volts)
#   [3-4]    uint16 BE  inputVac      (raw / 10 = volts)
#   [5-6]    uint16 BE  outputVac     (raw / 10 = volts)
#   [7-8]    uint16 BE  outputPower   (raw / 10 = percent)
#   [9-10]   uint16 BE  outputHz      (raw / 10 = Hz)
#   [11-12]  uint16 BE  batteryLevel  (raw / 10 = percent)
#   [13-14]  uint16 BE  temperatureC  (raw / 10 = °C)
#   [15]     status bits
#   [16]     checksum
#   [17]     0x0D end marker
_RESPONSE_STRUCT = struct.Struct(">B7HBB")
_RESPONSE_START = 0x3D
_RESPONSE_END = 0x0D
_MIN_RESPONSE_LEN = 18  # Full response including end marker


class SmsUpsSerialClientError(Exception):
    """General SMS UPS serial error."""


class SmsUpsSerialClientCommunicationError(SmsUpsSerialClientError):
    """Communication error — port not accessible or invalid response."""


class SmsUpsSerialClient:
    """Client for reading UPS data over USB serial."""

    def __init__(self, port: str) -> None:
        """Initialise the client with the given serial port path."""
        self._port = port
        self._ser: serial.Serial | None = None

    def connect(self) -> None:
        """Open the serial connection. Blocking — run in executor."""
        try:
            self._ser = serial.Serial(
                self._port,
                baudrate=_BAUD_RATE,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=_SERIAL_TIMEOUT,
            )
        except serial.SerialException as exc:
            msg = f"Cannot open serial port {self._port}: {exc}"
            raise SmsUpsSerialClientCommunicationError(msg) from exc

    def disconnect(self) -> None:
        """Close the serial connection. Blocking — run in executor."""
        if self._ser and self._ser.is_open:
            self._ser.close()

    def get_data(self) -> dict[str, Any]:
        """
        Read and return all UPS sensor data. Blocking — run in executor.

        Auto-reconnects if the port is not open.
        Returns a dict with keys matching the noBreak structure from smsUPS.py.
        """
        if self._ser is None or not self._ser.is_open:
            self.connect()

        raw = self._send_command(_CMD_Q)
        return self._parse_response(raw)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _send_command(self, cmd_bytes: bytes) -> bytes:
        """
        Send a command byte-by-byte and read the response.

        Matches smsUPS.py send_command(): writes one byte at a time with
        a 100 ms delay between bytes, then reads up to 32 bytes.
        """
        try:
            _LOGGER.debug("Sending command to UPS: %s", cmd_bytes.hex())
            # Time command execution for debugging timeouts
            start_time = time.time()

            for byte in cmd_bytes:
                self._ser.write(bytes([byte]))
                time.sleep(_BYTE_DELAY)

            elapsed_time = time.time() - start_time
            response = self._ser.read(_READ_BYTES)

            _LOGGER.debug("Response received in %.3f seconds", elapsed_time)
            return response

        except serial.SerialException as exc:
            msg = f"Serial communication error: {exc}"
            raise SmsUpsSerialClientCommunicationError(msg) from exc

    def _parse_response(self, response: bytes) -> dict[str, Any]:
        """
        Parse the 18-byte Q command response into a sensor data dict.

        Equivalent to trataRetorno() + dadosNoBreak() in smsUPS.py,
        rewritten using struct for clarity.
        """
        # Validate response length and start/end markers
        # (matching Node-RED flow validation)
        if len(response) < _MIN_RESPONSE_LEN:
            msg = (
                f"Invalid UPS response: too short "
                f"(len={len(response)}, expected {_MIN_RESPONSE_LEN})"
            )
            raise SmsUpsSerialClientCommunicationError(msg)

        if response[0] != _RESPONSE_START:
            msg = (
                f"Invalid UPS response: bad start marker "
                f"(got 0x{response[0]:02x}, expected 0x{_RESPONSE_START:02x})"
            )
            raise SmsUpsSerialClientCommunicationError(msg)

        if response[17] != _RESPONSE_END:
            msg = (
                f"Invalid UPS response: bad end marker "
                f"(got 0x{response[17]:02x}, expected 0x{_RESPONSE_END:02x})"
            )
            raise SmsUpsSerialClientCommunicationError(msg)

        (
            _start,
            last_input_vac_raw,
            input_vac_raw,
            output_vac_raw,
            output_power_raw,
            output_hz_raw,
            battery_level_raw,
            temperature_raw,
            status,
            _checksum,
        ) = _RESPONSE_STRUCT.unpack_from(response)

        # Decode status bits
        on_battery = bool(status & 0x80)
        low_battery = bool(status & 0x40)
        bypass = bool(status & 0x20)
        boost = bool(status & 0x10)
        ups_ok = bool(status & 0x08)
        test_active = bool(status & 0x04)
        shutdown_active = bool(status & 0x02)
        beep_on = bool(status & 0x01)

        _LOGGER.debug(
            "UPS raw response: hex=%s | "
            "lastInputVac=%d outputVac=%d inputVac=%d outputPower=%d "
            "outputHz=%d batteryLevel=%d temperatureC=%d status=0x%02x "
            "(onBattery=%s lowBattery=%s bypass=%s boost=%s upsOk=%s "
            "testActive=%s shutdownActive=%s beepOn=%s) checksum=0x%02x",
            response.hex(),
            last_input_vac_raw,
            output_vac_raw,
            input_vac_raw,
            output_power_raw,
            output_hz_raw,
            battery_level_raw,
            temperature_raw,
            status,
            on_battery,
            low_battery,
            bypass,
            boost,
            ups_ok,
            test_active,
            shutdown_active,
            beep_on,
            _checksum,
        )

        return {
            "inputVac": input_vac_raw / 10,
            "lastInputVac": last_input_vac_raw / 10,
            "outputVac": output_vac_raw / 10,
            "outputPower": output_power_raw / 10,
            "outputHz": output_hz_raw / 10,
            "batteryLevel": battery_level_raw / 10,
            "temperatureC": temperature_raw / 10,
            # Status bits — bit 7 (MSB) → onBattery, bit 0 (LSB) → beepOn
            # Matches dadosNoBreak() bit ordering in smsUPS.py
            "onBattery": on_battery,
            "lowBattery": low_battery,
            "bypass": bypass,
            "boost": boost,
            "upsOk": ups_ok,
            "testActive": test_active,
            "shutdownActive": shutdown_active,
            "beepOn": beep_on,
        }
