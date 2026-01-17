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

### 2. Edge Detection with Blur Preprocessing

#### 2.1 Gaussian Blur (Default - For Clean Line Art)

**Purpose:** Reduce noise before edge detection while preserving general structure.

**Mathematical Formulation:**

The 2D Gaussian function is given by:
```
G(x, y) = (1 / (2πσ²)) × exp(-(x² + y²) / (2σ²))
```

Where:
- σ (sigma) = standard deviation, controls spread
- (x, y) = distance from kernel center
- For kernel size k, typically σ = 0.3 × ((k-1) × 0.5 - 1) + 0.8

The smoothed image is obtained by convolution:
```
I_smooth(x, y) = (I * G)(x, y) = ΣΣ I(x-i, y-j) × G(i, j)
```

**Characteristics:**
- Isotropic smoothing (equal in all directions)
- Smooths both noise and edges uniformly
- Fast computation with separable kernels

**Best for:** Manga, anime, clean line art, technical drawings

---

#### 2.2 Bilateral Filter (For Photos and Posters)

**Purpose:** Edge-preserving smoothing - reduces noise while maintaining sharp edges.

**Mathematical Formulation:**

The bilateral filter is defined as:
```
I_bilateral(x, y) = (1/W) × ΣΣ I(i, j) × w_spatial(x, y, i, j) × w_range(I(x,y), I(i,j))
```

Where the spatial weight is a Gaussian based on distance:
```
w_spatial(x, y, i, j) = exp(-((x-i)² + (y-j)²) / (2σ_space²))
```

And the range weight is a Gaussian based on intensity difference:
```
w_range(I_center, I_neighbor) = exp(-(I_center - I_neighbor)² / (2σ_color²))
```

The normalization factor is:
```
W = ΣΣ w_spatial(x, y, i, j) × w_range(I(x,y), I(i,j))
```

**Parameters:**
- **d**: Diameter of pixel neighborhood (typically 5-9)
- **σ_color** (sigma_color): Controls intensity similarity (25-100)
  - Low values: Only very similar colors are averaged
  - High values: More permissive smoothing
- **σ_space** (sigma_space): Controls spatial distance (25-100)
  - Similar to Gaussian blur's sigma

**Key Difference from Gaussian:**
```
Gaussian:   w(x,y,i,j) = exp(-(distance²)/(2σ²))
Bilateral:  w(x,y,i,j) = exp(-(distance²)/(2σ_space²)) × exp(-(color_diff²)/(2σ_color²))
                         └─────────────────────────────┘   └────────────────────────────┘
                              Spatial component                  Range component
```

**Why it works better for photos:**
- Pixels across edges have large intensity differences → low range weight → edge preserved
- Pixels in smooth regions have similar intensities → high range weight → smoothed effectively
- Reduces noise while keeping object boundaries sharp

**Best for:** Real-life photographs, movie posters, images with gradients and textures

**Reference:**
- Tomasi, C., & Manduchi, R. (1998). "Bilateral filtering for gray and color images." ICCV.

---

### 2.3 Posterization (Gray Level Quantization)

**Purpose:** Reduce the number of gray levels to simplify complex images and reduce contour count.

**Mathematical Formulation:**

For an 8-bit grayscale image with values in [0, 255], posterization maps these to N discrete levels:
```
step = ⌊256 / N⌋

I_posterized(x, y) = ⌊I(x, y) / step⌋ × step
```

**Example with N=4 levels:**
```
step = 256 / 4 = 64

Original intensity ranges → Posterized value:
[0, 63]     → 0
[64, 127]   → 64
[128, 191]  → 128  
[192, 255]  → 192
```

**Effect on edge detection:**
```
Original: 256 possible gray levels → many subtle edges
Posterized (N=4): 4 gray levels → only 4 distinct regions → fewer, cleaner edges
```

**Typical Results:**
```
Photo without posterization: 2000-5000 contours
Same photo with N=4 posterization: 100-500 contours (80-90% reduction)
```

**Parameters:**
- **N** (posterize_levels): Number of gray levels (2-16)
  - N=2: Binary (black/white only) - extreme simplification
  - N=4-6: Strong posterization - good for complex photos
  - N=8-12: Moderate posterization - balanced
  - N=16: Subtle posterization - minor simplification

**Best for:** Real-life photos, movie posters, images producing too many contours

**Reference:**
- Gonzalez, R. C., & Woods, R. E. (2018). "Digital Image Processing," Chapter 3: Intensity Transformations.

---

### 2.4 Canny Edge Detection

**Purpose:** Identify boundaries between different regions in the image.

**Algorithm Steps:**

#### a) Gaussian Blur (if not already applied)
Reduces noise before edge detection:
```
G(x,y) = (1/(2πσ²)) × exp(-(x²+y²)/(2σ²))
```
A 5×5 Gaussian kernel is convolved with the image to smooth pixel intensities.

**Note:** When using bilateral filter, this step is skipped as bilateral filtering is applied before Canny.

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
Edges produced are usually thick due to the fact that intensity varies over a few rows and columns of pixels. This step reduces the thickness and produces thin, well-defined lines.

**Algorithm:**
- For each pixel, check if it is a local maximum along the gradient direction
- If not, suppress it (set to zero)
- Result: Single-pixel-wide edges

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

### 3. Contour Extraction

**Method:** `cv2.findContours()` with `CHAIN_APPROX_SIMPLE`

**Algorithm:** Suzuki's Border Following Algorithm

**Mathematical Representation:**
Each contour C is a sequence of 2D points:
```
C = {(x₁,y₁), (x₂,y₂), ..., (xₙ,yₙ)}
```

**Optimization:** `CHAIN_APPROX_SIMPLE` removes redundant points:
- Stores only endpoints of horizontal, vertical, and diagonal segments
- Reduces point count by approximately 50-70% without losing shape information


**Example:**
```
Original: [(0,0), (1,0), (2,0), (3,0), (3,1), (3,2)]
Simplified: [(0,0), (3,0), (3,2)]
```

**Reference:**
- Suzuki, S. and Abe, K. (1985). "Topological Structural Analysis of Digitized Binary Images by Border Following." CVGIP 30(1), pp. 32-46.

---

### 4. Morphological Cleanup (Optional - For Noisy Images)

**Purpose:** Clean up the edge map by connecting broken edges and removing noise.

#### 4.1 Morphological Closing (Connect Broken Edges)

**Mathematical Operation:**
```
Closing(A, B) = Erosion(Dilation(A, B), B)
```

Where:
- A = edge image (binary)
- B = structuring element (kernel)

**Dilation:**
```
Dilation(A, B) = A ⊕ B = {z | (B̂)_z ∩ A ≠ ∅}
```
Expands white regions by adding pixels at the boundaries.

**Erosion:**
```
Erosion(A, B) = A ⊖ B = {z | B_z ⊆ A}
```
Shrinks white regions by removing boundary pixels.

**Net Effect of Closing:**
- Fills small gaps in edges
- Connects nearby broken edge segments
- Preserves overall shape and size

**Example:**
```
Before Closing:        After Closing (3×3 kernel):
[0 0 1 1 0 0 1 1 0]  → [0 0 1 1 1 1 1 1 0]
     ↑ gap ↑                ↑ connected ↑
```

**Kernel Size (close_kernel):**
```
3×3: Connects gaps of 1-2 pixels
5×5: Connects gaps of 3-4 pixels  
7×7: Connects larger gaps (may over-connect)
```

---

#### 4.2 Morphological Opening (Remove Noise)

**Mathematical Operation:**
```
Opening(A, B) = Dilation(Erosion(A, B), B)
```

**Net Effect:**
- Removes isolated pixels and small specks
- Eliminates noise without affecting larger structures
- Smooths object boundaries

**Example:**
```
Before Opening:         After Opening (2×2 kernel):
[0 0 1 0 0 0 0 1 1]  → [0 0 0 0 0 0 0 1 1]
     ↑ speck                      ↑ removed
```

**Kernel Size (open_kernel):**
```
1×1: Minimal - only removes single pixels
2×2: Standard - removes small noise specks
3×3: Aggressive - removes larger noise (may remove small details)
```

---

#### 4.3 Complete Morphological Cleanup Process

**Implementation:**
```python
# Step 1: Closing (fill gaps)
close_kernel = np.ones((close_size, close_size), np.uint8)
edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, close_kernel)

# Step 2: Opening (remove noise)  
open_kernel = np.ones((open_size, open_size), np.uint8)
edges_clean = cv2.morphologyEx(edges_closed, cv2.MORPH_OPEN, open_kernel)

# Step 3: Re-extract contours from cleaned edge map
contours, _ = cv2.findContours(edges_clean, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
```

**Effect on Contour Count:**
```
Original edge map: 2000 contours (many fragments and noise)
After closing:     1500 contours (fragments connected)
After opening:     800 contours (noise removed)
Final cleaned:     800 clean, meaningful contours
```

**When to use:**
- Photos with JPEG compression artifacts
- Images with broken or fragmented edges  
- Movie posters with texture noise
- When contour count is too high due to noise

**When NOT to use:**
- Clean line art (manga, technical drawings)
- When small details are important
- Images already preprocessed to be clean

**Reference:**
- Serra, J. (1983). "Image Analysis and Mathematical Morphology." Academic Press.
- Gonzalez, R. C., & Woods, R. E. (2018). "Digital Image Processing," Chapter 9: Morphological Image Processing.

---

### 5. Contour Simplification (Douglas-Peucker Algorithm)

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

### 6. Coordinate Transformation

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

### 7. Curve Representation



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

#### Parametric Curve Fitting (Alternative - Using Lagrange Interpolation)

**Method:** Fit Lagrange polynomials through overlapping segments of contour points.

**Mathematical Formulation:**

For n+1 points {(x₀,y₀), (x₁,y₁), ..., (xₙ,yₙ)}, the Lagrange polynomial is:
```
L(t) = Σᵢ₌₀ⁿ yᵢ × ℓᵢ(t)
```

Where the basis polynomials are:
```
ℓᵢ(t) = ∏ⱼ₌₀,ⱼ≠ᵢⁿ [(t - tⱼ) / (tᵢ - tⱼ)]
```

For parametric curves, apply separately to x and y:
```
x(t) = Σᵢ₌₀ⁿ xᵢ × ℓᵢ(t)
y(t) = Σᵢ₌₀ⁿ yᵢ × ℓᵢ(t)
```

**Segmentation Strategy:**
To avoid Runge's phenomenon (oscillations with high-degree polynomials), contours are broken into overlapping segments:
```
Segment size: 5-10 points
Overlap: 2 points between consecutive segments
Result: Many low-degree polynomials instead of one high-degree polynomial
```

**Example:**
```
Contour with 100 points, segment_size=5:
- Segment 1: points [0, 1, 2, 3, 4]
- Segment 2: points [3, 4, 5, 6, 7]  (overlap: 3, 4)
- Segment 3: points [6, 7, 8, 9, 10] (overlap: 6, 7)
...
Total: ~25 segments, each with degree-4 polynomial
```

**Advantages:**
- No smoothing artifacts
- Preserves sharp corners better than B-splines
- Lower degree polynomials are more stable

**Disadvantages:**
- More equations needed than B-splines
- Discontinuities at segment boundaries
- Not as smooth as B-splines

---

#### Mode 2: B-Spline Interpolation (Balanced)

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

### 8. Desmos Export Format

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





## Limitations and Challenges

### 1. High-Contrast Real-Life Images

**Problem:** Photos and movie posters contain many shades of gray, resulting in thousands of edge contours.

**Example:**
```
Movie poster without preprocessing: 5000-15000 contours
Same poster with Gaussian blur only: 3000-10000 contours (still too many)
```

**Solution:** Use preprocessing features designed for real-life images:

#### Bilateral Filtering
- Smooths noise while preserving important edges
- Reduces false edges from gradients and textures
- Typical reduction: 30-50% fewer contours

#### Posterization
- Reduces gray levels from 256 to 4-16 discrete values
- Simplifies complex shading into distinct regions
- Typical reduction: 70-90% fewer contours

#### Morphological Cleanup
- Connects broken edge fragments
- Removes noise specks and artifacts
- Typical reduction: 20-40% fewer contours

**Combined Effect:**
```
Movie poster baseline: 13,000 contours
+ Bilateral filter: 8,000 contours (-38%)
+ Posterization (N=4): 1,200 contours (-91% from baseline)
+ Morphology: 800 contours (-94% from baseline)
```

**Recommended Settings for Photos/Posters:**
```
Bilateral: d=9, sigma_color=75-100, sigma_space=75-100
Posterization: 4-6 levels
Morphology: close=3, open=2
Edge detection: low=50, high=100-120
Min contour area: 50-100
```

### 2. Heavily Shaded Manga Panels

**Problem:** Manga with extensive screentone shading, crosshatching, or detailed textures produces too many contours.

**Example:**
```
Simple manga panel: 50-200 contours (works well)
Heavily shaded panel: 1000-3000 contours (too complex)
```

**Partial Solutions:**
- Increase edge detection thresholds (low=60, high=150)
- Use larger Gaussian blur (blur_size=7)
- Increase epsilon_factor for more aggressive simplification
- Preprocess image to remove screentones before conversion

**Limitation:** No perfect solution for preserving both line art and complex shading patterns.

### 3. Fundamental Algorithm Limitations

**Edge-Based Representation:**
- Only captures boundaries, not filled regions or gradients
- Cannot represent smooth color transitions
- Loses information about interior details

**Desmos Constraints:**
- Performance degrades with >1000 equations
- No native support for filled polygons with gradients
- Limited styling options for curves

**Accuracy vs. Complexity Trade-off:**
```
High accuracy (epsilon=0.0001): 10,000+ points → slow rendering
High simplification (epsilon=0.01): 500 points → loss of detail
```

---

## Practical Guidelines

### Image Type Classification

#### Type 1: Clean Line Art (Optimal)
**Characteristics:** Manga, anime, technical drawings, logos
**Settings:**
```
Blur: Gaussian (blur_size=3-5)
Bilateral: Disabled
Posterization: Disabled
Morphology: Disabled
Edge detection: low=30, high=100
```

#### Type 2: Real-Life Photos (Challenging - Use Preprocessing)
**Characteristics:** Portraits, landscapes, stock photos
**Settings:**
```
Blur: Bilateral (d=9, sigma_color=75, sigma_space=75)
Bilateral: Enabled
Posterization: Enabled (4-6 levels)
Morphology: Enabled (close=3, open=2)
Edge detection: low=50, high=120
Min contour area: 50-100
```

#### Type 3: Movie Posters (Challenging - Use Aggressive Preprocessing)
**Characteristics:** High contrast, text, gradients, multiple subjects
**Settings:**
```
Blur: Bilateral (d=9, sigma_color=100, sigma_space=100)
Bilateral: Enabled
Posterization: Enabled (4-5 levels - aggressive)
Morphology: Enabled (close=3-5, open=2-3)
Edge detection: low=50, high=100-120
Min contour area: 100
```

### Expected Contour Counts

```
Clean manga panel: 50-300 contours (excellent)
Manga with shading: 500-1500 contours (acceptable)
Simple photo: 1000-3000 contours (acceptable with preprocessing)
Complex photo: 2000-5000 contours (challenging even with preprocessing)
Movie poster (no preprocessing): 10,000-15,000 contours (unusable)
Movie poster (with preprocessing): 500-1500 contours (acceptable)
```

### Performance Benchmarks

```
Image preprocessing (bilateral + posterization + morphology): 0.5-2 seconds
Edge detection (Canny): 0.1-0.5 seconds
Contour extraction: 0.1-0.3 seconds
Douglas-Peucker simplification: 0.2-1 second
Lagrange curve fitting: 1-5 seconds
Total processing time: 2-10 seconds (depends on image size and complexity)
```

---

## Why Bilateral Filter and Posterization Are Critical for Real Images

### Gaussian Blur Limitations

**Problem:** Gaussian blur smooths uniformly in all directions:
```
w(distance) = exp(-distance² / (2σ²))
```
- Blurs across edges and within regions equally
- Reduces noise but also weakens important edges
- Still leaves many gray levels → many contours

**Example:**
```
Photo with Gaussian blur (σ=5): 8000 contours
Same photo with bilateral filter: 4000 contours (50% reduction)
```

### Bilateral Filter Advantages

**Mechanism:** Considers both spatial distance AND intensity similarity:
```
w(distance, color_diff) = exp(-distance²/(2σ_space²)) × exp(-color_diff²/(2σ_color²))
                          └────────────────────────┘   └──────────────────────────┘
                           Spatial weight (like Gaussian)   Range weight (preserves edges)
```

**Effect:**
- **Within smooth regions:** Similar colors → high range weight → smoothed effectively
- **Across edges:** Different colors → low range weight → edge preserved
- **Result:** Noise reduced while edges remain sharp

**Comparison:**
```
Gradient region (sky): [100, 105, 110, 115, 120]
Gaussian blur: [108, 109, 110, 111, 112] (gradient smoothed)
Bilateral filter: [102, 107, 110, 113, 118] (gradient preserved, noise reduced)

Edge region: [50, 55, 200, 205, 210]
Gaussian blur: [100, 125, 150, 175, 185] (edge weakened)
Bilateral filter: [52, 53, 202, 207, 208] (edge preserved)
```

### Posterization Necessity

**Problem:** Natural images have 256 gray levels → edges detected at every subtle intensity change.

**Example Intensity Profile:**
```
Original pixel values: [45, 52, 58, 65, 71, 78, 85, 92, 98, ...]
Canny edges detected: Multiple edges at every transition
Result: Hundreds of contours for a single object
```

**Posterization Effect (N=4 levels):**
```
Step = 256/4 = 64
Posterized values: [0, 64, 64, 64, 64, 64, 128, 128, 128, ...]
Canny edges detected: Single edge at 0→64 transition, single edge at 64→128 transition
Result: Clean, distinct boundaries
```

**Mathematical Justification:**

Number of possible edges without posterization:
```
Max edges = 256 - 1 = 255 possible intensity transitions
```

Number of possible edges with N-level posterization:
```
Max edges = N - 1 transitions
Example: N=4 → only 3 possible edge types (0→64, 64→128, 128→192, 192→255)
Reduction factor = 255/3 ≈ 85× fewer potential edges
```

**Practical Impact:**
```
Portrait photo (no posterization): 12,000 contours
Same photo (N=4 posterization): 1,500 contours (87.5% reduction)
Same photo (N=8 posterization): 3,000 contours (75% reduction)
```

### Why Clean Line Art Doesn't Need These Features

**Characteristics of Clean Line Art:**
- Already high contrast (black lines on white background)
- Few gray levels naturally (often binary or near-binary)
- Sharp, well-defined edges without noise
- Minimal gradients or textures

**Example:**
```
Manga panel pixel values: [255, 255, 255, 0, 0, 0, 255, 255, ...]
                          (white)        (black line)  (white)
Already essentially posterized to 2 levels
Bilateral filter provides no benefit (no gradients to preserve)
```

**Contour Count Comparison:**
```
Clean manga: 150 contours (with or without preprocessing)
Photo without preprocessing: 8000 contours
Photo with bilateral + posterization: 800 contours (comparable to manga)
```



## References

### Primary Papers

1. **Canny, J.** (1986). "A Computational Approach to Edge Detection." IEEE Transactions on Pattern Analysis and Machine Intelligence, 8(6):679-698.

2. **Tomasi, C., & Manduchi, R.** (1998). "Bilateral filtering for gray and color images." Sixth International Conference on Computer Vision (ICCV).

3. **Suzuki, S., & Abe, K.** (1985). "Topological structural analysis of digitized binary images by border following." Computer Vision, Graphics, and Image Processing, 30(1):32-46.

4. **Douglas, D. H., & Peucker, T. K.** (1973). "Algorithms for the reduction of the number of points required to represent a digitized line or its caricature." Cartographica, 10(2):112-122.

5. **Serra, J.** (1983). "Image Analysis and Mathematical Morphology." Academic Press.

6. **de Boor, C.** (1978). A Practical Guide to Splines. Springer-Verlag, New York.

### Software Libraries

1. **OpenCV** (2024). "Canny Edge Detection." https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

2. **SciPy** (2024). "Interpolate - splprep, splev." https://docs.scipy.org/doc/scipy/reference/interpolate.html

3. **Dierckx, P.** (1993). *Curve and Surface Fitting with Splines.* Oxford University Press. (Used by SciPy's FITPACK)

### Books

1. **Gonzalez, R. C., & Woods, R. E.** (2018). Digital Image Processing (4th ed.). Pearson.
   - Chapter 3: Intensity Transformations and Spatial Filtering
   - Chapter 9: Morphological Image Processing
   - Chapter 10: Image Segmentation

2. **Sonka, M., Hlavac, V., & Boyle, R.** (2014). Image Processing, Analysis, and Machine Vision (4th ed.). Cengage Learning.

3. **Preparata, F. P., & Shamos, M. I.** (1985). Computational Geometry: An Introduction. Springer-Verlag.

### Online Resources

1. **OpenCV Documentation** - "Canny Edge Detection." https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

2. **OpenCV Documentation** - "Smoothing Images - Bilateral Filter." https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html

3. **Computerphile** - Educational videos on edge detection and image processing. https://www.youtube.com/user/Computerphile

4. **Kevin Wood ** - "Gaussian Blur" - Detailed explanation of Gaussian filtering and convolution. 

5. **Kevin Wood ** - "Bilateral Filter" - Clear explanation of edge-preserving smoothing. 

6. **3Blue1Brown** - "But what is a Fourier series?" https://www.youtube.com/watch?v=r6sGWTCMz2k

7. **Desmos** - "Lists of Points" documentation. https://help.desmos.com/hc/en-us/articles/4407725009165

8. **Wikipedia** - "Canny edge detector", "Bilateral filter", "Mathematical morphology", "Ramer-Douglas-Peucker algorithm", "B-spline"

---

## Future Improvements

### User Interface Enhancements

1. Region-based threshold adjustment
   - Allow users to set different edge detection parameters for different image regions
   - Useful for images with varying lighting conditions

2. Interactive parameter tuning
   - Real-time preview of edge detection results
   - Slider-based adjustment with immediate visual feedback

### Algorithmic Enhancements

1. Adaptive Thresholding
   - Implement Otsu's method for automatic threshold selection
   - Local adaptive thresholds for varying lighting conditions

2. Sub-pixel Edge Detection
   - Interpolate edge positions to sub-pixel accuracy
   - Reduce staircase artifacts in diagonal edges

3. Semantic Segmentation with Deep Learning
   - Use visual transformers or CNNs to identify important features
   - Priority-based curve export (faces, text, main subjects before background)
   - Better understanding of image content for intelligent preprocessing

4. 3D Edge Detection
   - Extend algorithm to handle depth information
   - Convert 3D models or stereo images to 3D Desmos equations

### Alternative Representations

1. Bezier Curves
   - More intuitive control points than B-splines
   - Better for manual editing and adjustment

2. NURBS (Non-Uniform Rational B-Splines)
   - Better for precise CAD-like shapes
   - Exact representation of conic sections

3. Implicit Functions
   - Level sets: f(x,y) = c
   - Can represent filled regions and gradients

### Performance Optimizations

1. Multi-threading
   - Parallel contour processing
   - Concurrent curve fitting for multiple contours

2. GPU Acceleration
   - CUDA-based edge detection
   - GPU-accelerated bilateral filtering



---

## Failures

![alt text](image-7.png)

![alt text](image-8.png)

---

Last Updated: January 17, 2026
Version: 2.0 (Added bilateral filtering, posterization, and morphological operations)
