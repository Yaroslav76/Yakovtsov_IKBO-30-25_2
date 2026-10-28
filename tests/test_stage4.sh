#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
run tests/configs/stage3_basic_d3.json --stage 3
for name in basic_e basic_d basic_d_depth1 basic_root cycle_c demo_g \
        err_missing; do
    run "tests/configs/stage4_$name.json" --stage 4
done
run tests/configs/errors/reverse_in_maven.json --stage 4
