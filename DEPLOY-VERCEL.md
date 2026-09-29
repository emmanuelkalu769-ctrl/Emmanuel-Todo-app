# Deploy Little List with public editing

Everyone who opens the live app can view, add, edit, complete, reorder, and delete the same tasks and notes. There is no password or separate user account.

## 1. Upload the updated app

1. Extract `Little-List-Vercel.zip` from this chat.
2. In GitHub Desktop, select `Emmanuel-Todo-app`, then choose **Repository → Show in Explorer**.
3. Copy the extracted CONTENTS into that repository folder, replacing matching files. Keep your `.git` and `data` folders.
4. In GitHub Desktop, enter `Enable public editing`, click **Commit to main**, then **Push origin**.
5. In GitHub's **Actions** tab, check that **App checks** passes. It tests both SQLite and a disposable PostgreSQL database.

The repository root should contain `app.py`, `vercel.json`, `requirements.txt`, `backend`, and `frontend`.

## 2. Create the online database

If you already created Neon, keep using that database.

Otherwise, sign up at https://neon.com, create a project, and copy its pooled PostgreSQL connection string from **Connect**. Keep the complete string, including `sslmode=require`, private. Review any plan costs before selecting a plan.

The online list starts empty unless it already has online data. Your computer's SQLite tasks are not automatically uploaded.

## 3. Deploy with Vercel

1. Go to https://vercel.com/new, sign in with GitHub, and import `Emmanuel-Todo-app`.
2. Keep **Root Directory** at the repository root, not `frontend`.
3. Use the **FastAPI** framework. The included configuration supplies the build command; leave the output directory at its default.
4. Add the environment variable **DATABASE_URL** with the private Neon connection string. Do not prefix it with `VITE_` or put it into GitHub.
5. No **APP_PASSWORD** is needed. Remove that old variable if you previously added it; the new code ignores it.
6. Click **Deploy** and open the production `.vercel.app` URL. If the project was already connected, pushing to its production branch triggers deployment.

If Vercel itself asks visitors to sign in, check the project's **Settings → Deployment Protection** and ensure the production deployment allows public access. The app has no login, but Vercel's platform protection is a separate setting. Share the production domain, not a protected preview URL.

Use a separate database for Preview deployments if you enable them so preview changes do not modify the production list.

## 4. Verify the live app

1. Open the production URL in a private/incognito window. No app password should be requested.
2. Add two disposable tasks with notes and dates, then complete, edit, and reorder them.
3. Open the URL in a second browser and refresh. The same list should appear, and that visitor should be able to edit it.
4. Add a note, reload, and confirm it persists.
5. Delete only your disposable test items and confirm deletion persists after reloading.

Changes appear after an action or page refresh; this version does not push live updates into other visitors' open tabs.

## Troubleshooting

- **Setup incomplete**: set DATABASE_URL in Vercel and redeploy.
- **Server error**: confirm Neon is active and its connection string was copied completely.
- **Build failed**: share the error text from Vercel's build log, removing any secrets.

## Validation

Local endpoint tests cover public access from different visitors, CRUD, completion, dates, ordering, validation, and persistence. GitHub Actions also runs these tests against a disposable PostgreSQL service. Actual hosted connectivity and public Vercel access must be checked after deployment.
