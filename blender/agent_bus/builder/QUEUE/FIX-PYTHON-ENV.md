# FIX: Python environment — repo default has no yaml

**Priority:** Quick fix — run before next test suite

`/opt/homebrew/bin/python3` is missing `yaml` and `astral`. All seats need a consistent Python.

```bash
/opt/homebrew/bin/pip3 install pyyaml astral --break-system-packages
```

Then verify:
```bash
/opt/homebrew/bin/python3 -c "import yaml; import astral; print('OK')"
```

If that passes, the repo default python3 works for all seats. No config change needed.

If it fails, add to `.env`:
```
PYTHON=/Users/Disenelo/miniconda3/bin/python3
```

Evidence: one line — output of the verify command.

---

## BUILDER RESULT

**Status:** DONE — Python env verified working  
**Date:** 2026-09-27

Ran: `/opt/homebrew/bin/python3 -c "import yaml; import astral; print('OK')"`  
Output: `OK`

Both `pyyaml` and `astral` are installed at `/opt/homebrew/bin/python3`. No `.env` change needed. All seats can use repo default python3.

**Board action:** Close WO.
