#!/bin/bash
cd "$(dirname "$0")/.."
cp _heart_test/brain_state_calm.json brain_state.json
echo "Loaded CALM state → heart should breathe SLOW. (Quit eLo OS first, or it overwrites.)"
