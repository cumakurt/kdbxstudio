# Lessons

## Code quality (2026-07-17)

- Never check `Path.is_symlink()` after `resolve()` — resolve follows links; reject symlinks first.
- Recycle Bin emptying must walk subgroups; KeePass trashes groups as nested folders under the bin.
- Lock/close paths must treat dirty sessions like quit: save or confirm before discarding memory state.
- Merge and history restore must copy the full entry surface (expiry, OTP including empty, attachments, tags, custom props), not only the obvious string fields.
- Attachment UX: same guards for DnD and file dialog; always use `Path(name).name` for stored/default filenames.
