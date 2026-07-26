#!/bin/sh

set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: validate_contract.sh BUNDLE_DIRECTORY" >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
contract_root=$(CDPATH= cd -- "$script_dir/../.." && pwd)
bundle_dir=$1
validation_tmp=$(mktemp -d)
trap 'rm -r -- "$validation_tmp"' EXIT HUP INT TERM
ajv_bin="$contract_root/contract/node_modules/.bin/ajv"

if [ ! -x "$ajv_bin" ]; then
  npm ci --prefix "$contract_root/contract" \
    --ignore-scripts --no-audit --no-fund
fi

for document in configuration world protocol analysis; do
  python3 "$script_dir/toml_to_json.py" \
    "$bundle_dir/$document.toml" \
    "$validation_tmp/$document.json"
  "$ajv_bin" validate --spec=draft2020 \
    -s "$contract_root/schemas/$document.schema.json" \
    -d "$validation_tmp/$document.json"
done

julia "$script_dir/validate_bundle.jl" "$bundle_dir"
python3 "$script_dir/test_schema_variants.py"
julia "$script_dir/test_semantic_conformance.jl"
julia "$script_dir/test_seed_escrow.jl"
julia "$script_dir/test_analysis_math.jl"
julia "$script_dir/test_rng_transforms.jl"
python3 "$script_dir/public_contract_manifest.py" --check
julia "$script_dir/canonical_bundle.jl" build \
  "$bundle_dir" "$validation_tmp/$(basename "$bundle_dir").tar"
julia "$script_dir/canonical_bundle.jl" verify \
  "$validation_tmp/$(basename "$bundle_dir").tar"
if [ "$(basename "$bundle_dir")" = "51-P-00" ]; then
  julia "$script_dir/canonical_bundle.jl" self-test
  python3 "$script_dir/independent_verify.py" \
    "$validation_tmp/$(basename "$bundle_dir").tar" \
    "$contract_root/contract/archive-test-vector.sha256"
else
  python3 "$script_dir/independent_verify.py" \
    "$validation_tmp/$(basename "$bundle_dir").tar"
fi

echo "authoritative contract validation passed"
