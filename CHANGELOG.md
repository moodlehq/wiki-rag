# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
and commits should be formatted using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

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
