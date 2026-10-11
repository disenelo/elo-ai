# FROM BUILDER 3 → Builder 1: execution-ack dependency, document writing takes ~25 s

Card WO-B3-0009 (documents, `tools/document_writer.py`, a84dbe2) is a direct answer in `tools/tool_router._direct_intercepts`. Writing a document takes **~25 s** (local model; measured 2026-10-09), and during that time eLo says nothing.

When your execution-acknowledgement pattern ships (WO-B1-0108 / inner-thought ack: "give me a second, I'll write that up"), please account for this capability:
- **Trigger:** `tools.document_writer.is_document_request(text)` is True (e.g. "make me a list of…", "write that up", "create a doc…").
- **Ack before:** a short eLo line before the write starts.
- **Then:** the existing result line ("Done — I wrote it up: “<title>”, saved in ~/Documents/eLo as <file>.").

Same need, smaller: device commands (`tools/device_control`, a few seconds) and Spotify play (a few seconds).
Tell B3 the hook (function/flag) and B3 will call it from the document path.
