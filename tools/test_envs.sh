#!/usr/bin/env bash
# Build the ML4PS course environments from scratch, the way the README tells students to, check them with
# tools/check_env.py and execute the course notebooks in them (Linux/macOS).
#
# Usage: tools/test_envs.sh [options] [NOTEBOOK ...]
#   -s DIR   repository to test (default: the repository containing this script). Its working tree is tested,
#            uncommitted changes included (clone of HEAD + copy of the modified and untracked files).
#   -w DIR   work directory, must not exist yet (default: a new ${TMPDIR:-/tmp}/ml4ps-envtest.XXXXXX).
#            Count ~20 GB with all environments. Everything the test produces lands there:
#              repo/            copy of the repository, holding the uv environments .venv-base and .venv
#              envs/            pip and conda environments
#              runs/ENV/N/      a clean copy of the repository for each executed notebook
#              executed/ENV/    executed notebooks (outputs included)
#              logs/            build, check and notebook logs
#              summary.txt      one line per step
#   -e LIST  environments to build and check, comma separated, among uv,uv-torch,pip,conda (default: all four)
#   -n LIST  environments in which to execute the notebooks (default: uv-torch), "none" to only build and check
#   -d DIR   folder holding the datasets the notebooks download to ./data (default: WORKDIR/data), shared by all
#            notebook runs. Seed it (e.g. `cp -al 4-DeepLearning/data DIR`) to avoid downloading them again.
#   NOTEBOOK notebooks to execute, relative to the repository root (default: DEFAULT_NOTEBOOKS below)
#
# Environments:
#   uv        uv sync (README, recommended), checked without PyTorch, built in .venv-base
#   uv-torch  uv sync + the README command adding PyTorch (TORCH_INSTALL below), built in .venv
#   pip       python3.11 -m venv + pip install -r 0-Setup/ML4PSrequirements.txt
#   conda     conda env create -f 0-Setup/ML4PSrequirements.yml (as a prefix in envs/, not a named environment)
#
# Example: check that the first module runs in the uv base environment (1-IntroPython last: its optional cell
# adds PyTorch to the environment)
#   tools/test_envs.sh -e uv -n uv 2-Regression/2-Regression-Solutions.ipynb \
#       3-ClassificationClustering/3-ClassificationClustering-Solutions.ipynb 1-IntroPython/1-IntroPython.ipynb
#
# Commands run inside an environment see it activated, but never see conda itself (removed from PATH): notebook
# cells calling conda cannot create or change conda environments on this machine. Jupyter user kernels and
# config are ignored, so the notebooks always run on the python of the tested environment.
# Requires uv (and conda for the conda environment). Exit code 1 if any step failed.

set -uo pipefail

DEFAULT_NOTEBOOKS=(
    "1-IntroPython/SOLUTIONS_1-IntroPython.ipynb"
    "1-IntroPython/1-IntroPython.ipynb"
    "2-Regression/2-Regression-Solutions.ipynb"
    "3-ClassificationClustering/3-ClassificationClustering-Solutions.ipynb"
    "4-DeepLearning/SOLUTIONS_4-DeepLearning.ipynb"
    "5-Project Biodiversity/ML4PS_2025_Lab5_Biodiversity.ipynb"
)
# Folders where notebooks download datasets with root='./data': all point to the shared data folder
DATA_LINKS=("1-IntroPython/data" "4-DeepLearning/data")
PYTHON_VERSION=3.11
# Command adding PyTorch to the uv environment: keep in sync with the README
TORCH_INSTALL=(uv pip install --torch-backend auto torch==2.6.0 torchvision==0.21.0 segmentation-models-pytorch==0.5.0)
ALL_ENVS="uv,uv-torch,pip,conda"

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || dirname "$SCRIPT_DIR")
W="" DATA="" ENVS=$ALL_ENVS NB_ENVS="uv-torch"

usage() { sed -n '2,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"; exit "${1:-0}"; }
while getopts "s:w:e:n:d:h" opt; do
    case $opt in
        s) SRC=$(cd "$OPTARG" && pwd) ;;
        w) W=$OPTARG ;;
        e) ENVS=$OPTARG ;;
        n) NB_ENVS=$OPTARG ;;
        d) DATA=$OPTARG ;;
        h) usage 0 ;;
        *) usage 1 ;;
    esac
done
shift $((OPTIND - 1))
NOTEBOOKS=("$@")
[ ${#NOTEBOOKS[@]} -eq 0 ] && NOTEBOOKS=("${DEFAULT_NOTEBOOKS[@]}")
[ "$NB_ENVS" = none ] && NB_ENVS=""
IFS=, read -r -a ENV_LIST <<<"$ENVS"
IFS=, read -r -a NB_ENV_LIST <<<"$NB_ENVS"
for e in "${ENV_LIST[@]}" "${NB_ENV_LIST[@]}"; do
    [[ ",$ALL_ENVS," == *",$e,"* ]] || { echo "unknown environment: $e (choose among $ALL_ENVS)" >&2; exit 1; }
done
for e in "${NB_ENV_LIST[@]}"; do
    [[ ",$ENVS," == *",$e,"* ]] || { echo "notebook environment $e is not in the built environments ($ENVS)" >&2; exit 1; }
done
command -v uv >/dev/null || { echo "uv is required" >&2; exit 1; }

if [ -z "$W" ]; then
    W=$(mktemp -d "${TMPDIR:-/tmp}/ml4ps-envtest.XXXXXX")
else
    [ -e "$W" ] && { echo "work directory $W already exists" >&2; exit 1; }
    mkdir -p "$W"
fi
W=$(cd "$W" && pwd)
DATA=${DATA:-$W/data}
mkdir -p "$DATA" "$W/logs" "$W/envs" "$W/executed" "$W/runs" "$W/jupyter/data" "$W/jupyter/config"
DATA=$(cd "$DATA" && pwd)
REPO=$W/repo
SUMMARY=$W/summary.txt
CONDA_BIN=$(command -v conda || true)
CONDA_BASE=$([ -n "$CONDA_BIN" ] && "$CONDA_BIN" info --base 2>/dev/null || true)
FAILED=0

say() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
record() { printf '%-6s %-7s %-6s %6ss  %s\n' "$@" | tee -a "$SUMMARY"; }  # step env status seconds detail

copy_worktree() {  # copy_worktree SRC DEST: tracked + untracked (non ignored) files of SRC, uncommitted changes included
    local src=$1 dest=$2
    if git -C "$src" rev-parse --git-dir >/dev/null 2>&1; then
        git clone --quiet --no-hardlinks "$src" "$dest" || return 1
        (cd "$src" && git ls-files -z --modified --others --exclude-standard) |
            while IFS= read -r -d '' f; do [ -e "$src/$f" ] && printf '%s\0' "$f"; done |
            rsync -a --from0 --files-from=- "$src/" "$dest/" || return 1
        (cd "$src" && git ls-files -z --deleted) | (cd "$dest" && xargs -0 -r rm -f --)
    else
        rsync -a --exclude '/.venv*' "$src/" "$dest/"
    fi
}

env_prefix() {
    case $1 in
        uv) echo "$REPO/.venv-base" ;;
        uv-torch) echo "$REPO/.venv" ;;
        pip) echo "$W/envs/pip" ;;
        conda) echo "$W/envs/conda" ;;
    esac
}

strip_conda() {  # PATH without the entries of the conda installation
    local IFS=: p out=()
    for p in $1; do
        [[ -n $CONDA_BASE && $p == "$CONDA_BASE"* ]] && continue
        out+=("$p")
    done
    echo "${out[*]}"
}

in_env() {  # in_env ENV CMD...: run CMD with ENV activated and conda hidden
    local env=$1; shift
    (
        unset VIRTUAL_ENV CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER PYTHONPATH PYTHONHOME
        PATH=$(strip_conda "$PATH")
        if [ "$env" = conda ]; then
            eval "$("$CONDA_BIN" shell.bash activate "$(env_prefix conda)")" || exit 1
            PATH=$(strip_conda "$PATH")
        else
            export VIRTUAL_ENV
            VIRTUAL_ENV=$(env_prefix "$env")
            PATH=$VIRTUAL_ENV/bin:$PATH
        fi
        unset CONDA_EXE CONDA_PYTHON_EXE _CE_CONDA _CE_M CONDA_SHLVL
        export PATH PYTHONNOUSERSITE=1 JUPYTER_DATA_DIR=$W/jupyter/data JUPYTER_CONFIG_DIR=$W/jupyter/config
        "$@"
    )
}

build() {  # build ENV (uv commands run as in the README: from the repository root, no environment activated)
    case $1 in
        uv) (cd "$REPO" && unset VIRTUAL_ENV CONDA_PREFIX && UV_PROJECT_ENVIRONMENT=.venv-base uv sync --locked) ;;
        uv-torch) (cd "$REPO" && unset VIRTUAL_ENV CONDA_PREFIX && uv sync --locked && "${TORCH_INSTALL[@]}") ;;
        pip)
            local py
            uv python install "$PYTHON_VERSION" && py=$(uv python find "$PYTHON_VERSION") || return 1
            "$py" -m venv "$W/envs/pip" &&
                "$W/envs/pip/bin/python" -m pip install -r "$REPO/0-Setup/ML4PSrequirements.txt" ;;
        conda)
            [ -n "$CONDA_BIN" ] || { echo "conda not found"; return 1; }
            "$CONDA_BIN" env create --quiet --file "$REPO/0-Setup/ML4PSrequirements.yml" --prefix "$W/envs/conda" ;;
    esac
}

probe_kernel() {  # probe_kernel ENV: check that the notebook kernel runs on the python of ENV
    local env=$1 dir=$W/runs/$1/probe got
    mkdir -p "$dir"
    python3 - "$dir/probe.ipynb" <<'EOF'
import json, sys
cell = {"cell_type": "code", "execution_count": None, "id": "probe", "metadata": {}, "outputs": [],
        "source": ["import sys; print(sys.prefix)"]}
json.dump({"cells": [cell], "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
           "language": "python"}}, "nbformat": 4, "nbformat_minor": 5}, open(sys.argv[1], "w"))
EOF
    (cd "$dir" && in_env "$env" python -m nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=python3 \
        --output probe-out.ipynb probe.ipynb) >"$W/logs/probe-$env.log" 2>&1
    got=$(python3 -c 'import json,sys; print("".join(json.load(open(sys.argv[1]))["cells"][0]["outputs"][0]["text"]).strip())' \
        "$dir/probe-out.ipynb" 2>>"$W/logs/probe-$env.log")
    echo "kernel prefix: $got" >>"$W/logs/probe-$env.log"
    [ -n "$got" ] && [ "$(cd "$got" 2>/dev/null && pwd -P)" = "$(cd "$(env_prefix "$env")" && pwd -P)" ]
}

say "Work directory: $W"
say "Testing the working tree of $SRC ($(git -C "$SRC" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'not a git repository'))"
say "Environments: ${ENV_LIST[*]} | notebooks in: ${NB_ENV_LIST[*]:-none} | data: $DATA"
copy_worktree "$SRC" "$REPO" || { echo "could not copy $SRC" >&2; exit 1; }
: >"$SUMMARY"

declare -A BUILT
for env in "${ENV_LIST[@]}"; do
    say "Building $env (log: $W/logs/build-$env.log)"
    start=$SECONDS
    if build "$env" >"$W/logs/build-$env.log" 2>&1; then
        BUILT[$env]=1
        record build "$env" OK $((SECONDS - start)) "$(du -sh "$(env_prefix "$env")" | cut -f1) $(env_prefix "$env")"
    else
        FAILED=1
        record build "$env" FAIL $((SECONDS - start)) "see $W/logs/build-$env.log"
        continue
    fi
    say "Checking $env (log: $W/logs/check-$env.log)"
    start=$SECONDS
    extra=()
    [ "$env" = uv ] && extra=(--no-torch)
    if in_env "$env" python "$SCRIPT_DIR/check_env.py" --requirements "$REPO/0-Setup/ML4PSrequirements.txt" \
        "${extra[@]}" >"$W/logs/check-$env.log" 2>&1; then status=PASS; else status=FAIL; FAILED=1; fi
    record check "$env" $status $((SECONDS - start)) "$(grep -c '  WARN ' "$W/logs/check-$env.log") warning(s), $(tail -n1 "$W/logs/check-$env.log")"
done

for env in "${NB_ENV_LIST[@]}"; do
    [ -n "${BUILT[$env]:-}" ] || { record nb "$env" SKIP 0 "environment not built"; continue; }
    start=$SECONDS
    if probe_kernel "$env"; then
        record kernel "$env" OK $((SECONDS - start)) "notebooks run on $(env_prefix "$env")"
    else
        FAILED=1
        record kernel "$env" FAIL $((SECONDS - start)) "kernel is not the $env python, notebooks skipped (see $W/logs/probe-$env.log)"
        continue
    fi
    i=0
    for nb in "${NOTEBOOKS[@]}"; do
        i=$((i + 1))
        [ -f "$REPO/$nb" ] || { record nb "$env" SKIP 0 "$nb not found"; continue; }
        run=$W/runs/$env/$i
        out=$W/executed/$env/$(dirname "$nb")
        log=$W/logs/nb-$env-$i.log
        mkdir -p "$run" "$out"
        rsync -a --exclude '/.venv*' "$REPO/" "$run/"
        for d in "${DATA_LINKS[@]}"; do
            [ -d "$run/$(dirname "$d")" ] && rm -rf "${run:?}/$d" && ln -s "$DATA" "$run/$d"
        done
        say "Executing $nb in $env (log: $log)"
        start=$SECONDS
        (cd "$run/$(dirname "$nb")" && in_env "$env" python -m nbconvert --to notebook --execute --allow-errors \
            --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=python3 \
            --output-dir "$out" "$run/$nb") >"$log" 2>&1
        executed=$out/$(basename "$nb")
        if [ ! -f "$executed" ]; then
            FAILED=1
            record nb "$env" FAIL $((SECONDS - start)) "$nb: not executed, see $log"
            continue
        fi
        if python3 "$SCRIPT_DIR/nb_report.py" "$executed" >>"$log" 2>&1; then status=OK; else status=ERRORS; FAILED=1; fi
        record nb "$env" $status $((SECONDS - start)) "$nb: $(grep -m1 'code cells' "$log" | sed 's/^ *//')"
    done
done

say "Done. Summary ($SUMMARY):"
cat "$SUMMARY"
say "Details: $W/logs/ (notebook reports at the end of the nb-*.log files), executed notebooks in $W/executed/"
exit $FAILED
