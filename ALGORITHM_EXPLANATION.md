# Image to Desmos Converter - Algorithm Explanation

## Overview

This tool converts 2D images (particularly manga panels and anime characters) into mathematical equations that can be rendered in the Desmos graphing calculator. The approach uses **edge detection** followed by **contour extraction** to represent images as sets of parametric curves.

---
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



## Algorithm Pipeline

### 1. **Image Preprocessing**

**Steps:**
- Load image using OpenCV
- Convert to grayscale using the luminosity method

**Mathematical Basis:**
```
Grayscale = 0.299R + 0.587G + 0.114B
```
This weighted sum accounts for human perception sensitivity to different colors (more sensitive to green, less to blue).

**Reference:**
- OpenCV Documentation: Color Space Conversions
- ITU-R BT.601 standard for luminance calculation

---

### 2. **Edge Detection (Canny Algorithm)**

**Purpose:** Identify boundaries between different regions in the image.

**Algorithm Steps:**

#### a) Gaussian Blur
Reduces noise before edge detection:
```
G(x,y) = (1/(2πσ²)) * e^(-(x²+y²)/(2σ²))
```
A 5×5 Gaussian kernel is convolved with the image to smooth pixel intensities.

**Why?** Raw images contain noise that would create false edges.

#### b) Gradient Calculation
Compute intensity gradients using Sobel operators:
```
Gx = [[-1, 0, 1],      Gy = [[-1, -2, -1],
      [-2, 0, 2],             [ 0,  0,  0],
      [-1, 0, 1]]             [ 1,  2,  1]]

Magnitude: |G| = √(Gx² + Gy²)
Direction: θ = arctan(Gy/Gx)
```
essentially Gx finds the intensity contrast in x dirn and Gy in y dirn, from this we get well defined edges.

#### c) Non-Maximum Suppression
edges produced are usually reall thick, due to the fact that itensity varies over a few rows and columns of pixels, this reduces the thickness and gives thin well defined lines.

#### d) Double Threshold (Hysteresis)
Uses two thresholds (low and high):
- **High threshold (150)**: Definite edges
- **Low threshold (50)**: Potential edges
- Edges connected to strong edges are kept; isolated weak edges are discarded

**Parameters in Code:**
```python
canny_low = 50    # Lower threshold
canny_high = 150  # Upper threshold
```

**Reference:**
- Canny, J. (1986). "A Computational Approach to Edge Detection." IEEE Trans. Pattern Analysis and Machine Intelligence, 8(6):679-698.
- DOI: 10.1109/TPAMI.1986.4767851
- Computerphile has amazing videos on these topics.

---

### 3. **Contour Extraction**

**Method:** `cv2.findContours()` with `CHAIN_APPROX_SIMPLE`

**Algorithm:** Suzuki's Border Following Algorithm

**Mathematical Representation:**
Each contour C is a sequence of 2D points:
```
C = {(x₁,y₁), (x₂,y₂), ..., (xₙ,yₙ)}
```

**Optimization:** `CHAIN_APPROX_SIMPLE` removes redundant points:
- Stores only endpoints of horizontal, vertical, and diagonal segments
- Reduces point count by ~50-70% without losing shape information


**Example:**
```
Original: [(0,0), (1,0), (2,0), (3,0), (3,1), (3,2)]
Simplified: [(0,0), (3,0), (3,2)]
```

**Reference:**
- Suzuki, S. and Abe, K. (1985). "Topological Structural Analysis of Digitized Binary Images by Border Following." CVGIP 30(1), pp. 32-46.

---

### 4. **Contour Simplification (Douglas-Peucker Algorithm)**

**Purpose:** Reduce number of points while preserving shape.

**Algorithm:**
1. Draw a line between the first and last points
2. Find the point with maximum perpendicular distance from this line
3. If distance > ε (epsilon), recursively simplify left and right segments
4. If distance ≤ ε, discard intermediate points

**Mathematical Formulation:**

Distance from point P to line segment AB:
```
d = ||(B-A) × (A-P)|| / ||B-A||
```

Where × denotes the cross product (in 2D: determinant).

**Epsilon Parameter:**
```python
ε = epsilon_factor × perimeter(contour)
epsilon_factor = 0.0001  # High accuracy mode
```

**Trade-off:**
- **Smaller ε** → More points → Higher accuracy → Slower Desmos rendering
- **Larger ε** → Fewer points → Loss of detail → Faster rendering

**Example Effect:**
```
ε = 0.01: 1000 points → 100 points (smooth but loses details)
ε = 0.0001: 1000 points → 800 points (preserves fine details)
```

**Reference:**
- Douglas, D. H., & Peucker, T. K. (1973). "Algorithms for the reduction of the number of points required to represent a digitized line or its caricature." Cartographica, 10(2), 112-122.
- DOI: 10.3138/FM57-6770-U75U-7727

---

### 5. **Coordinate Transformation**

**Problem:** Image coordinates have origin at top-left with y-axis pointing down.
**Solution:** Transform to Cartesian coordinates (origin at bottom-left, y-axis up).

```python
y_cartesian = image_height - y_image
```

**Matrix Representation:**
```
[x']   [1   0    0  ] [x]
[y'] = [0  -1    h  ] [y]
[1 ]   [0   0    1  ] [1]
```

Where h is the image height.

---

### 6. **Curve Representation**



**Method:** Use edge pixels directly without interpolation.

**Representation:**
```
Points: {(x₁,y₁), (x₂,y₂), ..., (xₙ,yₙ)}
```

**Advantages:**
-  Perfect fidelity to detected edges
-  Preserves sharp corners and fine details
-  No mathematical approximation error

**Disadvantages:**
-  Large number of points (typically 100-300 per curve)
-  May include staircase artifacts from pixelation
-  Slower rendering in Desmos

**Best For:** Manga, anime, technical drawings, architecture

---

#### **Mode 2: B-Spline Interpolation (Balanced)**

**Method:** Fit parametric B-spline curves through points.

**Mathematical Formulation:**

A B-spline curve is defined as:
```
C(u) = Σᵢ₌₀ⁿ Pᵢ Nᵢ,ₖ(u)
```

Where:
- `Pᵢ` = control points
- `Nᵢ,ₖ(u)` = B-spline basis functions of degree k
- `u ∈ [0,1]` = parameter

**Parametric Form:**
```
x(t) = Σᵢ₌₀ⁿ xᵢ Nᵢ,₃(t)
y(t) = Σᵢ₌₀ⁿ yᵢ Nᵢ,₃(t)
```

We use cubic B-splines (k=3) for smooth C² continuity.

**Basis Functions (Cox-de Boor recursion):**
```
Nᵢ,₀(u) = 1 if tᵢ ≤ u < tᵢ₊₁, else 0

Nᵢ,ₖ(u) = ((u - tᵢ)/(tᵢ₊ₖ - tᵢ)) Nᵢ,ₖ₋₁(u) + 
          ((tᵢ₊ₖ₊₁ - u)/(tᵢ₊ₖ₊₁ - tᵢ₊₁)) Nᵢ₊₁,ₖ₋₁(u)
```

**Smoothing Factor:**
```python
s = 0  # Exact interpolation (curve passes through all points)
s > 0  # Approximate fit (curve near points, smoother)
```

The smoothing is achieved by minimizing:
```
E = Σᵢ (d(Pᵢ, C(uᵢ)))² + s × ∫ |C''(u)|² du
```
- First term: fitting error
- Second term: curvature penalty (weighted by s)

**Advantages:**
- Smooth, continuous curves
-  Fewer points needed (50-500 per curve)
-  Better for organic/rounded shapes
-  Removes pixelation artifacts

**Disadvantages:**
-  Loss of sharp corners and fine details
-  Approximation introduces error
-  Poor for angular/geometric shapes
-  Can create unwanted oscillations (Runge's phenomenon)

**Best For:** Organic shapes, portraits, rounded objects

**Reference:**
- de Boor, C. (1978). "A Practical Guide to Splines." Springer-Verlag.
- Scipy's `splprep` documentation: Uses FITPACK library (Dierckx, 1993)

---

### 7. **Desmos Export Format**

**Output Format:**
```
[(x₁,y₁), (x₂,y₂), ..., (xₙ,yₙ)]
```

**Why This Format?**
- Desmos interprets lists of points as polygons/polylines
- Automatically connects consecutive points with line segments
- Supports both open curves and closed polygons

**Alternative Formats** (not used):
- Parametric equations: `(x(t), y(t))` - Limited to simple functions
-  Implicit equations: `f(x,y) = 0` - Hard to fit to arbitrary curves
-  Polynomial fit: `y = p(x)` - Fails for vertical lines and multi-valued functions

---

## Complete Mathematical Workflow

### Input → Output Transformation

1. **Image Matrix** → Grayscale conversion
   ```
   I(x,y) ∈ [0,255]³ → G(x,y) ∈ [0,255]
   ```

2. **Grayscale** → Edge map via Canny
   ```
   G(x,y) → E(x,y) ∈ {0,1}
   ```

3. **Edge map** → Connected components (contours)
   ```
   E → {C₁, C₂, ..., Cₘ}
   ```

4. **Contours** → Simplified contours
   ```
   Cᵢ = {p₁, ..., pₙ} → C'ᵢ = {p'₁, ..., p'ₖ} where k < n
   ```

5. **Simplified contours** → Parametric curves
   ```
   C'ᵢ → (xᵢ(t), yᵢ(t)) or raw points
   ```

6. **Curves** → Desmos list format
   ```
   (xᵢ(t), yᵢ(t)) → [(x₁,y₁), (x₂,y₂), ...]
   ```

---

## Complexity Analysis

### Time Complexity

- **Gaussian Blur:** O(w × h × k²) where k = kernel size (5×5)
- **Canny Edge Detection:** O(w × h)
- **Contour Finding:** O(w × h) 
- **Douglas-Peucker per contour:** O(n log n) average, O(n²) worst case
- **B-Spline fitting per contour:** O(n³) for cubic splines

**Total:** O(w × h + Σᵢ nᵢ³) where nᵢ = points in contour i

**Typical Performance:**
- 500×500 image with 50 contours (100 points each): ~1-2 seconds

### Space Complexity

- **Raw Points Mode:** O(total_edge_pixels) ≈ 0.1-0.2 × w × h
- **Spline Mode:** O(num_contours × points_per_curve)

---





## Limitations and Drawbacks

1. Fails in high contrast images like movie posters, model pictures, etc.
2. fails in manga panels with high shading and detailing

---

## References

### Primary Papers

1. **Canny, J.** (1986). "A Computational Approach to Edge Detection." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 8(6):679-698.

2. **Suzuki, S., & Abe, K.** (1985). "Topological structural analysis of digitized binary images by border following." *Computer Vision, Graphics, and Image Processing*, 30(1):32-46.

3. **Douglas, D. H., & Peucker, T. K.** (1973). "Algorithms for the reduction of the number of points required to represent a digitized line or its caricature." *Cartographica*, 10(2):112-122.

4. **de Boor, C.** (1978). *A Practical Guide to Splines.* Springer-Verlag, New York.

### Software Libraries

1. **OpenCV** (2024). "Canny Edge Detection." https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

2. **SciPy** (2024). "Interpolate - splprep, splev." https://docs.scipy.org/doc/scipy/reference/interpolate.html

3. **Dierckx, P.** (1993). *Curve and Surface Fitting with Splines.* Oxford University Press. (Used by SciPy's FITPACK)

### Books

1. **Gonzalez, R. C., & Woods, R. E.** (2018). *Digital Image Processing* (4th ed.). Pearson.

2. **Sonka, M., Hlavac, V., & Boyle, R.** (2014). *Image Processing, Analysis, and Machine Vision* (4th ed.). Cengage Learning.

3. **Preparata, F. P., & Shamos, M. I.** (1985). *Computational Geometry: An Introduction.* Springer-Verlag.

### Online Resources

1. **3Blue1Brown** - "But what is a Fourier series?" https://www.youtube.com/watch?v=r6sGWTCMz2k

2. **Desmos** - "Lists of Points" documentation. https://help.desmos.com/hc/en-us/articles/4407725009165

3. **Wikipedia** - "Canny edge detector", "Ramer-Douglas-Peucker algorithm", "B-spline"

---

## Future Improvements

1. maybeee try adding a feature that lets us set threshold for a part of the image according to our choosing.
2. try to look for methods for 3d detection with high contrast (3d for normal photos like stock images works fine)
3. try llm features like visual transofrmers to produces good edges which take care of semantic interpretation.

### Algorithmic Enhancements

1. **Adaptive Thresholding**
   - Implement Otsu's method for automatic threshold selection
   - Local adaptive thresholds for varying lighting

2. **Sub-pixel Edge Detection**
   - Interpolate edge positions to sub-pixel accuracy
   - Reduce staircase artifacts

3. **Curve Hierarchy**
   - Respect parent-child relationships (holes in shapes)
   - Proper ordering for Desmos polygon() function

4. **Semantic Segmentation**
   - Use deep learning to identify important features
   - Priority-based curve export (faces → bodies → background)

### Alternative Representations

1. **Bézier Curves**
   - More intuitive control points
   - Better for manual editing

2. **NURBS**
   - Non-uniform rational B-splines
   - Better for precise CAD-like shapes

3. **Implicit Functions**
   - Level sets: f(x,y) = c
   - Can represent filled regions

### Performance Optimizations

1. **Multi-threading**
   - Parallel contour processing
   - GPU-accelerated edge detection



---

## Failures

![alt text](image-7.png)

![alt text](image-8.png)

---

**Last Updated:** Jan 14, 2026
**Version:** 1.0
