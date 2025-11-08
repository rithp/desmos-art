"""
Demonstration: What Lagrange Interpolation Actually Does

This shows the difference between the polynomial equation itself
vs. the evaluated points that we export to Desmos.
"""

import numpy as np
from scipy.interpolate import lagrange
import matplotlib.pyplot as plt

# Example: Simple curve with 5 points
print("=" * 70)
print("LAGRANGE INTERPOLATION DEMONSTRATION")
print("=" * 70)

# Original points
x_points = np.array([0, 1, 2, 3, 4])
y_points = np.array([100, 150, 120, 180, 160])

print("\n1. ORIGINAL POINTS (from edge detection):")
print("   ", list(zip(x_points, y_points)))

# Create Lagrange polynomial
poly = lagrange(x_points, y_points)

print("\n2. LAGRANGE POLYNOMIAL COEFFICIENTS:")
print("   Degree:", poly.order)
print("   Coefficients (highest to lowest degree):")
for i, coef in enumerate(poly.coefficients):
    print(f"     x^{poly.order-i}: {coef:+.6f}")

print("\n3. POLYNOMIAL EQUATION:")
print("   y(x) = ", end="")
for i, coef in enumerate(poly.coefficients):
    power = poly.order - i
    if i > 0:
        print(" + " if coef >= 0 else " - ", end="")
        print(f"{abs(coef):.3f}*x^{power}", end="")
    else:
        print(f"{coef:.3f}*x^{power}", end="")
print()

print("\n4. EVALUATION (what we export to Desmos):")
# Sample the polynomial at more points for smooth curve
x_sample = np.linspace(0, 4, 20)
y_sample = poly(x_sample)

print("   We evaluate the polynomial at 20 points:")
points = list(zip(np.round(x_sample, 2), np.round(y_sample, 2)))
print("   ", points[:5], "... (15 more)")

print("\n5. WHY EVALUATE INSTEAD OF EQUATION?")
print("   ✓ Desmos accepts point lists: [(x1,y1), (x2,y2), ...]")
print("   ✓ High-degree polynomials are unstable")
print("   ✓ Point lists are faster to render")
print("   ✓ Easier to debug and visualize")

print("\n6. WHAT LAGRANGE MODE DOES:")
print("   1. Divides each contour into segments (e.g., 5 points each)")
print("   2. Fits a Lagrange polynomial to each segment")
print("   3. Evaluates the polynomial at many points (e.g., 20 per segment)")
print("   4. Exports the evaluated points to Desmos")

print("\n7. COMPARISON:")
print("   RAW mode:  Uses original edge pixels directly")
print("   LAGRANGE mode: Fits local polynomials for smoothing")
print("   SPLINE mode: Fits global B-splines for maximum smoothing")

print("\n" + "=" * 70)
print("VISUALIZATION")
print("=" * 70)

# Plot to show the difference
plt.figure(figsize=(12, 5))

# Plot 1: Original points and polynomial curve
plt.subplot(1, 2, 1)
plt.plot(x_points, y_points, 'ro', markersize=10, label='Original points')
plt.plot(x_sample, y_sample, 'b-', linewidth=2, label='Lagrange polynomial')
plt.grid(True, alpha=0.3)
plt.xlabel('x')
plt.ylabel('y')
plt.title('Lagrange Polynomial Interpolation')
plt.legend()

# Plot 2: Sampled points that go to Desmos
plt.subplot(1, 2, 2)
plt.plot(x_sample, y_sample, 'b.-', markersize=8, linewidth=1)
plt.plot(x_points, y_points, 'ro', markersize=10, label='Original edge points')
plt.grid(True, alpha=0.3)
plt.xlabel('x')
plt.ylabel('y')
plt.title('Points Exported to Desmos (polynomial evaluated)')
plt.legend()

plt.tight_layout()
plt.savefig('lagrange_explanation.png', dpi=150)
print("\n✓ Saved visualization to 'lagrange_explanation.png'")
print("\n💡 The output you see in desmos_output.txt is the EVALUATED polynomial,")
print("   not the coefficients. This is intentional and correct!")
