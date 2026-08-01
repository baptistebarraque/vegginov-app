# FlavorGraph ingredient embeddings

Not committed to git (external asset, see `.gitignore`). Used by
`matching/flavorgraph.py` for the ingredients-view similarity (Phase 2).

Source: https://github.com/lamypark/FlavorGraph (Apache 2.0 license).

Place these two files directly in this directory:

- `embeddings.pickle` — the pretrained node embeddings (300-dim, ~6653
  ingredients), downloaded from the Google Drive link in the FlavorGraph
  repo's README (not hosted in the repo itself). Format: a pickled dict
  `{node_id (str): numpy vector(300,)}`.
- `nodes.csv` — the repo's `input/nodes_191120.csv`, mapping `name` /
  `node_id` / `node_type` (`ingredient` or `compound` — only `ingredient`
  rows are used).

Rename the downloaded files to match the two names above.
