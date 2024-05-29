# VGM-Sources-Upload-Bot
Deletes messages from specified channel and reposts them elsewhere

# Commands
- !set_monitored_channel - Channel to monitor for messages without a link/attachment and delete them if so.
- !set_repost_channel = Channel to subsequently repost the deleted message to.
- !set_debug_channel = Debug channel.
- !show_debug_info = Show debug info from saved JSON.
- !print_debug_info = Show current debug info from memory rather than JSON.

# Known Bugs
- For some reason, the designated repost channel doesn't actually repost deleted messages from the monitored channel unless the command is rerun upon restart.
