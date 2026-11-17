---
name: box-com-api
description: Use when connecting to or managing Box.com cloud storage.
---

# Box.com API Integration (boxsdk)

Connect Hermes to Box.com cloud storage: CCG auth, folder/file management, sharing.

## Auth: Client Credentials Grant (CCG) — server-to-server

1. Developer Console (cloud.app.box.com/developers/console) → New App → **Custom App** → **Server Authentication** → **Client Credentials Grant** (RECOMMENDED badge; JWT only for strict enterprise policies).
2. App must be **Authorized** — free developer accounts auto-approve after **Submit App**. While status is "Not Submitted", CCG returns `unauthorized_client: The box_subject_type value is unauthorized for this client_id`.
3. Grab Client ID + Client Secret (App Details → Access → "Fetch Secret").
4. Get Enterprise ID: `GET /2.0/users/me` with a developer token → `enterprise.id` (free accounts often have it).
5. CCG requires `enterprise_id`; without it: `invalid_request: box_subject_id cannot be used without a box_subject_type`. With `box_subject_type=enterprise&box_subject_id=<enterprise_id>` the token exchange succeeds.

## SDK (boxsdk>=10, generated SDK) — exact signatures matter

```python
from box_sdk_gen import BoxClient, BoxCCGAuth, CCGConfig
from box_sdk_gen.managers.folders import CreateFolderParent
from box_sdk_gen.managers.uploads import UploadFileAttributes, UploadFileAttributesParentField

cfg = CCGConfig(client_id=ID, client_secret=SECRET, enterprise_id=ENTERPRISE_ID)
client = BoxClient(auth=BoxCCGAuth(cfg))

# Buat folder
folder = client.folders.create_folder(name="x", parent=CreateFolderParent(id="0"))

# Upload file
with open(path, "rb") as f:
    up = client.uploads.upload_file(
        attributes=UploadFileAttributes(name="f.pdf", parent=UploadFileAttributesParentField(id=folder_id)),
        file=f,
    )

# List isi folder
items = client.folders.get_folder_items("0")   # .entries

# Share ke email user (biar kelihatan di akun pribadi mereka)
client.user_collaborations.create_collaboration(
    item={"id": folder_id, "type": "folder"},
    accessible_by={"login": "email@example.com", "type": "user"},
    role="co-owner",
)
```

Class names: `BoxCCGAuth`/`CCGConfig` (NOT BoxCcgAuth). Manager accessors are instance attributes (`client.folders`, `client.uploads`, `client.user_collaborations`), not methods — `dir(client)` on an instance reveals them; class-level `dir` shows only `make_request` etc.

## Key quirks & pitfalls

- **Service Account vs user account**: files created by CCG live under the app's Service Account ("AutomationUser..."), NOT the personal Box account — invisible in the owner's web UI until the folder is shared to their email (create_collaboration, role co-owner).
- **Developer tokens expire in 1 hour** — use CCG for anything persistent.
- Single upload limit 50 MB; larger needs chunked upload APIs.
- 409/SAME_NAME on folder create → folder exists; find its id by listing parent entries and matching name instead of erroring out.
- Webhooks/signature keys not needed for basic upload/backup flows.
- Credentials should be stored in a dedicated config file (e.g. `box.conf`), not echoed in logs.

## Verify connection

List root items and confirm `entries` length; then upload a tiny file and re-list to confirm it landed before reporting success to the user.
