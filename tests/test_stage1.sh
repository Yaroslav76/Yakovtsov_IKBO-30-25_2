#!/usr/bin/env bash
. "$(dirname "$0")/lib.sh"
run tests/configs/stage1_ok.json --stage 1
run tests/configs/stage1_ok_test_mode.json --stage 1
for f in tests/configs/errors/*.json; do
    run "$f" --stage 1
done
run tests/no_such.json --stage 1
run tests/data --stage 1
