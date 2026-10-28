#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
start_server
run tests/configs/stage2_app.json --stage 2
run tests/configs/stage2_lib_b.json --stage 2
run tests/configs/stage2_leaf.json --stage 2
run tests/configs/stage2_cycle.json --stage 2
run tests/configs/stage2_err_missing_pom.json --stage 2
run tests/configs/stage2_err_broken_pom.json --stage 2
stop_server
run tests/configs/stage2_err_no_server.json --stage 2
