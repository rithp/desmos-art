# Web Application Usage Guide

## Running the Web App

### 1. Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

### 2. Start the Flask Server

```bash
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
```

### 3. Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

## Using the Web Interface

1. **Upload an Image**: Click "Choose an image..." and select your image file
2. **Adjust Parameters** (optional):
   - **Rotation**: Rotate the image before processing (-360 to 360 degrees)
   - **Polynomial Degree**: Higher = smoother curves (3-10, default: 5)
   - **Edge Thresholds**: Adjust edge detection sensitivity
   - **Simplification Factor**: Lower = more detail, higher = simpler (0.0001-0.01)
3. **Click "Convert to Desmos"**: Wait for processing to complete
4. **View Results**:
   - **Output Image**: Preview of the converted image
   - **Console Input**: Copy this code to paste into Desmos console
   - **Download Files**: Download the output files

## Using the Desmos Console Output

1. Open [Desmos Graphing Calculator](https://www.desmos.com/calculator)
2. Press **F12** (or **Ctrl+Shift+I**) to open browser console
3. **Copy** the entire console input from the web app
4. **Paste** into the browser console
5. Press **Enter**
6. Your image will appear as mathematical equations!

## Tips

- **For best results**: Use high-contrast images with clear edges
- **Manga/Anime**: Works great with line art and simplified graphics
- **Complex images**: May take 10-30 seconds to process
- **Too slow in Desmos?**: Increase the simplification factor to reduce equation count

## Troubleshooting

### Server won't start
- Make sure port 5000 is not in use
- Try: `python app.py` or `python3 app.py`

### Image won't upload
- Check file size (max 16MB)
- Supported formats: PNG, JPG, JPEG, GIF, BMP

### Processing takes too long
- Use smaller images (resize to ~800x800px)
- Increase simplification factor
- Lower the polynomial degree

## File Structure

```
cv project/
├── app.py                  # Flask web server
├── base.py                 # Image processing logic
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── style.css          # Styling
├── uploads/               # Temporary upload storage
└── outputs/               # Generated output files
```

## Stopping the Server

Press **Ctrl+C** in the terminal where the server is running.
