# Wiki-RAG

**Wiki-RAG (Mediawiki Retrieval-Augmented Generation)** is a project that leverages Mediawiki as a source for augmenting text generation tasks, enhancing the quality and relevance of generated content.

## Summary

Wiki-RAG integrates Mediawiki's structured knowledge (ingested via [API](https://www.mediawiki.org/wiki/API:Main_page)) with language models to improve text generation. By using retrieval-augmented generation and some interesting techniques, it provides more contextually relevant and accurate responses using any Mediawiki site as KB.

Labeled as an experimental project, Wiki-RAG is part of the [Moodle Research](https://moodle.org/course/view.php?id=17254) initiative, aiming to explore and develop innovative solutions for the educational technology sector.

## Requirements

To get started with Wiki-RAG, ensure you have the following:

- Git
- Python 3.12 or later with pip (Python package installer)
- [Docker](https://www.docker.com/get-started) (if you intend to run the project using Docker)
- [Milvus 2.6.2](https://milvus.io/docs/release_notes.md) or later (for vector similarity search). Standalone or Distributed deployments are supported. Lite deployments are not supported. It's highly recommended to use the [Docker Compose deployment](https://milvus.io/docs/install_standalone-docker-compose.md) specially for testing and development purposes.

## Configuration

1. **Create `config.yml`** (non-secret settings):
   - Using the [config template](config.yml.template) as source, create a new `config.yml` file:
     ```bash
     cp config.yml.template config.yml
     ```
   - Edit it to suit your needs (mediawiki sites and namespaces, models, search parameters, etc.)

2. **Create `.env`** (secrets only):
   - Using the [env template](dotenv.template) as source, create a new `.env` file:
     ```bash
     cp dotenv.template .env
     ```
   - Edit it to fill in API keys, tokens and other secrets.

> **Upgrading from an older `.env`-only setup?** All non-secret settings (model names, URLs,
> search parameters, etc.) have moved to `config.yml`. Run `python scripts/generate-config.py` to
> generate a `config.yml` pre-populated from your existing `.env` — then remove those non-secret
> variables from `.env` and keep only the secrets listed in `dotenv.template`.

## Installation

### Running Locally

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/moodlehq/wiki-rag.git
   cd wiki-rag
   ```

2. **Set Up Virtual Environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -e .
   ```
   If interested into [contributing](CONTRIBUTING.md) to the project, you can install the development dependencies and enable all the checks by running:
   ```bash
   pip install -e .[dev]  # To install all the development dependencies.
   pre-commit install     # To enable all the check (style, lint, commits, etc.)
   ```


4. **Run the Application**:
   The application comes with four different executables:
   - `wr-load`: Will parse all the configured pages in the source Mediawiki site, extracting contents and other important metadata. All the generated information will be stored into a JSON file in the `data` directory. Supports `--incremental` mode to only re-fetch changed pages since a previous dump.
   - `wr-index`: In charge of creating (or incrementally updating) the collection in the vector index (Milvus) with all the information extracted in the previous step. Automatically uses incremental mode for incremental dumps; use `--full` to force a full reindex.
   - `wr-search`: A tiny CLI utility to perform searches against the RAG system from the command line.
   - `wr-server`: A comprehensive and secure web service (documented with OpenAPI) that allows users to interact with the RAG system using the OpenAI API (`v1/models` and `v1/chat/completions` endpoints) as if it were a large language model (LLM). Protected with bearer tokens (local list via `AUTH_TOKENS` and/or remote delegation via `AUTH_URL`). Supports streaming responses.
   - `wr-mcp`: A complete built-in MCP server that allows you to access to various parts of Wiki-RAG like prompts (system and use prompt with placeholders), resources (access to the source parsed documents) and tools (retrieve, optimise and generate) using the [MCP Protocol](https://modelcontextprotocol.io/). Uses the same authentication schema as `wr-server`.
   - `wr-cleanup.sh`: A standalone Bash script to prune old dump files. Run `./scripts/wr-cleanup.sh --help` for full usage.

### Running with Docker (Milvus elsewhere)

1. Pull the image from GitHub [Container Registry](https://github.com/moodlehq/wiki-rag/pkgs/container/wiki-rag):
   ```bash
   docker pull ghcr.io/moodlehq/wiki-rag:latest  # or specify a tag
   ```

2. Run the container:
   - **Note 1:** `config.yml` (non-secret settings) is required and must be mounted. Secrets can be supplied either via a `.env` file (mounted as shown) or as plain `--env` flags — use whichever suits your deployment.
   - **Note 2:** The `data` directory will be created in the current directory, and it will store all the data generated by the `wr-load` command. If the `LOADER_DUMP_PATH` is set, you will have to change the volume mapping accordingly.
   ```bash
   docker run --rm --detach \
       --volume $(pwd)/data:/app/data \
       --volume $(pwd)/config.yml:/app/config.yml \
       --volume $(pwd)/.env:/app/.env \
       --env MILVUS_URL=http://milvus-standalone:19530 \
       --network milvus \
       --publish 8080:8080 \
       --env OPENAI_API_KEY=YOUR_OPENAI_API_KEY \
       --env LOG_LEVEL=info \
       --name wiki-rag \
       wiki-rag:latest
   ```
   - **Note 3:** The command above will start the `wr-server` automatically, listening on the configured port (8080) and the `OPENAI_API_KEY` is required to interact with the embedding and LLM models. If, instead, you want to execute any of the other commands (`wr-load`, `wr-index`, `wr-search`), you can specify it as the last argument.
   - **Note 4:** The 2 lines related to Milvus are required to connect to the Milvus server **if also running in Docker**. If it's running elsewhere, you can replace the `MILVUS_URL` with the appropriate URL or configure it in the `.env` file instead
   - **Note 5:** You can use `docker logs wiki-rag` to check the logs of the running container (`wr-server` logs).
   - **Note 6:** When running the `wr-server`, you still can execute any of the commands (`wr-load`, `wr-index`, `wr-search`) using `docker exec -it wiki-rag <command>`.
   - **Note 7:** To stop and remove the container, you can use `docker stop wiki-rag`.

### Running with Docker Compose (all-in-one)

1. Download the Milvus Docker Compose file:
   ```bash
   wget https://github.com/milvus-io/milvus/releases/download/v2.6.2/milvus-standalone-docker-compose.yml -O milvus-standalone.yml
   ```
   OR
   ```bash
   curl https://github.com/milvus-io/milvus/releases/download/v2.6.2/milvus-standalone-docker-compose.yml -o milvus-standalone.yml
   ```

2. Run Wiki-RAG own Docker Compose file:
   - **Note 1:** `config.yml` (non-secret settings) is required and must be present in the same directory. Secrets can be supplied via a `.env` file or as environment variables in your compose override — use whichever suits your deployment.
   - **Note 2:** The `data` directory will be created in the current directory, and it will store all the data generated by the `wr-load` command. If the `LOADER_DUMP_PATH` is set, you will have to change the volume mapping accordingly.
   - **Note 3:** The `volumes` directory will be created in the current directory, and it will store all the data required by the Milvus containers.
   ```bash
   docker compose up -d
   ```
   - **Note 4:** Some useful commands include:
     - To stop all the containers, you can use `docker compose stop`.
     - To start again all the containers, you can use `docker compose start`.
     - To stop and remove all the containers, you can use `docker compose down`.
   - **Note 5:** You can use `docker logs wiki-rag` to check the logs of the running container (`wr-server` logs).
    - **Note 6:** When running, you still can execute any of the commands (`wr-load`, `wr-index`, `wr-search`) using `docker exec -it wiki-rag <command>`.

## Features

   * Accepts virtually any Mediawiki site as a knowledge base (KB).
   * Uses Mediawiki API to extract content and metadata (not web crawling).
   * Supports multiple namespaces and page exclusions.
   * The whole KB is stored in a (dated) JSON file for later use, access and analysis.
   * Supports incremental loading and indexing, processing only changed pages since a previous dump.
   * Metadata-rich information containing parent-ship relations, sources and other useful information.
   * Loads the KB into a vector database (Milvus) for fast retrieval.
   * Hybrid retrieval using both vector and keyword search with fusion reranking.
   * Contextual-aware query rewrite for a better chat experience.
   * Optional HyDE (Hypothetical Document Embeddings) support, with configurable number of passages.
   * Support for chit-chatting cases, avoiding out-of-scope questions (limited but effective).
   * Performs post-retrieval optimisations to improve the quality of the retrieved documents:
       * POP (popularity): In charge of boosting the most popular chunks.
       * POC (parent, own and child): Add those related chunks to the retrieved ones.
   * Many configuration options:
       * Models to use for embeddings, query rewrite and answers generation (any OpenAI compatible provider).
       * Size (in messages count and tokens length) to use as history.
       * Other settings (embed dimensions, chunk size, etc.)
   * Supports (opt-in) observability (tracing) with both LangSmith and Langfuse.
   * Prompts management (also opt-in) with LangSmith and Langfuse. Defaults apply otherwise.
   * Uses LangGraph for orchestration of the whole LLM pipeline.
   * Exposed as a model using standard OpenAI API endpoints (`v1/models` and `v1/chat/completions`). Protected with bearer tokens (local list via `AUTH_TOKENS` and/or remote delegation via `AUTH_URL`). Supports streaming responses.
   * Exposed as a MCP server (Model Context Protocol) with all the required endpoints (prompts, resources and tools). Using the same authentication schema as the HTTP server.
   * Plenty of ideas for future work and improvements (see next section).

## Future Work

   ~~[support partial/incremental loading](https://github.com/moodlehq/wiki-rag/commit/63ced69)~~ /
   ~~[support partial/incremental indexing](https://github.com/moodlehq/wiki-rag/commit/ccd4c4a)~~ /
   process multiple mediawiki sites /
   process other sites (docusaurus, ...) /
   more granular splits /
   loaders to become plugins /
   [use markdown as "backend format"](https://github.com/moodlehq/wiki-rag/issues/5) /
   ~~[include/exclude lists](https://github.com/moodlehq/wiki-rag/commit/454d2bc244dfd933589239413589c73437f0f4d9)~~ /
   compare results with different embeddings /
   fine tune the embedding /
   support adding a watermark text to the responses /
   consider adding summaries, multiple levels and more metadata /
   [able to use other vector databases](https://github.com/moodlehq/wiki-rag/issues/3) /
   add other algos, apart from current POP and POC /
   support multi-level searches /
   ~~[context-aware rag](https://github.com/moodlehq/wiki-rag/commit/77cac73469da7c07710851be51321b13e1c923fc)~~ /
   ~~[HyDE support](https://github.com/moodlehq/wiki-rag/commit/0548728290ddf5e6374a053fc4f0f1759206c3e7)~~ /
   extra querying techniques /
   prepare an evaluation collection /
   apply thresholds to results /
   better Open AI implementation, supporting more parameters /
   add supports to the Responses Open AI API /
   ~~[better prompt management](https://github.com/moodlehq/wiki-rag/commit/2d6127f308fa7da21908f94818108cde59e39076)~~ /
   ~~[observability alternatives (langfuse, ...)](https://github.com/moodlehq/wiki-rag/commit/2f1be65900255d837bb8d4bf913a4a557cd2f404)~~ /
   context-size control /
   add guardrails at different levels /
   ~~[move configuration away from env file](https://github.com/moodlehq/wiki-rag/issues/2)~~ /
   better fit in multi-agentic environments /
   detect out of scope questions better /
   semantic routing /
   ~~[support MCP (model context protocol)](https://github.com/moodlehq/wiki-rag/issues/4)~~ /
   protected (bearer token) MCP server /
   make everything pluggable /
   add unit and integration tests /
   automate checks and releases

## Documentation

For more detailed information, please refer to the following files:

- [License](LICENSE)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for more information.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

---
© 2025 Moodle Research Team
