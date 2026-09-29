# Little List

A shared to-do app built with React, Python/FastAPI, and SQLite.

## Open the app on this computer

1. Double-click **Start Little List.cmd** in this folder.
2. Your browser opens at **http://127.0.0.1:8000**.
3. Keep the command window open while using the app. Press **Ctrl+C** in that window to stop it.

If the app is already running, just visit the address above. If you see “address already in use,” close the extra launcher and use the running app.

## Using it

- Enter a task title, optionally add details and a due date, then click **Add task**.
- Tick the checkbox to complete a task; untick it to reopen it.
- Click a task's title or pencil to edit it. Clear the date field to remove a due date.
- Drag the dotted handle onto another item, or use the up/down arrows to reorder.
- Open **Notes** for separate notes with titles and text.
- Click **×** to delete an item; you will be asked to confirm.
- Every successful save is stored in SQLite. Reloading or restarting keeps your data.

Due dates are labels with an overdue indicator; they do not send notifications.

## Your data

Your tasks and notes are in `data/todo.sqlite3`. To back up your data, stop the app and copy that file somewhere safe. Keep the `data` folder when updating the source.

The local launcher listens only on this computer and works offline after setup. Once deployed online, everyone can view and edit the same list without a password. Other visitors see changes when they refresh or perform an action.

## How the parts fit together

- `frontend/src/main.jsx`: React interface and button actions.
- `frontend/src/style.css`: colors, spacing, and mobile layout.
- `backend/main.py`: FastAPI routes and SQLite queries.
- `frontend/dist`: ready-to-use browser files.
- `run.py`: starts the server and opens the browser.
- `test_app.py`: checks saving, editing, ordering, validation, and persistence with a temporary database.

The browser sends requests to FastAPI. FastAPI reads or writes SQLite and sends the results back. FastAPI also serves the built React interface, so you only need one running server.

## Set up on another computer

Install Python 3.12+ and Node.js 22.12+. In a terminal opened in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The included `frontend/dist` is already built, so Node.js is only needed when changing the frontend. Double-click the launcher to run the app.

For frontend changes, install pnpm and run:

```powershell
cd frontend
pnpm install
pnpm run build
cd ..
```

Restart the app after rebuilding. For live frontend development, start the backend, then run `pnpm run dev` in `frontend` and use the Vite URL shown in the terminal.

## Verify

From this folder:

```powershell
.\.venv\Scripts\python.exe -m unittest test_app -v
```

API documentation is available at http://127.0.0.1:8000/docs while running.

## Deploy online

See **DEPLOY-VERCEL.md** for the beginner deployment guide. Online hosting uses PostgreSQL through the private server environment variable `DATABASE_URL`. All task and note endpoints allow public editing without authentication. `APP_PASSWORD` is no longer used. Local mode continues using SQLite when `DATABASE_URL` is not set. Vercel requires a database URL to prevent accidental use of temporary local storage.

Environment variables must be set in the process or hosting dashboard; `.env.example` is documentation and is not loaded automatically.
