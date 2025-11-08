# Image to Desmos Equation Converter 🎨

Convert manga panels, anime characters, and other images into Desmos graphing calculator equations!

> 📚 **For detailed algorithm explanation, mathematical theory, and references, see [ALGORITHM_EXPLANATION.md](ALGORITHM_EXPLANATION.md)**

## 🚀 Quick Start

### 1. Activate the virtual environment
```bash
source venv/bin/activate
```

### 2. Run the converter
```bash
python base.py
```

## 📖 How to Use

### Basic Usage

1. **Place your image** in this folder (manga panel, anime character, etc.)
2. **Edit `base.py`** and change this line:
   ```python
   image_path = "test_image.jpg"  # Change to your image filename
   ```
3. **Run the script**:
   ```bash
   python base.py
   ```
4. **Copy the output** from `desmos_output.txt` to [Desmos](https://www.desmos.com/calculator)

### Advanced Usage

```python
from base import ImageToDesmosConverter

# Create converter
converter = ImageToDesmosConverter("your_anime_image.png")

# Customize parameters
converter.load_and_preprocess()

# Adjust edge detection sensitivity
converter.detect_edges(
    canny_low=30,      # Lower = more edges detected
    canny_high=100,    # Higher = fewer edges
    blur_size=5        # Higher = smoother edges
)

# Control detail level
converter.simplify_contours(
    epsilon_factor=0.001  # Lower = more detail, higher = simpler
)

# Fit curves and export
converter.fit_curves(smoothing_factor=0, num_points=100)
converter.export_to_desmos_file("my_output.txt", max_curves=50)
converter.visualize()
```

## 🎛️ Parameter Guide

### Edge Detection
- **`canny_low`** (30-100): Lower threshold - lower values detect more edges
- **`canny_high`** (100-200): Upper threshold - higher values are more selective
- **`blur_size`** (3-7): Blur before detection - higher = smoother

### Simplification
- **`epsilon_factor`** (0.001-0.01): 
  - Lower = more detail (more equations)
  - Higher = simpler (fewer equations)

### Curve Fitting
- **`smoothing_factor`** (0-10): 
  - 0 = exact fit to points
  - Higher = smoother curves
- **`num_points`** (50-200): Points per curve in output

### Export
- **`max_curves`** (10-100): Maximum curves to export to Desmos

## 💡 Tips for Best Results

### For Manga/Anime:
- ✅ Use **high-contrast** images
- ✅ **Clean line art** works best
- ✅ **Black & white** or simplified color schemes
- ✅ Start with **simpler characters** or **single panels**

### Image Preparation:
1. **Crop** to focus on the subject
2. **Increase contrast** if lines are faint
3. **Remove noise** or background clutter
4. **Resize** to 800-1000px for optimal processing

### Parameter Tuning:
- **Too many curves?** → Increase `epsilon_factor` or lower `canny_low`
- **Missing details?** → Decrease `epsilon_factor` or adjust Canny thresholds
- **Jagged curves?** → Increase `smoothing_factor` or `num_points`

## 📊 What Gets Generated

The script produces:

1. **`desmos_output.txt`**: Ready-to-paste Desmos equations
2. **`processing_steps.png`**: Visualization of the conversion process
3. Console output showing statistics

### Output Format
Each curve is exported as a polygon that Desmos can render:
```
polygon((100,200) (105,205) (110,210) ...)
```

## 🛠️ Troubleshooting

### "Could not load image"
- Check the file path is correct
- Supported formats: JPG, PNG, BMP, TIFF

### Too many equations / Desmos is slow
- Reduce `max_curves` parameter
- Increase `epsilon_factor` to simplify
- Use a simpler/smaller image

### Missing important features
- Decrease `canny_low` threshold
- Decrease `epsilon_factor`
- Try adjusting `blur_size`

### Curves look wrong
- Check if image needs preprocessing
- Adjust `smoothing_factor`
- Try inverting the image (white lines on black)

## 🎯 Example Workflows

### Simple Character Outline
```python
converter = ImageToDesmosConverter("character.png")
converter.load_and_preprocess()
converter.detect_edges(canny_low=50, canny_high=150)
converter.simplify_contours(epsilon_factor=0.005)  # Simpler
converter.fit_curves()
converter.export_to_desmos_file()
```

### Detailed Manga Panel
```python
converter = ImageToDesmosConverter("manga_panel.jpg")
converter.load_and_preprocess()
converter.detect_edges(canny_low=30, canny_high=120)
converter.simplify_contours(epsilon_factor=0.001)  # More detail
converter.fit_curves(num_points=150)
converter.export_to_desmos_file(max_curves=100)
```

## 📦 Dependencies

- `opencv-python`: Image processing and edge detection
- `numpy`: Numerical operations
- `scipy`: Curve fitting and interpolation
- `matplotlib`: Visualization

All installed in your virtual environment!

## 🔬 How It Works

1. **Edge Detection**: Canny algorithm finds edges in the image
2. **Contour Extraction**: Identifies separate curves/shapes
3. **Simplification**: Douglas-Peucker algorithm reduces point count
4. **Curve Fitting**: B-spline interpolation creates smooth parametric curves OR raw points for maximum accuracy
5. **Export**: Converts to Desmos polygon format

> 📖 **Want to understand the math and theory?** Read the [detailed algorithm explanation](ALGORITHM_EXPLANATION.md) which covers:
> - Mathematical foundations (Canny edge detection, B-splines, Douglas-Peucker)
> - Complexity analysis and performance characteristics
> - Comparison with Fourier transform approaches
> - Limitations and theoretical drawbacks
> - Academic references and citations

## 📝 Notes

- Desmos has a limit on complexity - simpler is often better
- You may need to adjust colors/styling in Desmos after import
- For large images, processing may take a few seconds
- Results work best with clear, defined edges

---

**Made for converting manga panels and anime characters to mathematical art! 🎨✨**
