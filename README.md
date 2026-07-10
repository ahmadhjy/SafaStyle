# Safa Style — Django storefront

Modern, fast replacement for the WordPress/WooCommerce site.

## Quick start (local)

```powershell
cd "C:\Users\ME\Desktop\Safa Style"
.\djangoenv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_store
python manage.py runserver
```

- Storefront: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Deploy to production (DigitalOcean)

### What is SSH?

**SSH** is how your PC opens a remote terminal on the droplet. In PowerShell:

```powershell
ssh root@209.38.211.102
```

You'll be asked for the droplet password (from DigitalOcean email) or it connects automatically if you added an SSH key when creating the droplet. The DigitalOcean **web console** (browser terminal) is the same thing — SSH is just faster from Cursor.

### One-time server setup

1. **Push this repo to GitHub** (including the new `deploy/` folder):

   ```powershell
   git add .
   git commit -m "Add deployment scripts"
   git push origin main
   ```

2. **Copy deploy config** (already done if `deploy.config` exists):

   ```powershell
   copy deploy.config.example deploy.config
   ```

3. **Run setup from your PC** (installs Nginx, PostgreSQL, Gunicorn, SSL):

   ```powershell
   .\deploy.ps1 -Setup
   ```

   Or paste `deploy/setup-server.sh` into the DigitalOcean web console.

4. **Create admin user** on the server:

   ```powershell
   ssh root@209.38.211.102
   cd /var/www/safastyle
   ./venv/bin/python manage.py createsuperuser
   ```

5. **Edit email password** on the server:

   ```powershell
   nano /var/www/safastyle/.env
   # Set EMAIL_HOST_PASSWORD=...
   systemctl restart gunicorn-safastyle
   ```

### Every update (one command)

After you change code locally:

```powershell
git add .
git commit -m "Describe your change"
git push origin main
.\deploy.ps1
```

That SSHs into the droplet, runs `git pull`, migrates, collects static files, and restarts Gunicorn.

Check status:

```powershell
.\deploy.ps1 -Status
```

### DNS (already configured)

| Record | Value |
|--------|-------|
| A `@` | `209.38.211.102` |
| A `www` | `209.38.211.102` |
| MX / SPF / DKIM | unchanged (IONOS mail) |

## Launch catalog

```powershell
python manage.py prepare_launch
```

On the server this imports 10 products from safastyle.com (when reachable), optimizes images, and sets category photos.

## Data entry (variations)

1. Create/select **Colors** and **Sizes**
2. On a **Product**: set base price, pick available colors & sizes
3. Upload **images** — assign each image to a **color**
4. Variations tab → **Generate variations**
5. Set **price / sale price / stock** per row (or use bulk editor)
