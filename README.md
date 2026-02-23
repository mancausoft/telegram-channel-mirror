# telegram-channel-mirror

Mirror Telegram channels, groups, and topics to other channels/groups/topics without forwarding.

Messages are re-sent as new posts using the same remote file reference, so no data is downloaded. This means that if the original message gets taken down (e.g. copyright claim), the copy remains accessible.

## Requirements

- Python 3.8+
- [Telethon](https://github.com/LonamiWebs/Telethon)

```
pip install telethon
```

## Setup

1. Get your API credentials from [my.telegram.org](https://my.telegram.org)
2. Copy the example config:

```
cp config.json.example config.json
```

3. Edit `config.json` with your credentials and source/dest pairs
4. Run the script once to authenticate your session:

```
python mirror.py --config config.json backfill
```

Telethon will ask for your phone number and code on first run.

## Usage

### Backfill (copy all existing messages)

```
python mirror.py backfill
```

### Sync (watch for new messages in real time)

```
python mirror.py sync
```

### Run (backfill first, then sync)

```
python mirror.py run
```

Progress is saved to `state.json` automatically. You can stop and restart at any time - it will resume from where it left off.

## Configuration

```json
{
    "api_id": 12345678,
    "api_hash": "your_api_hash",
    "session_name": "mirror_session",
    "delay": 1.5,
    "pairs": [
        {
            "source": "@public_channel",
            "dest": -1001234567890,
            "source_topic": null,
            "dest_topic": null
        }
    ]
}
```

### Pair options

| Field | Description |
|---|---|
| `source` | Source chat. Can be `@username`, channel/group ID (e.g. `-1001234567890`), or user ID |
| `dest` | Destination chat ID |
| `source_topic` | Topic ID to read from (for groups with topics). `null` to read all messages |
| `dest_topic` | Topic ID to write to. `null` to post to the main chat |

### Supported combinations

Any combination works:

- Channel to channel
- Channel to group
- Group to group
- Group to channel
- Topic to channel
- Topic to topic
- Channel to topic
- Topic to group

### Multiple pairs

You can mirror multiple sources at once:

```json
{
    "pairs": [
        {"source": "@channel_a", "dest": -1001111111111, "source_topic": null, "dest_topic": null},
        {"source": "@channel_b", "dest": -1002222222222, "source_topic": null, "dest_topic": null},
        {"source": -1003333333333, "dest": -1004444444444, "source_topic": 123, "dest_topic": 456}
    ]
}
```

## How it works

Instead of using Telegram's forward feature, the script sends messages as new posts. For media messages, it reuses Telegram's internal file reference (`file_id`) so the file is never downloaded - Telegram just creates a new message pointing to the same file on their servers.

This has two advantages:
1. No bandwidth/storage used for media files
2. The copy is independent from the original - if the source gets deleted or restricted, the copy stays

## License

[WTFPL](LICENSE)
