#!/usr/bin/env bash

# Read variables
echo -en "New hostname > "
read HOST

echo -en "New tunnel port > "
read PORT

# Set hostname everywhere
sudo sed -i -E "s/vpi.+/$HOST/" /etc/hosts && cat /etc/hosts
sudo hostname $HOST
echo $HOST | sudo tee /etc/hostname

# Generate a new GUID
sudo python3 -c 'import snowflake; snowflake.make_snowflake()'

# Remove old API key
rm ~/votebox/auth.json

# Update tunnel port
sudo sed -i "s|\(\/opt\/tunnel\/tunnel.sh\) \(22\) \([0-9\ ]*\) \(.*\)|\1 \2 $PORT \4|" /etc/rc.local
