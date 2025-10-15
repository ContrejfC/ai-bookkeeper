# How to Get Your Production DATABASE_URL

## Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com
2. Sign in to your account

## Step 2: Find Your Database
1. Look for your PostgreSQL database service
2. It should be named something like "ai-bookkeeper-db" or similar
3. Click on it

## Step 3: Get the Connection String
1. Go to the "Info" tab
2. Look for "External Database URL" or "Connection String"
3. Copy the entire URL (it will look like: `postgresql://username:password@host:port/database`)

## Step 4: Run the Script
```bash
# Set the environment variable
export DATABASE_URL='your_database_url_here'

# Run the script
python create_production_admin.py
```

## Alternative: Use Render Shell
If you can't find the DATABASE_URL, you can also:
1. Go to your web service (ai-bookkeeper-web)
2. Click on "Shell" tab
3. Run the script directly in the Render environment

## What the Script Does
- Creates an admin user with email: `admin@example.com`
- Password: `admin123`
- Role: `owner`
- Enables Dev Magic Link login

## After Running
You'll be able to login at:
https://ai-bookkeeper-nine.vercel.app/login

Using either:
- Email: admin@example.com, Password: admin123
- OR Dev Magic Link with admin@example.com
