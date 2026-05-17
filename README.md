# datasets_hub

Python library for uploading HuggingFace `datasets` to lakeFS. **Every commit is automatically tied to your validation profile** when `lakefs_validation.json` is present.

## End-to-end flow

```
Your project/lakefs_validation.json
        ↓
datasets_hub.push_to_hub()  →  sync profile to validation service
        ↓                      inject metadata: profile=my_project_v1
lakeFS pre-commit hook      →  validation service runs checks
        ↓
Commit allowed (200) or blocked (400 + errors)
```

## Setup (one time per environment)

### 1. Configure lakeFS

```powershell
copy .env.example .env
# Set LAKEFS_HOST, LAKEFS_USERNAME, LAKEFS_PASSWORD, LAKEFS_STORAGE_NAMESPACE
```

### 2. Run the validation service

```powershell
cd ..\validation_service
copy .env.example .env
pip install -r requirements.txt
python -m validation_service.main
```

### 3. Point datasets_hub at the service

In `datasets_hub/.env`:

```env
DATASETS_HUB_VALIDATION_SERVICE_URL=http://localhost:8080
```

### 4. Install the lakeFS action

Copy `../validation_service/examples/_lakefs_actions/validate_on_commit.yaml` into each lakeFS repository under `_lakefs_actions/`.

## Per-project validation (user workflow)

1. **Automatic (recommended):** run `push_to_hub()` once — if `lakefs_validation.json` is missing, `datasets_hub` creates a commented template linked to the bundled JSON Schema (IDE tooltips + validation).
2. Or scaffold manually: `from datasets_hub import init_validation_profile; init_validation_profile()`.
3. Edit `profile_id` and `steps` for your domain (NER, audio, text, etc.).
4. Push data as usual — validation is automatic:

```python
from datasets import Dataset
from datasets_hub import LFSDataset

ds = LFSDataset.from_dataset(Dataset.from_dict({"text": ["hello"], "label": [1]}))
ds.push_to_hub(
    repo_id="my-dataset",
    revision="feature/add-data",
    commit_message="add training split",
    file_type="parquet",
)
```

The library will:

- Load `lakefs_validation.json` from the current directory (walks up to 6 parent dirs).
- `POST` the profile to `{VALIDATION_SERVICE_URL}/registry/profiles`.
- Set commit metadata `profile=<profile_id>`.
- Upload a copy to `.lakefs/validation.json` in the repo.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASETS_HUB_VALIDATION_ENABLED` | `true` | Attach validation metadata on commit |
| `DATASETS_HUB_VALIDATION_REQUIRED` | `true` | Fail if `lakefs_validation.json` is missing |
| `DATASETS_HUB_VALIDATION_PROFILE_FILENAME` | `lakefs_validation.json` | Profile file name |
| `DATASETS_HUB_VALIDATION_SERVICE_URL` | — | Validation service base URL |
| `DATASETS_HUB_VALIDATION_SYNC_ON_COMMIT` | `true` | Register profile before commit |
| `DATASETS_HUB_VALIDATION_REGISTRY_API_KEY` | — | Matches `VALIDATION_REGISTRY_API_KEY` |
| `DATASETS_HUB_VALIDATION_METADATA_KEY` | `profile` | Commit metadata key |
| `DATASETS_HUB_VALIDATION_AUTO_SCAFFOLD` | `true` | Create `lakefs_validation.json` when missing |
| `DATASETS_HUB_VALIDATION_SCHEMA_URL` | — | HTTPS schema URL for teams (optional) |
| `LAKEFS_HOST` | `http://localhost:8000` | lakeFS endpoint |
| `LAKEFS_USERNAME` / `LAKEFS_PASSWORD` | — | Credentials |

Disable validation for a single call: `skip_validation=True`.

## IDE autocompletion (Vite-style — rules separate from editor wiring)

`lakefs_validation.json` contains **only validation rules** (no `$schema` link).

On scaffold, `datasets_hub` configures the editor like Vite does for its config:

| File | Role |
|------|------|
| `lakefs_validation.json` | Your rules (what you edit) |
| `.vscode/settings.json` | Maps the file to JSON Schema (auto-merged) |
| `.lakefs/lakefs_validation.schema.json` | Tooling copy of the schema (auto-synced) |

VS Code / Cursor read `json.schemas` from workspace settings — you get tooltips and error highlighting without schema noise in the config file.

Disable IDE wiring: `DATASETS_HUB_VALIDATION_IDE_SETUP=false`  
Team HTTPS schema: `DATASETS_HUB_VALIDATION_SCHEMA_URL=https://…`

## Example profile

See `examples/lakefs_validation.json` and `../validation_service/registry/` for templates.
