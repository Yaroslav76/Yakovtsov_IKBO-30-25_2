#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
for name in pkg_a pkg_c pkg_d no_tree depth2 reverse_g; do
    run "tests/configs/stage5_$name.json"
done
start_server
run tests/configs/stage5_maven_app.json
stop_server
