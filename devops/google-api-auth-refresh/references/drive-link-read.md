# Reading a file from a pasted Drive link ("cari tau ini <link>")

When the user pastes a `drive.google.com` link, the job is *identify the file, then read it* —
not to ask them to upload it. The `/preview` URL is HTML and cannot be fetched directly;
go through the API with the token from `google_token.json` (refresh first if `expiry` is past —
a 403 "unregistered callers" is a stale token, not an ACL issue).

## 1. Get the file ID — never invent one

All of these carry the same ID:

```
/file/d/<ID>/preview      /file/d/<ID>/view
open?id=<ID>              document/d/<ID>      drive/folders/<ID>
```

A folder ID is not a file ID: if the resource is a folder, list it
(`files?q='<ID>' in parents`) instead of downloading.

## 2. Metadata first (cheap — tells you what it is before pulling megabytes)

```
GET drive/v3/files/<ID>?fields=id,name,mimeType,size,createdTime,modifiedTime,owners(emailAddress),parents,webViewLink
```

Report name, mimeType, human-readable size, owner, created/modified. A file owned by an
**outside** account is normal for a shared link — `owners[].emailAddress` differing from the
token's account is information to report, not an error.

## 3. Download, then extract by type

```
GET drive/v3/files/<ID>?alt=media   →  save under the scratch dir under a SAFE name
```

Quote any path derived from a Drive filename — real names contain `#`, `&`, `(`, `)`, `'`, and
an unquoted `#` truncates the command. Copy to a safe local name first, then work on that.

| Type | Extract with |
|---|---|
| PDF | `pymupdf`: page count, per-page `get_text()` |
| xlsx / xls | `openpyxl` |
| docx | `python-docx`, or `read_file` auto-extract |
| Google-native (Docs/Sheets/Slides) | export endpoint `files/<ID>/export?mimeType=...`, NOT `alt=media` |

Sanity check before quoting: report **page count and character count**. A long PDF that yields
~0 characters is a scanned image needing OCR — say that, do not report it as "empty".

## 4. Report order (this is what the user actually wants)

1. **Identity block first** — name, size, pages, owner, created/modified, type. Never bury this
   under a summary; the literal question is "what is this file".
2. **One line: what the document is** (vendor module doc, contract, invoice, spec...).
3. **Structure** — follow the document's own sections/TOC, condensing each. Quote exact numbers,
   names, IDs and figures; those are why the user could not read it themselves.
4. **Detail worth flagging** — duplicated or garbled text, missing signatures/dates,
   contradictions between sections.
5. **Relevance to the user's business + 2–3 concrete next options** as a short A/B/C list.

If the document is a vendor/module manual for the user's own platform, end by offering:
(A) turn it into a 1-page SOP, (B) check whether the feature is already live in our panel,
(C) risk analysis. That matches how this user consumes vendor docs.
