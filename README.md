# telegram-channel-mirror

Mirror Telegram channels, groups, and topics to other channels/groups/topics without forwarding.

Messages are re-sent as new posts using the same remote file reference, so no data is downloaded. This means that if the original message gets taken down (e.g. copyright claim), the copy remains accessible.

## Installation

### Linux

```bash
git clone https://github.com/mancausoft/telegram-channel-mirror.git
cd telegram-channel-mirror
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### macOS

```bash
git clone https://github.com/mancausoft/telegram-channel-mirror.git
cd telegram-channel-mirror
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you don't have Python 3 installed, get it with [Homebrew](https://brew.sh/):

```bash
brew install python3
```

## Setup

1. Go to [my.telegram.org](https://my.telegram.org), log in and create an application to get your `api_id` and `api_hash`

2. Copy the example config and edit it:

```bash
cp config.json.example config.json
```

3. Fill in your API credentials and configure at least one source/dest pair (see [Configuration](#configuration) below)

4. Run the script once to authenticate - Telethon will ask for your phone number and a login code:

```bash
python mirror.py backfill
```

The session is saved to a `.session` file so you only need to authenticate once.

## Usage

Always activate the virtualenv first:

```bash
source venv/bin/activate
```

### Backfill - copy all existing messages

```bash
python mirror.py backfill
```

### Sync - watch for new messages in real time

```bash
python mirror.py sync
```

### Run - backfill first, then switch to sync

```bash
python mirror.py run
```

Progress is saved to `state.json` automatically. You can stop and restart at any time and it will resume from where it left off.

## Configuration

Edit `config.json`:

```json
{
    "api_id": 12345678,
    "api_hash": "your_api_hash_from_my_telegram_org",
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

### General options

| Field | Description |
|---|---|
| `api_id` | Your Telegram API ID from my.telegram.org |
| `api_hash` | Your Telegram API hash from my.telegram.org |
| `session_name` | Name for the session file (default: `mirror_session`) |
| `delay` | Seconds to wait between messages to avoid rate limits (default: `1.5`) |
| `pairs` | List of source/destination pairs to mirror |

### Pair options

| Field | Description |
|---|---|
| `source` | Source chat: `@username` for public chats, or numeric ID (e.g. `-1001234567890`) for private ones |
| `dest` | Destination chat numeric ID |
| `source_topic` | Topic ID to read from (for groups with topics enabled). Set to `null` to read all messages |
| `dest_topic` | Topic ID to write to. Set to `null` to post to the main chat |

### Finding chat and topic IDs

The easiest way to find a chat ID is to open [Telegram Web](https://web.telegram.org), navigate to the chat, and look at the URL. For example `https://web.telegram.org/k/#-1001234567890` means the chat ID is `-1001234567890`.

For topic IDs, open a topic in Telegram Web and look at the URL. For example `https://web.telegram.org/k/#-1001234567890/456` means the topic ID is `456`.

### Supported combinations

Any combination of source and destination works:

- Channel to channel
- Channel to group
- Channel to topic
- Group to channel
- Group to group
- Group to topic
- Topic to channel
- Topic to group
- Topic to topic

### Multiple pairs

You can mirror multiple sources at once. Each pair runs independently:

```json
{
    "api_id": 12345678,
    "api_hash": "your_api_hash",
    "session_name": "mirror_session",
    "delay": 1.5,
    "pairs": [
        {
            "source": "@channel_a",
            "dest": -1001111111111,
            "source_topic": null,
            "dest_topic": null
        },
        {
            "source": "@channel_b",
            "dest": -1002222222222,
            "source_topic": null,
            "dest_topic": null
        },
        {
            "source": -1003333333333,
            "dest": -1004444444444,
            "source_topic": 123,
            "dest_topic": 456
        }
    ]
}
```

## How it works

Instead of using Telegram's forward feature, the script sends messages as new posts. For media messages, it reuses Telegram's internal file reference so the file is never downloaded - Telegram just creates a new message pointing to the same file on their servers.

This has two advantages:
1. No bandwidth or storage needed for media files
2. The copy is independent from the original - if the source gets deleted or restricted, the copy remains accessible

## License

[WTFPL](LICENSE)
