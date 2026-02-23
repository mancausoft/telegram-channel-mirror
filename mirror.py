#!/usr/bin/env python3
"""
Telegram Channel Mirror - Copy messages between Telegram chats without forwarding.

Supports channels, groups, and topics in any combination.
Messages are sent as new posts (not forwards) so they remain accessible
even if the original is taken down for copyright.
"""

import asyncio
import json
import os
import sys
import argparse
import time

CONFIG_FILE = 'config.json'
STATE_FILE = 'state.json'


def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)


def load_state(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_state(path, state):
    with open(path, 'w') as f:
        json.dump(state, f)


def state_key(pair):
    """Unique key for a source/dest pair."""
    src = str(pair['source'])
    st = str(pair.get('source_topic') or '')
    return f"{src}:{st}"


async def copy_message(client, dest, dest_topic, message):
    """Send a message to dest without forwarding. Uses the same remote file."""
    from telethon.errors import FloodWaitError

    reply_to = dest_topic if dest_topic else None

    try:
        if message.media:
            await client.send_file(
                dest,
                file=message.media,
                caption=message.text or '',
                formatting_entities=message.entities,
                reply_to=reply_to,
            )
        elif message.text:
            await client.send_message(
                dest,
                message=message.text,
                formatting_entities=message.entities,
                reply_to=reply_to,
            )
        else:
            return False
        return True
    except FloodWaitError as e:
        print(f"  flood wait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds + 1)
        return await copy_message(client, dest, dest_topic, message)


async def backfill_pair(client, pair, state, config):
    """Copy all messages from source to dest, starting from last saved position."""
    source = pair['source']
    dest = pair['dest']
    source_topic = pair.get('source_topic')
    dest_topic = pair.get('dest_topic')
    delay = config.get('delay', 1.5)

    sk = state_key(pair)
    start_id = state.get(sk, 0)

    try:
        source = int(source)
    except (ValueError, TypeError):
        pass

    source_entity = await client.get_entity(source)
    dest_entity = await client.get_entity(int(dest))

    src_name = getattr(source_entity, 'title', str(source))
    dst_name = getattr(dest_entity, 'title', str(dest))
    print(f"backfill: {src_name} -> {dst_name} (from id {start_id})")

    iter_kwargs = {
        'entity': source_entity,
        'offset_id': start_id,
        'reverse': True,
        'limit': None,
    }
    if source_topic:
        iter_kwargs['reply_to'] = int(source_topic)

    copied = 0
    skipped = 0

    async for message in client.iter_messages(**iter_kwargs):
        if message.id <= start_id:
            continue

        ok = await copy_message(client, dest_entity, dest_topic, message)
        if ok:
            copied += 1
        else:
            skipped += 1

        state[sk] = message.id

        if copied % 10 == 0 and copied > 0:
            save_state(STATE_FILE, state)
            print(f"  [{copied} copied, {skipped} skipped] last id: {message.id}")

        await asyncio.sleep(delay)

    save_state(STATE_FILE, state)
    print(f"  done: {copied} copied, {skipped} skipped")
    return copied


async def watch_pair(client, pair, state, config):
    """Watch a source for new messages and copy them in real time."""
    from telethon import events

    source = pair['source']
    dest = pair['dest']
    source_topic = pair.get('source_topic')
    dest_topic = pair.get('dest_topic')
    delay = config.get('delay', 1.5)

    try:
        source_int = int(source)
    except (ValueError, TypeError):
        source_int = source

    source_entity = await client.get_entity(source_int)
    dest_entity = await client.get_entity(int(dest))

    src_name = getattr(source_entity, 'title', str(source))
    dst_name = getattr(dest_entity, 'title', str(dest))
    sk = state_key(pair)

    print(f"watching: {src_name} -> {dst_name}")

    @client.on(events.NewMessage(chats=source_entity))
    async def handler(event):
        msg = event.message

        # If filtering by source topic, skip messages from other topics
        if source_topic:
            reply_to = getattr(msg, 'reply_to', None)
            if not reply_to:
                return
            topic_id = getattr(reply_to, 'reply_to_top_id', None) or getattr(reply_to, 'reply_to_msg_id', None)
            if topic_id != int(source_topic):
                return

        await asyncio.sleep(delay)
        ok = await copy_message(client, dest_entity, dest_topic, msg)
        if ok:
            state[sk] = msg.id
            save_state(STATE_FILE, state)
            print(f"  synced message {msg.id} from {src_name}")


async def main():
    parser = argparse.ArgumentParser(
        description='Mirror Telegram channels/groups/topics without forwarding'
    )
    parser.add_argument('--config', default=CONFIG_FILE,
                        help=f'config file path (default: {CONFIG_FILE})')
    parser.add_argument('--state', default=STATE_FILE,
                        help=f'state file path (default: {STATE_FILE})')

    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('backfill', help='copy all existing messages')
    sub.add_parser('sync', help='watch for new messages and copy in real time')
    sub.add_parser('run', help='backfill first, then switch to sync')

    args = parser.parse_args()

    global STATE_FILE
    STATE_FILE = args.state

    config = load_config(args.config)
    state = load_state(STATE_FILE)

    from telethon import TelegramClient

    session = config.get('session_name', 'mirror_session')
    async with TelegramClient(session, config['api_id'], config['api_hash']) as client:
        print("connected to telegram")

        pairs = config.get('pairs', [])
        if not pairs:
            print("no pairs configured")
            return

        if args.command in ('backfill', 'run'):
            for pair in pairs:
                await backfill_pair(client, pair, state, config)

        if args.command in ('sync', 'run'):
            for pair in pairs:
                await watch_pair(client, pair, state, config)

            print("listening for new messages... (ctrl+c to stop)")
            await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
