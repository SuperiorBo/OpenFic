# SuperiorBo/OpenFic — maintenance notes

This is a **fork** of [syrizelink/OpenFic](https://github.com/syrizelink/OpenFic)
used for self-hosted stability patches (agent loops, edit tools, retries).

## Remotes

| Remote     | URL                                      | Role              |
|------------|------------------------------------------|-------------------|
| `origin`   | `https://github.com/SuperiorBo/OpenFic`  | Our fork (push)   |
| `upstream` | `https://github.com/syrizelink/OpenFic`  | Official (pull)   |

## Sync from upstream

```bash
git fetch upstream
git checkout main
git merge upstream/main   # or: git rebase upstream/main
git push origin main
```

After merging upstream, re-apply or rebase feature branches:

```bash
git checkout fix/agent-stability-loops
git rebase main
git push origin fix/agent-stability-loops --force-with-lease
```

## Deploy (this host)

Data lives in Docker volume `openfic` (`/data` in container). **Never**
`docker volume rm openfic` when swapping images.

```bash
# Full rebuild (needs network for base images / uv)
docker compose build
docker compose up -d

# Fast backend-only refresh when openfic:local already exists:
docker build -f Dockerfile.local-patch -t openfic:local .
docker stop openfic && docker rm openfic
docker compose up -d
```

Port mapping: host **9888** → container 8000.

## Patches on `fix/agent-stability-loops`

1. **LLM retry** — retry empty stream / stream chunk timeout / empty assistant
   turns inside the ReAct `llm_call` node (up to 8 attempts; avoids immediate
   subagent death on Grok jitter).
2. **Edit line-number strip** — `fuzzy_replace` strips `N|` prefixes copied
   from `read_*` tools so `edit_*` stops failing in a loop.
3. **Tool-failure circuit breaker** — same tool failing 3 times ends the turn.
4. **Lower iteration caps** — primary default 80, subagent 40 (was 1000).
5. **Stream chunk stall timeout** — OpenAI-compatible models use
   `stream_chunk_timeout=300s` by default (was langchain 120s). Override with
   `LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S` (0 disables).

## Intentionally not changed (yet)

- Auto-recycle of completed subagents (product sticky-session design).
- Stream chunk timeout env (set via compose if needed).
