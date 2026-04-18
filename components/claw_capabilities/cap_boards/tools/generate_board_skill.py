#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PIN_KEY_SUFFIXES = (
    '_io_num',
    '_gpio_num',
    '_io',
)
PIN_KEY_NAMES = {
    'gpio_num',
    'sda',
    'scl',
    'mosi',
    'miso',
    'sclk',
    'clk',
    'dout',
    'din',
    'cs',
    'dc',
    'reset',
    'vsync',
    'hsync',
    'de',
    'pclk',
    'xclk',
    'pwdn',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate current board skill markdown.')
    parser.add_argument('--gen-bmgr-dir', required=True, help='Path to application/basic_demo/components/gen_bmgr_codes')
    parser.add_argument('--output-md', required=True, help='Generated markdown output path')
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open('r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(f'Missing YAML file: {path}') from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f'Invalid YAML file {path}: {exc}') from exc
    if not isinstance(data, dict):
        fail(f'Expected a YAML mapping in {path}')
    return data


def parse_board_path(gen_bmgr_dir: Path) -> Path:
    cmake_path = gen_bmgr_dir / 'CMakeLists.txt'
    text = cmake_path.read_text(encoding='utf-8')
    match = re.search(r'message\(STATUS "Board Path: ([^"]+)"\)', text)
    if not match:
        fail(f'Could not resolve board path from {cmake_path}')
    return Path(match.group(1)).resolve()


def normalize_label(path_parts: list[str]) -> str:
    filtered = [part for part in path_parts if part not in {'config', 'pins', 'flags', 'sub_cfg', 'lcd_panel_config', 'io_spi_config', 'spi_bus_config'}]
    if not filtered:
        filtered = path_parts
    label = '.'.join(filtered)
    label = label.replace('_io_num', '').replace('_gpio_num', '').replace('_io', '')
    if label == 'doubt':
        return 'dout'
    return label


def is_pin_key(key: str, parents: list[str]) -> bool:
    return key in PIN_KEY_NAMES or key.endswith(PIN_KEY_SUFFIXES) or (parents and parents[-1] == 'pins')


def collect_io_entries(node: Any, path_parts: list[str] | None = None) -> list[tuple[str, int]]:
    path_parts = path_parts or []
    entries: list[tuple[str, int]] = []

    if isinstance(node, dict):
        for key, value in node.items():
            current_path = path_parts + [str(key)]
            if isinstance(value, int) and value >= 0 and is_pin_key(str(key), path_parts):
                entries.append((normalize_label(current_path), value))
                continue
            if isinstance(value, list) and key == 'data_io':
                for index, item in enumerate(value):
                    if isinstance(item, int) and item >= 0:
                        entries.append((f'{normalize_label(current_path)}[{index}]', item))
                continue
            entries.extend(collect_io_entries(value, current_path))
        return entries

    if isinstance(node, list):
        for index, item in enumerate(node):
            entries.extend(collect_io_entries(item, path_parts + [str(index)]))
    return entries


def format_io_list(entries: list[tuple[str, int]]) -> list[str]:
    seen: set[tuple[str, int]] = set()
    lines: list[str] = []
    for label, pin in entries:
        key = (label, pin)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'- `{label}` -> `GPIO{pin}`')
    return lines


def summarize_peripheral(peripheral: dict[str, Any]) -> dict[str, Any]:
    config = peripheral.get('config')
    io_entries = collect_io_entries(config) if isinstance(config, dict) else []
    return {
        'name': str(peripheral.get('name', '')),
        'io_lines': format_io_list(io_entries),
    }


def summarize_device(device: dict[str, Any], peripheral_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    name = str(device.get('name', ''))
    config = device.get('config')
    peripheral_refs = device.get('peripherals')
    io_entries = collect_io_entries(config) if isinstance(config, dict) else []
    peripherals: list[dict[str, Any]] = []

    if isinstance(peripheral_refs, list):
        for item in peripheral_refs:
            if not isinstance(item, dict):
                continue
            peripheral_name = item.get('name')
            if not isinstance(peripheral_name, str) or not peripheral_name:
                continue
            periph_summary = peripheral_map.get(peripheral_name)
            peripherals.append({
                'name': peripheral_name,
                'io_lines': periph_summary['io_lines'] if periph_summary else [],
            })

    return {
        'name': name,
        'io_lines': format_io_list(io_entries),
        'peripherals': peripherals,
    }


def render_markdown(board_info: dict[str, Any], board_version: str, devices: list[dict[str, Any]]) -> str:
    board_name = str(board_info.get('board', 'unknown'))
    chip = str(board_info.get('chip', 'unknown'))
    manufacturer = str(board_info.get('manufacturer', 'unknown'))
    description = str(board_info.get('description', ''))
    lines = [
        f'# Current Board Hardware: {board_name}',
        '',
        'Read this skill before operating hardware, assigning GPIOs, or writing Lua and board-specific code.',
        '',
        '## Rules',
        '- Before operating any hardware, read this skill first.',
        '- Before assigning a GPIO, check whether it is already occupied below.',
        '- When writing Lua or board-specific code, use the listed device names instead of guessing hardware wiring.',
        '',
        '## Board Summary',
        f'- Board: `{board_name}`',
        f'- Chip: `{chip}`',
        f'- Version: `{board_version}`',
        f'- Manufacturer: `{manufacturer}`',
    ]

    if description:
        lines.append(f'- Description: {description}')

    lines.extend([
        '',
        '## Device Inventory',
    ])

    for device in devices:
        title = f"### {device['name']}"
        lines.extend(['', title])

        io_lines = list(device['io_lines'])
        for peripheral in device['peripherals']:
            io_lines.extend(peripheral['io_lines'])
        io_lines = list(dict.fromkeys(io_lines))

        if io_lines:
            lines.append('- Occupied IO:')
            lines.extend([f'  {line}' for line in io_lines])
        else:
            lines.append('- Occupied IO: none declared')

    lines.extend([
        '',
        '## Notes',
        '- If a device has no explicit IO mapping here, treat it as unknown instead of guessing.',
        '',
    ])
    return '\n'.join(lines)

def main() -> int:
    args = parse_args()
    gen_bmgr_dir = Path(args.gen_bmgr_dir).resolve()
    output_md = Path(args.output_md).resolve()

    board_dir = parse_board_path(gen_bmgr_dir)
    print(f'[cap_boards] Loading board metadata from {board_dir}')
    board_info = load_yaml(board_dir / 'board_info.yaml')
    board_devices = load_yaml(board_dir / 'board_devices.yaml')
    board_peripherals = load_yaml(board_dir / 'board_peripherals.yaml')

    devices_raw = board_devices.get('devices')
    peripherals_raw = board_peripherals.get('peripherals')
    if not isinstance(devices_raw, list):
        fail(f"Expected 'devices' array in {board_dir / 'board_devices.yaml'}")
    if not isinstance(peripherals_raw, list):
        fail(f"Expected 'peripherals' array in {board_dir / 'board_peripherals.yaml'}")

    peripheral_map = {}
    for peripheral in peripherals_raw:
        if not isinstance(peripheral, dict):
            continue
        name = peripheral.get('name')
        if isinstance(name, str) and name:
            peripheral_map[name] = summarize_peripheral(peripheral)

    devices = [
        summarize_device(device, peripheral_map)
        for device in devices_raw
        if isinstance(device, dict) and isinstance(device.get('name'), str) and not str(device.get('name')).startswith('fake')
    ]
    board_version = str(board_info.get('version') or board_devices.get('version') or board_peripherals.get('version') or 'unknown')
    markdown = render_markdown(board_info, board_version, devices)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding='utf-8')
    print(
        f"[cap_boards] Generated skill for board {board_info.get('board', 'unknown')} "
        f'with {len(devices)} devices: {output_md}'
    )
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'generate_board_skill.py: {exc}', file=sys.stderr)
        raise SystemExit(1)
