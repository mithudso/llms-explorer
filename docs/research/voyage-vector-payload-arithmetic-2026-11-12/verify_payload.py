#!/usr/bin/env python3
"""Reproduce raw vector payload arithmetic with synthetic standard-library data."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def pack_bits_msb(values: list[int]) -> bytes:
    """Pack eight logical bits per byte, with the first bit most significant."""
    assert len(values) % 8 == 0
    assert all(type(value) is int and value in (0, 1) for value in values)
    return bytes(
        sum(values[start + offset] << (7 - offset) for offset in range(8))
        for start in range(0, len(values), 8)
    )


def unpack_bits_msb(payload: bytes) -> list[int]:
    return [(value >> offset) & 1 for value in payload for offset in range(7, -1, -1)]


def verify() -> dict:
    # '<' fixes byte order and uses standard sizes without native alignment padding.
    assert struct.calcsize('<f') == 4
    assert struct.calcsize('<b') == 1
    float_values = [index / 256 for index in range(2048)]
    int_values = [index % 256 - 128 for index in range(1024)]
    float_payload = struct.pack('<2048f', *float_values)
    int_payload = struct.pack('<1024b', *int_values)
    assert list(struct.unpack('<2048f', float_payload)) == float_values
    assert list(struct.unpack('<1024b', int_payload)) == int_values
    assert len(float_payload) == 2048 * 4 == 8192
    assert len(int_payload) == 1024 * 1 == 1024
    assert len(float_payload) % len(int_payload) == 0
    assert len(float_payload) // len(int_payload) == 8

    # The repeating synthetic pattern 01001101 must pack to byte 0x4d (77).
    pattern = [0, 1, 0, 0, 1, 1, 0, 1]
    packed = {}
    for dimensions in (1024, 512):
        logical_bits = pattern * (dimensions // 8)
        payload = pack_bits_msb(logical_bits)
        assert len(logical_bits) == dimensions
        assert payload == bytes([0x4d]) * (dimensions // 8)
        assert unpack_bits_msb(payload) == logical_bits
        assert len(payload) == dimensions // 8
        packed[dimensions] = payload
    assert len(packed[1024]) == 128
    assert len(packed[512]) == 64

    return {
        'schema': 'vector-payload-arithmetic/v1',
        'evidence_kind': 'firsthand synthetic serialization and arithmetic',
        'assumptions': {
            'float32_bits_per_coordinate': 32,
            'int8_bits_per_coordinate': 8,
            'bits_per_byte': 8,
            'struct_byte_order': 'little-endian',
            'struct_alignment_padding': False,
            'packed_bit_order': 'most-significant bit first',
        },
        'results': {
            'float32_2048_coordinates_bytes': len(float_payload),
            'int8_1024_coordinates_bytes': len(int_payload),
            'raw_payload_reduction_factor': len(float_payload) // len(int_payload),
            'binary_1024_logical_dimensions_bytes': len(packed[1024]),
            'binary_512_logical_dimensions_bytes': len(packed[512]),
        },
        'payload_sha256': {
            'float32_2048': hashlib.sha256(float_payload).hexdigest(),
            'int8_1024': hashlib.sha256(int_payload).hexdigest(),
            'binary_1024': hashlib.sha256(packed[1024]).hexdigest(),
            'binary_512': hashlib.sha256(packed[512]).hexdigest(),
        },
        'checks': {
            'standard_type_sizes': True,
            'float_and_int_round_trips': True,
            'packed_values_and_bit_round_trips': True,
            'exact_payload_lengths_and_ratio': True,
        },
        'limits': [
            'Synthetic values; no Voyage API request or embedding quality measurement.',
            'Raw coordinate payload only; excludes containers, headers, transport and indexes.',
            'No Atlas RAM, total storage, latency, rescoring or billing measurement.',
        ],
    }


def main() -> None:
    if not __debug__:
        raise SystemExit('Run without -O: this verification requires active assertions.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Also write the deterministic JSON result.')
    args = parser.parse_args()
    result = json.dumps(verify(), indent=2) + '\n'
    if args.output is not None:
        args.output.write_text(result, encoding='utf-8')
    print(result, end='')


if __name__ == '__main__':
    main()
