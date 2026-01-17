# Image to Desmos Equation Converter

Convert manga panels, anime characters, ph## Parameter Guide

### Blur Options

#### Gaussian Blur (Default - Best## Tips for Best Results

### For Manga/Anime (Clean Line Art):
- Use **Gaussian blur** (default)
- **Disable** bilateral filter and posterization
- Use **high-contrast** images
- **Black & white** or simplified color schemes
- Start with **simpler characters** or **single panels**

### For Photos/Posters (Real-Life Images):
- **Enable bilateral filter** (preserves edges while smoothing)
- **Enable posterization** with 4-6 levels
- **Enable morphological cleanup** (close=3, open=2)
- Increase **min_contour_area** to 50-100
- Use higher **canny thresholds** (low=50, high=120)

### For Movie Posters:
- **Bilateral filter**: d=9, sigma_color=75-100, sigma_space=75-100
- **Posterization**: 4-5 levels for high simplification
- **Morphology**: close=3, open=2
- **Edge detection**: low=50, high=100-120

### Image Preparation:n line art)
- **`blur_size`** (3-7): Kernel size for Gaussian blur
  - 3 = Minimal smoothing
  - 5 = Standard smoothing  
  - 7 = Heavy smoothing

#### Bilateral Filter (Best for photos and posters)
- **`use_bilateral`**: Enable bilateral filtering instead of Gaussian
- **`bilateral_d`** (5-9): Diameter of pixel neighborhood
- **`bilateral_sigma_color`** (25-100): Color similarity threshold
- **`bilateral_sigma_space`** (25-100): Spatial distance threshold

**When to use bilateral filter:**
- Real-life photographs (portraits, landscapes)
- Movie posters with gradients and textures
- Images with noise but important edge details
- When you want to preserve sharp edges while smoothing

### Preprocessing Options

#### Posterization (Best for photos and high-detail images)
- **`use_posterize`**: Enable gray level reduction
- **`posterize_levels`** (2-16): Number of gray levels to reduce to
  - 2-4 = High contrast, cartoon-like effect
  - 5-8 = Balanced simplification
  - 9-16 = Subtle reduction

**When to use posterization:**
- Real-life photos with many shades of gray
- Movie posters with complex lighting
- Images that produce too many contours
- To create stylized, poster-like effects

#### Morphological Cleanup (Best for noisy images)
- **`use_morphology`**: Enable edge cleanup operations
- **`morph_close`** (2-5): Closing kernel size (connects broken edges)
- **`morph_open`** (1-3): Opening kernel size (removes noise)

**When to use morphology:**
- Photos with JPEG compression artifacts
- Images with broken or fragmented edges
- To connect nearby edge segments
- To remove small noise specks

### Edge Detection
- **`canny_low`** (30-100): Lower threshold - lower values detect more edges
- **`canny_high`** (100-200): Upper threshold - higher values are more selective
- **`min_contour_area`** (10-100): Minimum contour size to keepand movie posters into Desmos graphing calculator equations.

For detailed algorithm explanation, mathematical theory, and references, see [ALGORITHM_EXPLANATION.md](ALGORITHM_EXPLANATION.md)

## What's New in Version 2.0

Version 2.0 introduces advanced preprocessing features specifically designed for real-life photos and movie posters:

### New Features

**1. Bilateral Filter (Edge-Preserving Smoothing)**
- Smooths noise while preserving sharp edges
- Uses dual Gaussian kernels (spatial + color similarity)
- Ideal for photos, portraits, and posters with gradients
- Reduces contours by 30-50% compared to Gaussian blur
- Configurable parameters: diameter, sigma_color, sigma_space

**2. Posterization (Gray Level Quantization)**
- Reduces 256 gray levels to 2-16 discrete levels
- Simplifies complex images into distinct regions
- Reduces contours by 70-90% for photos
- Essential for movie posters and high-detail images
- Adjustable levels for different stylization effects

**3. Morphological Cleanup**
- Connects broken edge segments (closing operation)
- Removes noise specks and artifacts (opening operation)
- Reduces fragmented contours by 20-40%
- Configurable kernel sizes for fine control
- Particularly effective for JPEG-compressed images

**4. Preview Mode (Contours Only)**
- Fast preview of edge detection results
- See detected contours before full polynomial fitting
- Helps tune parameters without waiting for complete processing
- Displays contour count and visualization
- No equation generation for faster iteration

### Impact on Different Image Types

**Clean Line Art (Manga/Anime):**
- Version 1.0 already works well
- New features can be disabled for optimal results

**Real-Life Photos:**
- Version 1.0: 5,000-15,000 contours (unusable)
- Version 2.0 with preprocessing: 500-1,500 contours (acceptable)
- 80-90% reduction in complexity

**Movie Posters:**
- Version 1.0: 10,000+ contours (unusable)
- Version 2.0 with aggressive preprocessing: 800-1,500 contours (good)
- Bilateral + Posterization combination is critical

### Technical Details

For mathematical formulations and detailed explanations of these algorithms, see the updated [ALGORITHM_EXPLANATION.md](ALGORITHM_EXPLANATION.md).


## sample outputs
<div style="display: flex; gap: 10px;">
  <img src="image-1.png" alt="Sample Output 1" width="49%">
  <img src="image-2.png" alt="Sample Output 2" width="49%">
</div>

<div style="display: flex; gap: 10px;">
  <img src="image-3.png" alt="Sample Output 3" width="49%">
  <img src="image-4.png" alt="Sample Output 4" width="49%">
</div>

<div style="display: flex; gap: 10px;">
  <img src="image-5.png" alt="Sample Output 5" width="49%">
  <img src="image-6.png" alt="Sample Output 6" width="49%">
</div>


##  Quick Start

### 1. Activate the virtual environment
```bash
source venv/bin/activate
```

### 2. Run the converter
```bash
python base.py
```

##  How to Use

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

##  Parameter Guide

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

##  Tips for Best Results

### For Manga/Anime:
-  Use **high-contrast** images
-  **Clean line art** works best
- **Black & white** or simplified color schemes
-  Start with **simpler characters** or **single panels**

### Image Preparation:
1. **Crop** to focus on the subject
2. **Increase contrast** if lines are faint
3. **Remove noise** or background clutter
4. **Resize** to 800-1000px for optimal processing

### Parameter Tuning:
- **Too many curves?** → Increase `epsilon_factor` or lower `canny_low`
- **Missing details?** → Decrease `epsilon_factor` or adjust Canny thresholds
- **Jagged curves?** → Increase `smoothing_factor` or `num_points`

##  What Gets Generated

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

##  Example Workflows

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

##  Dependencies

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

>  **Want to understand the math and theory?** Read the [detailed algorithm explanation](ALGORITHM_EXPLANATION.md) which covers:
> - Mathematical foundations (Canny edge detection, B-splines, Douglas-Peucker)
> - Complexity analysis and performance characteristics
> - Comparison with Fourier transform approaches
> - Limitations and theoretical drawbacks
> - Academic references and citations

##  Notes

- Desmos has a limit on complexity - simpler is often better
- You may need to adjust colors/styling in Desmos after import
- For large images, processing may take a few seconds
- Results work best with clear, defined edges

---


## Failures

![alt text](image-7.png)

![alt text](image-8.png)
