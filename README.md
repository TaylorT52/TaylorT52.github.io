### me.taylortam.com

## Summer Page Studio

The Summer Projects page has a local-only editor for adding new projects,
writing updates, attaching photos, previewing the result, and publishing to
GitHub Pages. Newly added projects appear above the older project sections and
automatically become available in the update editor.

From this repository, run:

```sh
./manage-summer
```

Open the private localhost link printed in the terminal. Drafts are written to
`data/summer-updates.json`; the **Publish to website** button commits only the
summer-page files and pushes them to `main`.

The server listens on `127.0.0.1`, so it is not reachable from another computer.
It also requires a random per-computer token stored in
`.summer-portal-token`, which is excluded from Git. Publishing uses this
computer's existing Git credentials. Press Control-C in the terminal to stop
the portal.
