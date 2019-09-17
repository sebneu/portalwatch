#!/usr/bin/env bash
docker run --rm -d --name odpwui --network="host" odpw -v ODPWUI 1>> /home/opwu/portalwatch_data/odpw_ui.out 2> /home/opwu/portalwatch_data/odpw_ui.err