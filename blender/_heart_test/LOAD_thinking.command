#!/bin/bash
cd "$(dirname "$0")/.."
cp _heart_test/brain_state_thinking.json brain_state.json
echo "Loaded THINKING state → heart should beat FAST. (Quit eLo OS first, or it overwrites.)"
