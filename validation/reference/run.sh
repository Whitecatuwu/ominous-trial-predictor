#!/bin/sh
set -eu
if [ "${REFERENCE_ACCEPT_EULA:-}" != "true" ]; then
    echo 'Minecraft EULA acceptance required: https://aka.ms/MinecraftEULA' >&2
    exit 1
fi
mkdir /world
cd /world
printf 'eula=true\n' > eula.txt
# All other Minecraft properties retain vanilla defaults; no ports are published.
printf 'level-seed=%s\n' "$REFERENCE_SEED" > server.properties
CP=$(sed 's@META-INF/@/opt/reference/META-INF/@g' /opt/reference/classpath)
exec java -Xms512m -Xmx2g \
    -javaagent:/opt/reference/agent.jar -cp "/opt/reference/agent.jar:$CP" \
    net.minecraft.server.Main --nogui
