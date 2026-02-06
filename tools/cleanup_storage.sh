#!/usr/bin/env bash
# tools/cleanup_storage.sh
# 안전한 디스크 정리 도구 (WSL용)
# 기본 동작: 드라이런(목록만 출력). 삭제/정리 수행하려면 --yes 또는 플래그 사용.

set -euo pipefail

DRY_RUN=1
REMOVE_NODE_MODULES=0
PRUNE_PNPM=0
PRUNE_NPM=0
DOCKER_PRUNE=0
JSON_OUT=""
GENERATE_DELETE_LIST=""
SELECT_DELETE_LIST=""

usage() {
  cat <<EOF
usage: cleanup_storage.sh [--yes] [--remove-node-modules] [--prune-pnpm] [--prune-npm] [--docker-prune]

Options:
  --yes                   : 실제 삭제/정리 수행 (없으면 모두 드라이런)
  --remove-node-modules   : 찾은 node_modules 디렉터리를 삭제
  --prune-pnpm            : pnpm store prune 실행 (존재할 때)
  --prune-npm             : npm cache clean/verify 실행 (존재할 때)
  --docker-prune          : docker system prune -a --volumes 실행 (권장 확인)
  -h, --help              : 이 도움말

Examples:
  ./tools/cleanup_storage.sh                # 드라이런 (목록만)
  ./tools/cleanup_storage.sh --yes --prune-pnpm --remove-node-modules

Note: 삭제는 되돌릴 수 없습니다. 중요 데이터는 백업하세요.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) DRY_RUN=0; shift ;;
    --remove-node-modules) REMOVE_NODE_MODULES=1; shift ;;
    --prune-pnpm) PRUNE_PNPM=1; shift ;;
    --prune-npm) PRUNE_NPM=1; shift ;;
    --docker-prune) DOCKER_PRUNE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --json-out) JSON_OUT="$2"; shift 2 ;;
    --generate-delete-list) GENERATE_DELETE_LIST="$2"; shift 2 ;;
    --select-delete-list) SELECT_DELETE_LIST="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

echo "[cleanup_storage] mode: $( [[ $DRY_RUN -eq 1 ]] && echo 'DRY-RUN' || echo 'EXECUTE' )"
echo

echo "[1/6] Filesystem usage"
DF_OUT=$(df -h || true)
echo "$DF_OUT"
echo

if [[ -n "$JSON_OUT" ]]; then
  mkdir -p "$(dirname "$JSON_OUT")" 2>/dev/null || true
  echo "{" > "$JSON_OUT"
  echo "  \"timestamp\": \"$(date --iso-8601=seconds)\"," >> "$JSON_OUT"
  echo "  \"filesystem\": " >> "$JSON_OUT"
  echo "$(echo "$DF_OUT" | python3 -c 'import sys,json;lines=sys.stdin.read().strip().split("\n");head=lines[0].split();rows=[dict(zip(head,x.split())) for x in lines[1:]];print(json.dumps(rows,ensure_ascii=False,indent=2))' 2>/dev/null)" >> "$JSON_OUT" || true
  echo "," >> "$JSON_OUT"
fi
echo

echo "[2/6] Top directories in HOME"
TOPDIRS=$(du -h --max-depth=1 "$HOME" 2>/dev/null | sort -h || true)
echo "$TOPDIRS"
if [[ -n "$JSON_OUT" ]]; then
  echo "  \"top_dirs\": " >> "$JSON_OUT"
  echo "$(echo "$TOPDIRS" | awk '{printf "{\\"size\\":\\"%s\\",\\"path\\":\\"%s\\"},",$1,$2}' | sed 's/,$//;s/^/[ /;s/$/ ]/')" >> "$JSON_OUT" 2>/dev/null || true
  echo "," >> "$JSON_OUT"
fi
echo

echo "[3/5] Top node_modules under HOME (up to 100 entries)"
TMPFILE=$(mktemp)
(find "$HOME" -type d -name node_modules -prune -exec du -sh '{}' 2>/dev/null \; | sort -h) | tee "$TMPFILE" >/dev/null || true
NODES=()
if [[ -s "$TMPFILE" ]]; then
  while IFS= read -r line; do
    NODES+=("$line")
  done < "$TMPFILE"
  for i in "${NODES[@]}"; do
    echo "  $i"
  done | tail -n 100
else
  echo "No node_modules found under $HOME"
fi
if [[ -n "$JSON_OUT" ]]; then
  echo "  \"node_modules\": [" >> "$JSON_OUT"
  for entry in "${NODES[@]}"; do
    size=$(echo "$entry" | awk '{print $1}')
    path=$(echo "$entry" | awk '{print $2}')
    echo "    { \"size\": \"$size\", \"path\": \"$path\" }," >> "$JSON_OUT"
  done
  # remove trailing comma properly
  sed -i '$ s/,\s*$//' "$JSON_OUT" 2>/dev/null || true
  echo "  ]," >> "$JSON_OUT"
fi
rm -f "$TMPFILE"
echo

if [[ $REMOVE_NODE_MODULES -eq 1 ]]; then
  echo "[4/5] Removing node_modules (requested)"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY-RUN: No deletion performed. Re-run with --yes to delete."
  else
    echo "WARNING: Deleting all node_modules found under $HOME"
    read -p "Type YES to continue: " CONF
    if [[ "$CONF" != "YES" ]]; then
      echo "Aborted by user."; exit 1
    fi
    for entry in "${NODES[@]}"; do
      path=$(echo "$entry" | awk '{print $2}')
      if [[ -d "$path" ]]; then
        echo "Removing: $path"
        rm -rf "$path"
      fi
    done
    echo "Removal complete."
  fi
else
  echo "[4/5] node_modules removal not requested (skip)"
fi
echo

if [[ $PRUNE_PNPM -eq 1 ]]; then
  echo "[5/5] pnpm store prune"
  if command -v pnpm >/dev/null 2>&1; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY-RUN: pnpm store path: $(pnpm store path 2>/dev/null || echo 'unknown')"
      echo "Re-run with --yes to actually prune the pnpm store."
    else
      pnpm store prune || echo "pnpm store prune failed or nothing to do"
    fi
  else
    echo "pnpm not installed — skipping pnpm steps"
  fi
fi

if [[ $PRUNE_NPM -eq 1 ]]; then
  echo "npm cache actions"
  if command -v npm >/dev/null 2>&1; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY-RUN: npm cache verify would run. Re-run with --yes to execute."
    else
      npm cache verify || true
      # npm cache clean may require --force and is destructive
      read -p "Run 'npm cache clean --force'? Type YES to continue: " CNF
      if [[ "$CNF" = "YES" ]]; then
        npm cache clean --force || true
      else
        echo "Skipped npm cache clean."
      fi
    fi
  else
    echo "npm not installed — skipping npm cache steps"
  fi
fi

if [[ $DOCKER_PRUNE -eq 1 ]]; then
  echo "docker prune requested"
  if command -v docker >/dev/null 2>&1; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY-RUN: docker system df"; docker system df || true
      echo "Re-run with --yes to perform 'docker system prune -a --volumes'"
    else
      read -p "Docker prune will remove images/containers/volumes. Type YES to continue: " DCF
      if [[ "$DCF" = "YES" ]]; then
        docker system prune -a --volumes
      else
        echo "Skipped docker prune."
      fi
    fi
  else
    echo "docker not found — skipping docker prune"
  fi
fi

if [[ -n "$JSON_OUT" ]]; then
  # finish JSON
  # remove possible trailing commas and close
  sed -i ':a;N;$!ba;s/,\n\s*\]/\n  ]/g' "$JSON_OUT" 2>/dev/null || true
  echo "  \"note\": \"run with --yes to perform destructive actions\"" >> "$JSON_OUT"
  echo "}" >> "$JSON_OUT"
  echo "Wrote JSON report to $JSON_OUT"
fi

if [[ -n "$GENERATE_DELETE_LIST" ]]; then
  echo "Generating delete list to $GENERATE_DELETE_LIST"
  mkdir -p "$(dirname "$GENERATE_DELETE_LIST")" 2>/dev/null || true
  : > "$GENERATE_DELETE_LIST"
  for entry in "${NODES[@]}"; do
    size=$(echo "$entry" | awk '{print $1}')
    path=$(echo "$entry" | awk '{print $2}')
    echo -e "$size\t$path" >> "$GENERATE_DELETE_LIST"
  done
  echo "Delete list saved. Review before deleting." 
fi

if [[ -n "$SELECT_DELETE_LIST" ]]; then
  if [[ ! -f "$SELECT_DELETE_LIST" ]]; then
    echo "Select list file not found: $SELECT_DELETE_LIST"; exit 1
  fi
  echo "Interactive deletion from $SELECT_DELETE_LIST"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY-RUN mode: no deletion will be performed. Re-run with --yes to execute.";
  else
    while IFS=$'\t' read -r size path; do
      if [[ -d "$path" ]]; then
        echo "Delete candidate: $path ($size)"
        read -p "Delete? Type YES to delete: " Y
        if [[ "$Y" = "YES" ]]; then
          rm -rf "$path" && echo "Deleted $path"
        else
          echo "Skipped $path"
        fi
      fi
    done < "$SELECT_DELETE_LIST"
  fi
fi

echo "\nDone. Review above output. Use --yes to perform destructive actions."
