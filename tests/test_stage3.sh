#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
for name in basic_d3 basic_d1 basic_d0 cycle self chain_d2 chain_d9; do
    run "tests/configs/stage3_$name.json" --stage 3
done
for name in err_missing_root err_bad_line err_bad_name err_duplicate \
        err_bad_dep; do
    run "tests/configs/stage3_$name.json" --stage 3
done
start_server
run tests/configs/stage3_maven_app.json --stage 3
run tests/configs/stage3_maven_cycle.json --stage 3
stop_server
