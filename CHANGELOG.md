# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
and commits should be formatted using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Added

- Config: Migrate (BC for now) from env-only to YAML + env configuration ([e7f5cb5](https://github.com/moodlehq/wiki-rag/commit/e7f5cb52b32f90415a53a82c520585138883e6c2))
- Config: Add `generate-config.py` migration script

### Changed

- GitHub: Update various GH actions to actual versions by @stronk7 ([5851e6a](https://github.com/moodlehq/wiki-rag/commit/5851e6ab0a507d682bb4d9124dd5dd0a08b6d3cd))
- Config: Re-organise various config sections and model fallbacks ([ac1d099](https://github.com/moodlehq/wiki-rag/commit/ac1d099524cdc8e5bab1ebf8778f19dae8e75240))

### Fixed

- Search: Use only HyDE passages for dense search, not the original query by @stronk7 ([1527624](https://github.com/moodlehq/wiki-rag/commit/1527624c924f9fdbb423d188a68c3026a656ed86))

## [0.14.0] - 2026-04-06

### Added

- Loader: Skip dump file when no incremental changes are detected by @stronk7 ([57106dd](https://github.com/moodlehq/wiki-rag/commit/57106dddf4241db64a105d5269d93d31da38a1ea))
- Indexer: Skip re-indexing when dump was already indexed by @stronk7 ([2562b60](https://github.com/moodlehq/wiki-rag/commit/2562b60a97276861dfbb0b6834c532b6fcdd37f3))
- Cleanup: Make the scripts directory available within the container by @stronk7 ([3986860](https://github.com/moodlehq/wiki-rag/commit/398686013ce353e6f13964eae23bbbaa16caf3a6))
- MCP: Add bearer token authentication to the MCP server by @stronk7 ([b26e9ee](https://github.com/moodlehq/wiki-rag/commit/b26e9ee81b5f1f12c5eeab62811911e09ca20276))
  - **BREAKING**: Previously unprotected calls to the MCP server will now
require to provide a valid bearer token, configured in the server, see
`AUTH_TOKENS` and/or `AUTH_URL` for supported verifications.

- Search: Add HyDE (Hypothetical Document Embeddings) support by @stronk7 ([0548728](https://github.com/moodlehq/wiki-rag/commit/0548728290ddf5e6374a053fc4f0f1759206c3e7))

### Changed

- Dependencies: Upgrade Langfuse to new major release 4.x by @stronk7 ([6b9372c](https://github.com/moodlehq/wiki-rag/commit/6b9372cf2d111069ac343225848eae830ad89d2a))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.13.1...v0.14.0

## [0.13.1] - 2026-03-23

### Fixed

- Server: Solved a regression in the web server, preventing it to run properly by @stronk7 ([109e321](https://github.com/moodlehq/wiki-rag/commit/109e3217456b57c3eef15a96a88846c435625b9b))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.13.0...v0.13.1

## [0.13.0] - 2026-03-20

### Added

- Loader: Add incremental load mode to wr-load by @stronk7 ([63ced69](https://github.com/moodlehq/wiki-rag/commit/63ced69b833120242abc9355a1ff703fc8cc671f))
- Indexer: Add incremental index mode to wr-index by @stronk7 ([3c3b3ac](https://github.com/moodlehq/wiki-rag/commit/3c3b3ac3934dbc809409821156bddfd6ec965dec))
- Cleanup: Add wr-cleanup.sh dump file retention script by @stronk7 ([2790460](https://github.com/moodlehq/wiki-rag/commit/27904606d773c0df111d7717f5766f63ab61a2f8))
- Lock: Add per-instance lock to prevent concurrent wr-load / wr-index by @stronk7 ([2c39c63](https://github.com/moodlehq/wiki-rag/commit/2c39c633a2e17ec3ebf40629cb6e6d3ce5c94943))

### Changed

- Docker: Update the docker image to Python 3.13 by @stronk7 ([124cfc8](https://github.com/moodlehq/wiki-rag/commit/124cfc8b060d94e101b3e842f65543d2c3b5ebca))
- Dependencies: Bump all library and dev dependencies by @stronk7 ([7be5992](https://github.com/moodlehq/wiki-rag/commit/7be5992d8270bdf88bbdca25cfd5ab91dcbf1fc4))
- Tests: Mirror source package structure in tests/ by @stronk7 ([f69d765](https://github.com/moodlehq/wiki-rag/commit/f69d765d79959fe35592e36cf904a764075fda2e))
- Move all imports to module top-level by @stronk7 ([ccf3f0e](https://github.com/moodlehq/wiki-rag/commit/ccf3f0e8aee8e4177d7299f54eea85bf22f58e28))

### Fixed

- Prompts: Reconcile local prompts with external ones by @stronk7 ([c547bbb](https://github.com/moodlehq/wiki-rag/commit/c547bbb101240d991f2df4ae09c97a488acaa389))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.12.2...v0.13.0

## [0.12.2] - 2026-01-09

### Changed

- Dependencies: Bump pymilvus to 2.6.6 by @stronk7 ([7e80ea4](https://github.com/moodlehq/wiki-rag/commit/7e80ea488663200700502d500a40832715f06e83))
- Dependencies: Bump all library and dev dependencies by @stronk7 ([00b3f96](https://github.com/moodlehq/wiki-rag/commit/00b3f96ad9c31b6d102dd578c273c4525770e60a))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.12.1...v0.12.2

## [0.12.1] - 2025-12-01

### Changed

- LLM: Increase default max_completion_tokens to 1536 by @stronk7 ([8d7daba](https://github.com/moodlehq/wiki-rag/commit/8d7daba71bfc33e1a8f6a82b0bf10e1f7624057c))
- Detail: Rename `env_template` to `dotenv.template` by @stronk7 ([f04b54d](https://github.com/moodlehq/wiki-rag/commit/f04b54d5bceb80d6d8e21658032f16d67d775def))
- Deprecation: Stop using `get_event_loop_policy()`, deprecated in Python >= 3.14 by @stronk7 ([053157b](https://github.com/moodlehq/wiki-rag/commit/053157b155ec8bb6223dce56f6931012dda4a382))
- Dependencies: Bump pymilvus to 2.6.4 by @stronk7 ([2a77c7e](https://github.com/moodlehq/wiki-rag/commit/2a77c7e2943c926efadb65d8b4c20c8d4e35e3e9))

### Fixed

- Embeddings: Solved a problem caused by recent Langchain updates by @stronk7 ([678af33](https://github.com/moodlehq/wiki-rag/commit/678af33d48e2963ece3da4fa421ab3580df7fd32))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.12.0...v0.12.1

## [0.12.0] - 2025-11-03

### Added

- Indexer: Add JSON schema support and apply for it before indexing by @stronk7 ([81b49e3](https://github.com/moodlehq/wiki-rag/commit/81b49e3ce7631f7e04da33024ca6049ea5ce7bcb))
- Vector Stores: First step towards making vector stores pluggable by @stronk7 ([b605134](https://github.com/moodlehq/wiki-rag/commit/b60513481efa64f2bcd618e64c06e4316db7b412))
- Vector Stores: Move the indexer and the searcher to use pluggable stores. by @stronk7 ([a49c037](https://github.com/moodlehq/wiki-rag/commit/a49c037732e23883fba4f069e18510314c45c63b))
- Vector Stores: Move the OpenAI and MCP servers to use pluggable stores. by @stronk7 ([2cccf31](https://github.com/moodlehq/wiki-rag/commit/2cccf31d04018466fcf738a5df2b6dda2af355bf))

### Changed

- GitHub: Run workflows also with Python 3.14 (aka, πthon) by @stronk7 ([ffc9b17](https://github.com/moodlehq/wiki-rag/commit/ffc9b17312ee7e190050585d674d3f11510fa8f2))
- Loader: Improve the generation of page head sections by @stronk7 ([a228019](https://github.com/moodlehq/wiki-rag/commit/a228019a03284aa21da8661adfd2c23dac9eee8d))
- Indexer: Better handling of preamble and contents on indexing by @stronk7 ([996eeec](https://github.com/moodlehq/wiki-rag/commit/996eeecfc9d3f49ee6b9264ae77cea9fa5bb0f34))
- Searcher: Improve the "popularity" optimisation by @stronk7 ([5e84ba5](https://github.com/moodlehq/wiki-rag/commit/5e84ba5039fdb02a8b5549297036cbe7c3931d03))
- Retriever: Improve the query rewrite to be more specific by @stronk7 ([f2156bf](https://github.com/moodlehq/wiki-rag/commit/f2156bf3f68bd773b971cf5a380fe2487326f096))
- MCP: Switch the server from SSE to HTTP by @stronk7 ([967ba0c](https://github.com/moodlehq/wiki-rag/commit/967ba0c3853644de0106d7a5402178fb59ebd512))
  - **BREAKING**: Any client previously using MCP SSE clients
must change the transport to HTTP. Normally this change is
trivial and everything continues working exactly the same.


### Fixed

- MCP: Fix the MCP resources to work with the new file format added in [v0.11.2](#0112---2025-10-22) by @stronk7 ([9ef93b3](https://github.com/moodlehq/wiki-rag/commit/9ef93b38af071d8dc9c96fcef6362ed56699c3f5))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.11.2...v0.12.0

## [0.11.2] - 2025-10-22

### Added

- Loader: Modify the dump file format to support metadata by @stronk7 ([49695ee](https://github.com/moodlehq/wiki-rag/commit/49695ee094f11eba5b077f4de46d9b2ffbde4ec7))

### Changed

- Dependencies: Bump dependencies, most noticeably FastMCP by @stronk7 ([38bdbe6](https://github.com/moodlehq/wiki-rag/commit/38bdbe6709365408e1bfb78f0d17d147a164aafc))
- Dependencies: Bump langchain and langgraph libs to 1.0.x by @stronk7 ([811cd88](https://github.com/moodlehq/wiki-rag/commit/811cd88d8f656765d873df957d220c7311b7aafe))

### Fixed

- Indexing: Avoid name clashes when finding the JSON file to index by @stronk7 ([7ac9dde](https://github.com/moodlehq/wiki-rag/commit/7ac9ddeb75aafb4a3a0ddda5a333de9b722e3312))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.11.1...v0.11.2

## [0.11.1] - 2025-09-23

### Fixed

- Langfuse: Ensure that all objects passed are JSON-serializable by @stronk7 ([307e577](https://github.com/moodlehq/wiki-rag/commit/307e57768394ff4c0a39aee252d72fd31da9847c))
- GitHub: Fixed problem causing release docker images to be skipped by @stronk7 ([b9796a3](https://github.com/moodlehq/wiki-rag/commit/b9796a3e3eb01a557a2a5b28865502fdb091bd2b))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.11.0...v0.11.1

## [0.11.0] - 2025-09-19

### Added

- GitHub: Add test and check (pre-commit) job to commits and PRs by @stronk7 ([0c7e15b](https://github.com/moodlehq/wiki-rag/commit/0c7e15b44f479097db75d0980558f786ee8f804e))

### Changed

- Milvus: Bump Milvus client dependencies to v2.6.2 and up by @stronk7 ([aecfd9f](https://github.com/moodlehq/wiki-rag/commit/aecfd9f9d047b8139dd575aad2568be7d8955e6a))
  - **BREAKING**: This may require to upgrade or regenerate the Milvus instance
    (currently v2.5.x) although no specific v2.6 features are being used yet.


**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.10.0...v0.11.0

## [0.10.0] - 2025-09-13

### Added

- Langgraph: Switch to new contexts vs previous configs by @stronk7 ([4d1971d](https://github.com/moodlehq/wiki-rag/commit/4d1971d2d83459922f1d1024ff4d7d6ce54210a1))
- Loader: Add option to control rate limiting by @yusufozgur ([56eabcf](https://github.com/moodlehq/wiki-rag/commit/56eabcf2e69142a31ad3b146ef00d3bd9bb1471a))

### Changed

- Dependencies: Bump dependencies, most noticeably Langfuse 3.x by @stronk7 ([3a4f19e](https://github.com/moodlehq/wiki-rag/commit/3a4f19e400418b01c67ba00c14e16642466ac94b))
- MCP: Move from MCP official library to FastMCP v2 by @stronk7 ([c600552](https://github.com/moodlehq/wiki-rag/commit/c600552b74bdff31e29c0fd84b6d3b9933acc6a3))

### New Contributors 🧡:

- @yusufozgur made their first contribution

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.9.1...v0.10.0

## [0.9.1] - 2025-08-25

### Changed

- Dependencies: Update all runtime and development dependencies by @stronk7 ([679737a](https://github.com/moodlehq/wiki-rag/commit/679737a2dc65c587980a777348b1302895e87f2b))

### Fixed

- Loader: Solve a problem while loading files with 1 section by @stronk7 ([2ca8643](https://github.com/moodlehq/wiki-rag/commit/2ca8643cac275884084c381db1afa201be823d31))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.9.0...v0.9.1

## [0.9.0] - 2025-05-20

### Added

- Prompts: Split langsmith tracing and prompts management by @stronk7 ([4397a86](https://github.com/moodlehq/wiki-rag/commit/4397a864ee35508fa2a06c59544860867fa03895))
- Langfuse: Add Langfuse observability support by @stronk7 ([2f1be65](https://github.com/moodlehq/wiki-rag/commit/2f1be65900255d837bb8d4bf913a4a557cd2f404))
- Langfuse: Add Langfuse prompt management support by @stronk7 ([2d6127f](https://github.com/moodlehq/wiki-rag/commit/2d6127f308fa7da21908f94818108cde59e39076))

### Changed

- Update docs to show latest changes by @stronk7 ([66d5c2c](https://github.com/moodlehq/wiki-rag/commit/66d5c2c0a42f3aa465ea70d067af74c0aa502984))

### Fixed

- Search: Fix a problem with the `wr-search --stream` command by @stronk7 ([962e59f](https://github.com/moodlehq/wiki-rag/commit/962e59f344613c88ecb882fa024b358256185383))
- CI: Initial unit tests and associated configuration by @stronk7 ([fed640b](https://github.com/moodlehq/wiki-rag/commit/fed640b1255dd0326963753990b098b7405c523d))
- Langgraph: Small fixes to state management by @stronk7 ([59f1d4f](https://github.com/moodlehq/wiki-rag/commit/59f1d4f6d9d7c570ec71359577bd7eb0b261ebd5))
- Milvus: Downgrade to pymilvus 2.5.6 by @stronk7 ([6081eb8](https://github.com/moodlehq/wiki-rag/commit/6081eb8f3eb0816b5fb9c04fda8760746995c86e))
- Prompts: Fix local context-query prompt by @stronk7 ([0c474ef](https://github.com/moodlehq/wiki-rag/commit/0c474ef83570e859ba0b7a4e3b283755b469d5ec))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.8.0...v0.9.0

## [0.8.0] - 2025-05-13

### Added

- Server: Start listening to custom events by @stronk7 ([6eca5dd](https://github.com/moodlehq/wiki-rag/commit/6eca5dd3f3ed0683dd7bfcf4773201a96f255697))
- Config: Add support for a new CONTEXTUALISATION_MODEL by @stronk7 ([0845b41](https://github.com/moodlehq/wiki-rag/commit/0845b41b37f6a2d0e389da69f42f5451b121d944))
- RAG: Introduce context awareness support to the system by @stronk7 ([77cac73](https://github.com/moodlehq/wiki-rag/commit/77cac73469da7c07710851be51321b13e1c923fc))

### Changed

- Changelog: Better handling of (skipped) merge commits by @stronk7 ([c9f9e4c](https://github.com/moodlehq/wiki-rag/commit/c9f9e4ce66141631fe0baed44c1d3d0d0469e17d))
- Dependencies: Update all run and dev dependencies by @stronk7 ([a756141](https://github.com/moodlehq/wiki-rag/commit/a756141798acb6fe3ddecec35e1aadd737733a26))

### Fixed

- MCP: Apply the history filtering to the MCP server by @stronk7 ([bcce5df](https://github.com/moodlehq/wiki-rag/commit/bcce5df0e3f0165fab1cdf7a5a0aee0a7b504cce))
- Langgraph: Make the conditional edges easier to understand by @stronk7 ([9d6a0b4](https://github.com/moodlehq/wiki-rag/commit/9d6a0b4f3312e3440d5903f1bc6b359386f4825f))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.7.1...v0.8.0

## [0.7.1] - 2025-04-13

### Added

- Loader: Add support to keep some templates in the wiki text by @stronk7 ([07f05e4](https://github.com/moodlehq/wiki-rag/commit/07f05e4287724d66fbea2f17d7a52f60887aab96))
- CI: Add support for codespell via pre-commit hooks by @stronk7 ([c7f9d96](https://github.com/moodlehq/wiki-rag/commit/c7f9d964358ccf8497f071304acbd48aa8c074cc))

### Changed

- Update cliff.toml by @cclauss ([f50fa79](https://github.com/moodlehq/wiki-rag/commit/f50fa7913151ccba24f41b83057826ad8e9dbf22))

### Fixed

- Docs: Small changes towards better tracking of modifications by @stronk7 ([9fe3e14](https://github.com/moodlehq/wiki-rag/commit/9fe3e148a9a7b9aedbaa15dfb4b2f31df16d360b))
- Typos discovered by codespell by @cclauss ([c4a7fef](https://github.com/moodlehq/wiki-rag/commit/c4a7fefd56596d76f3070e5cd715767f32b3c275))
- Fix a few defaults and return lists by @stronk7 ([79bb773](https://github.com/moodlehq/wiki-rag/commit/79bb773994d9945df47b56630cd38fde12df5741))

### New Contributors 🧡:

- @cclauss made their first contribution

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.7.0...v0.7.1

## [0.7.0] - 2025-04-07

### Added

- MCP: Make Wiki-RAG to behave as a MCP server by @stronk7 ([dfd34b3](https://github.com/moodlehq/wiki-rag/commit/dfd34b346a5615ad7490b7c29f44fc65fb58b6a9))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.6.2...v0.7.0

## [0.6.2] - 2025-04-03

### Fixed

- Config: Add some missing config settings to the config schema by @stronk7 ([9d308a6](https://github.com/moodlehq/wiki-rag/commit/9d308a660d4fc7639f7085b1ed34c604d8767cc0))
- Changelog: Improve fix/feat detection for changelogs by @stronk7 ([c2e88cf](https://github.com/moodlehq/wiki-rag/commit/c2e88cf7cf1bb758e820e58703a0af0f8d9965f0))
- Docs: Amend the future work section with details by @stronk7 ([64f00b9](https://github.com/moodlehq/wiki-rag/commit/64f00b9221693b7849a0d9af666aa762c4e84bfc))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.6.1...v0.6.2

## [0.6.1] - 2025-03-21

### Fixed

- Docker: Provide the full container registry url by @stronk7 ([40c3f3c](https://github.com/moodlehq/wiki-rag/commit/40c3f3cf9543fd27d3cdc086e4e62802de8721f2))
- Environment: Split WRAPPER_MODEL_NAME from COLLECTION_NAME by @stronk7 ([ea86ead](https://github.com/moodlehq/wiki-rag/commit/ea86ead8aef18d13ead6950f80d25b1f8bc16772))
- Install: Make the project PEP 639 compliant by @stronk7 ([6f9b4d2](https://github.com/moodlehq/wiki-rag/commit/6f9b4d228622aa232f995c64a7aea2c7c8a0b4f7))
- Logging: Set the logging level explicitly, before the helper by @stronk7 ([e8e0f96](https://github.com/moodlehq/wiki-rag/commit/e8e0f9696abf6f4a121f11def100403f789ec8d9))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.6.0...v0.6.1

## [0.6.0] - 2025-03-09

### Added

- Develop: Get commit messages and changelogs under control by @stronk7 ([1556f88](https://github.com/moodlehq/wiki-rag/commit/1556f8820f48ae465c0bc0dda00327d9bb35f3da))
- Docs: Automate CHANGELOG.md generation by @stronk7 ([092f094](https://github.com/moodlehq/wiki-rag/commit/092f094e290c03f591a2f1857314a8a4e34d0c5b))
- Release: Automate GitHub releases on tagging by @stronk7 ([d35ea69](https://github.com/moodlehq/wiki-rag/commit/d35ea69496975cb3225c95a604f83ad81b310997))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.6...v0.6.0

## [0.5.6] - 2025-03-08

### Added

- Install: Add support for all-in-one installation with docker compose by @stronk7 ([a8a6a58](https://github.com/moodlehq/wiki-rag/commit/a8a6a585bc19295f5b68438f29f9f76511451c7a))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.5...v0.5.6

## [0.5.5] - 2025-03-08

### Added

- Add OCI annotations that is what ghcr.io registry uses by @stronk7 ([e8c90f6](https://github.com/moodlehq/wiki-rag/commit/e8c90f63f5b110af61a389ecfb6d1e63afbf4e57))
- Add instructions to run it as a docker container by @stronk7 ([1c1f5b4](https://github.com/moodlehq/wiki-rag/commit/1c1f5b46f552470f126d8c90c13a2e519d1a9608))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.4...v0.5.5

## [0.5.4] - 2025-03-08

### Changed

- Split Dockerfile into builder and runner by @stronk7 ([15ccc03](https://github.com/moodlehq/wiki-rag/commit/15ccc03f4ca6640c2193062eeb26ae8d38b5eea2))
- Set PR author as assignee by @stronk7 ([6d43dbf](https://github.com/moodlehq/wiki-rag/commit/6d43dbfe6ddee57a31b0771bd885b849b1b74dde))
- Build the docker images on push (tags & latest) by @stronk7 ([8990608](https://github.com/moodlehq/wiki-rag/commit/89906083e92d1ffff07b636fbc0a87365afe9b80))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.3...v0.5.4

## [0.5.3] - 2025-03-06

### Changed

- Bump dependencies to current + update some link by @stronk7 ([04d9a2d](https://github.com/moodlehq/wiki-rag/commit/04d9a2dbfe81914926d6e62a83100ca74497b112))
- Attempt to create the "data" directory if not present by @stronk7 ([9eb3b5f](https://github.com/moodlehq/wiki-rag/commit/9eb3b5fe14af6aabcb1419748122ff3877103453))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.2...v0.5.3

## [0.5.2] - 2025-03-05

### Added

- Add preliminary env_template file by @stronk7 ([b0db040](https://github.com/moodlehq/wiki-rag/commit/b0db0406a8affbcf0e12cbc2fb8aa985e8a8ffc9))

### Changed

- Fix some project URLs, docs and defaults by @stronk7 ([a328dc8](https://github.com/moodlehq/wiki-rag/commit/a328dc84a7346b9d827e740d6b650469c6b33c73))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.1...v0.5.2

## [0.5.1] - 2025-03-04

### Changed

- Ignore the volumes dir (created by milvus) by @stronk7 ([021fe8f](https://github.com/moodlehq/wiki-rag/commit/021fe8fe6916fff1b143337d901823c25d7f24c5))
- Initial documentation details by @stronk7 ([60ff816](https://github.com/moodlehq/wiki-rag/commit/60ff81640b1d601c1749c8a19b17f0bc7040c5e0))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.5.0...v0.5.1

## [0.5.0] - 2025-03-04

### Added

- Add docker support by @stronk7 ([0ecb2e9](https://github.com/moodlehq/wiki-rag/commit/0ecb2e91b59024cf6ca528e1d148246691dac448))

### Changed

- Few improvements towards better working in a container by @stronk7 ([6e3960d](https://github.com/moodlehq/wiki-rag/commit/6e3960d2ca89ab7e69981b2a75c934e53644c9f8))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.4.1...v0.5.0

## [0.4.1] - 2025-03-03

### Added

- Add support for exclusions by @stronk7 ([454d2bc](https://github.com/moodlehq/wiki-rag/commit/454d2bc244dfd933589239413589c73437f0f4d9))

### Changed

- Small improvements to auth, better logging and caching by @stronk7 ([9a867fc](https://github.com/moodlehq/wiki-rag/commit/9a867fc70eaef4924da3ce1a214bbfd41cea98dd))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.4.0...v0.4.1

## [0.4.0] - 2025-03-02

### Added

- Add authentication to all end-points by @stronk7 ([b8f07f0](https://github.com/moodlehq/wiki-rag/commit/b8f07f0c1718c37abb3e5e68231d6872b3f6df85))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.3.4...v0.4.0

## [0.3.4] - 2025-03-01

### Changed

- Tidy up the local prompt fallback by @stronk7 ([fdf4aa0](https://github.com/moodlehq/wiki-rag/commit/fdf4aa011f551c9126ed9d2179b6ada1880e2489))
- Few improvements to server (globals, responses, deprecations...) by @stronk7 ([204de9c](https://github.com/moodlehq/wiki-rag/commit/204de9cdadee4b0d1db0617c1f229204889d40e3))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.3.3...v0.3.4

## [0.3.3] - 2025-02-27

### Added

- Add page_id to the index and search results for easier tracking by @stronk7 ([dc08e2b](https://github.com/moodlehq/wiki-rag/commit/dc08e2bcd3f0c0e89efe1e316613bb41ba89dcdc))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.3.2...v0.3.3

## [0.3.2] - 2025-02-27

### Changed

- Small changes to sources generation by @stronk7 ([5bde66b](https://github.com/moodlehq/wiki-rag/commit/5bde66b9d189088dad9b4e3a9ff66532b2548e59))
- Make all search / graph operations async by @stronk7 ([a4ba97b](https://github.com/moodlehq/wiki-rag/commit/a4ba97b4add67b2641fff68839677171016b4516))
- Small improvements to prompt handling an others by @stronk7 ([fdd8062](https://github.com/moodlehq/wiki-rag/commit/fdd80629059f7c0e179053cbbdc92a69b1355ade))
- Cache load_prompts_for_rag() by @stronk7 ([202cc73](https://github.com/moodlehq/wiki-rag/commit/202cc73539587b2e3c7f8d33aa49eb4e11659f6d))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.3.1...v0.3.2

## [0.3.1] - 2025-02-24

### Added

- Add basic support to show sources by @stronk7 ([788e3a1](https://github.com/moodlehq/wiki-rag/commit/788e3a19da81db61147853cca0ef8632833c30a6))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.3.0...v0.3.1

## [0.3.0] - 2025-02-24

### Changed

- Move package name from hci to wiki_rag by @stronk7 ([0f30291](https://github.com/moodlehq/wiki-rag/commit/0f3029173656fd9b28a0edb149ebb9e011553045))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.2.1...v0.3.0

## [0.2.1] - 2025-02-24

### Changed

- Coding style (ruff) fixes by @stronk7 ([bf570fa](https://github.com/moodlehq/wiki-rag/commit/bf570fab600d10e32e382d96fb3ba95aa7eebbae))
- Typing (pyright) fixes by @stronk7 ([e101179](https://github.com/moodlehq/wiki-rag/commit/e101179d3bdb8a2a0c52daf0f3c3997f3d8328c7))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.2.0...v0.2.1

## [0.2.0] - 2025-02-22

### Added

- Add basic support for incoming chat history by @stronk7 ([ebd4fd3](https://github.com/moodlehq/wiki-rag/commit/ebd4fd31dd33b6a7092d04497390fbb0002e4511))
- Add basic support for chat history by @stronk7 ([88ddef7](https://github.com/moodlehq/wiki-rag/commit/88ddef7b81efb42e79fa91e64bff849aefa5e93f))

### Changed

- Small adjustments to search (system prompt, checks, ...) by @stronk7 ([70b7a69](https://github.com/moodlehq/wiki-rag/commit/70b7a69b43c9580e723d16e8eacfc724afa80cb6))
- Whitespace fixes by @stronk7 ([9b33cbc](https://github.com/moodlehq/wiki-rag/commit/9b33cbcb2eb1f022ee496be2de9e02d450d013d0))
- First cut of the OpenAi-compatible server by @stronk7 ([73c3878](https://github.com/moodlehq/wiki-rag/commit/73c3878e19a07f75816c2859d648159340ecbc3b))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.1.3...v0.2.0

## [0.1.3] - 2025-02-20

### Added

- Add support for streaming answers in search CLI by @stronk7 ([8573c90](https://github.com/moodlehq/wiki-rag/commit/8573c9078f3e967fa4024b3cf975fb9f7731c656))

### Changed

- Better support the progress when multiple namespaces are processed by @stronk7 ([55e976e](https://github.com/moodlehq/wiki-rag/commit/55e976eaec382a2936d8dd4c62e3cd63b695d3f7))
- By default always index the last (by name) file in the data dir by @stronk7 ([ad06c85](https://github.com/moodlehq/wiki-rag/commit/ad06c8578074febaf2420926dc5c7aa7f4533281))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.1.2...v0.1.3

## [0.1.2] - 2025-02-17

### Changed

- First cut to the search utility by @stronk7 ([b03bf68](https://github.com/moodlehq/wiki-rag/commit/b03bf68e9d6aa1f67349bcdfcbaecd59820357ba))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.1.1...v0.1.2

## [0.1.1] - 2025-02-16

### Changed

- Completed the indexing page by @stronk7 ([4468437](https://github.com/moodlehq/wiki-rag/commit/4468437ad394b39d07dd08e52e3a921fa3d14704))

**Full Changelog**: https://github.com/moodlehq/wiki-rag/compare/v0.1.0...v0.1.1

## [0.1.0] - 2025-02-15

### Changed

- Initial commit, implementing the loader and project basis by @stronk7 ([c1b282a](https://github.com/moodlehq/wiki-rag/commit/c1b282acce3b24cac516df36b6105a0ba05c2945))
- Completed the load phase, results are dump to file by @stronk7 ([a24a644](https://github.com/moodlehq/wiki-rag/commit/a24a644f40584f12ce2a4aea992066cf3713be7a))

### New Contributors 🧡:

- @stronk7 made their first contribution



[unreleased]: https://github.com/moodlehq/wiki-rag/compare/v0.14.0..HEAD
[0.14.0]: https://github.com/moodlehq/wiki-rag/compare/v0.13.1..v0.14.0
[0.13.1]: https://github.com/moodlehq/wiki-rag/compare/v0.13.0..v0.13.1
[0.13.0]: https://github.com/moodlehq/wiki-rag/compare/v0.12.2..v0.13.0
[0.12.2]: https://github.com/moodlehq/wiki-rag/compare/v0.12.1..v0.12.2
[0.12.1]: https://github.com/moodlehq/wiki-rag/compare/v0.12.0..v0.12.1
[0.12.0]: https://github.com/moodlehq/wiki-rag/compare/v0.11.2..v0.12.0
[0.11.2]: https://github.com/moodlehq/wiki-rag/compare/v0.11.1..v0.11.2
[0.11.1]: https://github.com/moodlehq/wiki-rag/compare/v0.11.0..v0.11.1
[0.11.0]: https://github.com/moodlehq/wiki-rag/compare/v0.10.0..v0.11.0
[0.10.0]: https://github.com/moodlehq/wiki-rag/compare/v0.9.1..v0.10.0
[0.9.1]: https://github.com/moodlehq/wiki-rag/compare/v0.9.0..v0.9.1
[0.9.0]: https://github.com/moodlehq/wiki-rag/compare/v0.8.0..v0.9.0
[0.8.0]: https://github.com/moodlehq/wiki-rag/compare/v0.7.1..v0.8.0
[0.7.1]: https://github.com/moodlehq/wiki-rag/compare/v0.7.0..v0.7.1
[0.7.0]: https://github.com/moodlehq/wiki-rag/compare/v0.6.2..v0.7.0
[0.6.2]: https://github.com/moodlehq/wiki-rag/compare/v0.6.1..v0.6.2
[0.6.1]: https://github.com/moodlehq/wiki-rag/compare/v0.6.0..v0.6.1
[0.6.0]: https://github.com/moodlehq/wiki-rag/compare/v0.5.6..v0.6.0
[0.5.6]: https://github.com/moodlehq/wiki-rag/compare/v0.5.5..v0.5.6
[0.5.5]: https://github.com/moodlehq/wiki-rag/compare/v0.5.4..v0.5.5
[0.5.4]: https://github.com/moodlehq/wiki-rag/compare/v0.5.3..v0.5.4
[0.5.3]: https://github.com/moodlehq/wiki-rag/compare/v0.5.2..v0.5.3
[0.5.2]: https://github.com/moodlehq/wiki-rag/compare/v0.5.1..v0.5.2
[0.5.1]: https://github.com/moodlehq/wiki-rag/compare/v0.5.0..v0.5.1
[0.5.0]: https://github.com/moodlehq/wiki-rag/compare/v0.4.1..v0.5.0
[0.4.1]: https://github.com/moodlehq/wiki-rag/compare/v0.4.0..v0.4.1
[0.4.0]: https://github.com/moodlehq/wiki-rag/compare/v0.3.4..v0.4.0
[0.3.4]: https://github.com/moodlehq/wiki-rag/compare/v0.3.3..v0.3.4
[0.3.3]: https://github.com/moodlehq/wiki-rag/compare/v0.3.2..v0.3.3
[0.3.2]: https://github.com/moodlehq/wiki-rag/compare/v0.3.1..v0.3.2
[0.3.1]: https://github.com/moodlehq/wiki-rag/compare/v0.3.0..v0.3.1
[0.3.0]: https://github.com/moodlehq/wiki-rag/compare/v0.2.1..v0.3.0
[0.2.1]: https://github.com/moodlehq/wiki-rag/compare/v0.2.0..v0.2.1
[0.2.0]: https://github.com/moodlehq/wiki-rag/compare/v0.1.3..v0.2.0
[0.1.3]: https://github.com/moodlehq/wiki-rag/compare/v0.1.2..v0.1.3
[0.1.2]: https://github.com/moodlehq/wiki-rag/compare/v0.1.1..v0.1.2
[0.1.1]: https://github.com/moodlehq/wiki-rag/compare/v0.1.0..v0.1.1

<!-- generated by git-cliff -->
