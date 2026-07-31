# docs/

Sample PriceLabs-inspired knowledge base for RAG demos (18 markdown documents).

Each file includes YAML frontmatter:

- `document_id`, `title`, `category`, `last_updated`, `version`, `tags`

Ingestion reads this directory via `IngestionService` (CLI or `POST /api/ingest`).
`README.md` in this folder is skipped during discovery.
