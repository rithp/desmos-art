# 🚀 Free Deployment Guide for Image to Desmos Converter

This guide will walk you through deploying your web app for free using various platforms.

## Option 1: Render (Recommended - Easiest)

Render offers free hosting for web applications with automatic deployments from GitHub.

### Step-by-Step Instructions:

1. **Prepare Your Repository**
   - Make sure all your code is pushed to GitHub
   - You should already have this done!

2. **Create Required Files**
   
   Create a `requirements.txt` file (if not already present):
   ```
   Flask>=3.0.0
   Werkzeug>=3.0.0
   opencv-python-headless
   numpy
   scipy
   matplotlib
   Pillow
   gunicorn
   ```
   
   **Important**: Use `opencv-python-headless` instead of `opencv-python` for deployment (no GUI dependencies).

3. **Create a `render.yaml` file** (optional but recommended):
   ```yaml
   services:
     - type: web
       name: desmos-art-converter
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn app:app
       envVars:
         - key: PYTHON_VERSION
           value: 3.9.6
   ```

4. **Update `app.py` for Production**
   
   Change the last lines from:
   ```python
   if __name__ == '__main__':
       app.run(debug=True, port=5000)
   ```
   
   To:
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(host='0.0.0.0', port=port, debug=False)
   ```

5. **Sign Up and Deploy on Render**
   
   a. Go to [render.com](https://render.com) and sign up (free)
   
   b. Click "New +" → "Web Service"
   
   c. Connect your GitHub account and select your `desmos-art` repository
   
   d. Configure the service:
      - **Name**: `desmos-art-converter` (or any name you like)
      - **Environment**: `Python 3`
      - **Build Command**: `pip install -r requirements.txt`
      - **Start Command**: `gunicorn app:app`
      - **Plan**: Select "Free"
   
   e. Click "Create Web Service"
   
   f. Wait 5-10 minutes for the initial deployment
   
   g. Your app will be live at: `https://your-app-name.onrender.com`

### Render Free Tier Limitations:
- ✅ Free forever
- ⚠️ Sleeps after 15 minutes of inactivity (takes 30-60 seconds to wake up)
- ✅ 750 hours/month of runtime
- ✅ Automatic deploys from GitHub

---

## Option 2: Railway

Railway offers generous free tier and easy deployment.

### Step-by-Step Instructions:

1. **Prepare Files** (same requirements.txt as above)

2. **Create `Procfile`**:
   ```
   web: gunicorn app:app
   ```

3. **Update `app.py`** (same as Render instructions above)

4. **Deploy on Railway**
   
   a. Go to [railway.app](https://railway.app) and sign up
   
   b. Click "New Project" → "Deploy from GitHub repo"
   
   c. Select your `desmos-art` repository
   
   d. Railway will auto-detect it's a Python app
   
   e. Add environment variables if needed
   
   f. Click "Deploy"
   
   g. Your app will be live at: `https://your-app.up.railway.app`

### Railway Free Tier:
- ✅ $5 free credit per month
- ✅ No sleep after inactivity
- ⚠️ Limited to ~500 hours/month

---

## Option 3: PythonAnywhere

Free tier with always-on service (no sleeping).

### Step-by-Step Instructions:

1. **Sign Up**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Create a free "Beginner" account

2. **Upload Your Code**
   
   a. Open a Bash console
   
   b. Clone your repository:
   ```bash
   git clone https://github.com/rithp/desmos-art.git
   cd desmos-art
   ```

3. **Create Virtual Environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 desmos-env
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   
   a. Go to "Web" tab → "Add a new web app"
   
   b. Choose "Manual configuration" → Python 3.9
   
   c. Set these configurations:
      - **Source code**: `/home/yourusername/desmos-art`
      - **Working directory**: `/home/yourusername/desmos-art`
      - **Virtualenv**: `/home/yourusername/.virtualenvs/desmos-env`
   
   d. Edit the WSGI configuration file:
   ```python
   import sys
   path = '/home/yourusername/desmos-art'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```

5. **Set Up Static Files**
   - URL: `/static/`
   - Directory: `/home/yourusername/desmos-art/static`

6. **Reload** the web app

7. Your app will be live at: `https://yourusername.pythonanywhere.com`

### PythonAnywhere Free Tier:
- ✅ Always on (no sleeping)
- ✅ Free forever
- ⚠️ Limited CPU and bandwidth
- ⚠️ Manual deployment (no auto-deploy from GitHub)

---

## Option 4: Fly.io

Fast and global edge deployment.

### Step-by-Step Instructions:

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign Up**
   ```bash
   fly auth signup
   # or
   fly auth login
   ```

3. **Create `fly.toml`**:
   ```toml
   app = "desmos-art-converter"
   
   [build]
     builder = "paketobuildpacks/builder:base"
   
   [env]
     PORT = "8080"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

4. **Create `Procfile`**:
   ```
   web: gunicorn app:app
   ```

5. **Deploy**
   ```bash
   cd "/Users/rithvikp/Desktop/rithvik/cv project"
   fly launch
   fly deploy
   ```

6. Your app will be live at: `https://desmos-art-converter.fly.dev`

### Fly.io Free Tier:
- ✅ 3 shared-cpu VMs
- ✅ 3GB storage
- ✅ Global deployment
- ⚠️ May sleep after inactivity

---

## Required Files Checklist

Before deploying, make sure you have:

- ✅ `requirements.txt` (with opencv-python-headless)
- ✅ `app.py` (updated for production)
- ✅ `Procfile` (for some platforms)
- ✅ `.gitignore` (exclude venv, __pycache__, uploads, outputs)
- ✅ All code pushed to GitHub

---

## Troubleshooting Common Issues

### Issue: "ModuleNotFoundError: No module named 'cv2'"
**Solution**: Make sure `opencv-python-headless` is in requirements.txt (not `opencv-python`)

### Issue: App crashes on startup
**Solution**: Check logs and ensure gunicorn is installed in requirements.txt

### Issue: "Address already in use"
**Solution**: Use `PORT` environment variable instead of hardcoding port 5000

### Issue: File upload too large
**Solution**: Most free tiers limit file uploads to 10-50MB

### Issue: Slow first load (Render)
**Solution**: Free tier sleeps after inactivity. Consider pinging your app with UptimeRobot

---

## Recommended: Render

For your use case, I recommend **Render** because:
- ✅ Easiest setup (directly from GitHub)
- ✅ Automatic deployments on git push
- ✅ Free SSL certificates
- ✅ Good documentation
- ✅ 750 hours/month is plenty

The only downside is the cold start delay, but that's acceptable for a free tier.

---

## Next Steps After Deployment

1. **Test Your Live App**
   - Upload test images
   - Verify Desmos output works
   - Check all download links

2. **Update Your GitHub README**
   - Add link to live demo
   - Update deployment status badge

3. **Optional: Custom Domain**
   - Most platforms allow custom domains on free tier
   - Point your domain DNS to the platform

4. **Monitor Usage**
   - Check platform dashboard for usage stats
   - Stay within free tier limits

---

## Need Help?

If you run into issues:
1. Check platform-specific documentation
2. Review deployment logs
3. Verify all files are committed to GitHub
4. Test locally first with `gunicorn app:app`

Good luck with your deployment! 🚀
