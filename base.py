import cv2
import numpy as np
from scipy.interpolate import splprep, splev, lagrange
import matplotlib.pyplot as plt
from pathlib import Path
import json
import urllib.parse

class ImageToDesmosConverter:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = None
        self.gray = None
        self.edges = None
        self.contours = []
        self.equations = []
        self.output_dir = Path(".")
    
    def load_and_preprocess(self, auto_rotate=True, manual_rotation=0, enhance_contrast=True):
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"Could not load image from {self.image_path}")
        
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            self.gray = clahe.apply(self.gray)
        
        if manual_rotation != 0:
            self.gray = self._rotate_image(self.gray, manual_rotation)
            self.image = self._rotate_image(self.image, manual_rotation)
            print(f"✓ Rotated {manual_rotation:.1f}°")
        
        print(f"✓ Loaded {self.gray.shape[1]}×{self.gray.shape[0]} image")
        return self
    
    def _rotate_image(self, img, angle):
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(255, 255, 255))
        return rotated
    
    def detect_edges(self, low_threshold=30, high_threshold=100, 
                     blur_size=3, min_contour_area=20):
        blurred = cv2.GaussianBlur(self.gray, (blur_size, blur_size), 0)
        self.edges = cv2.Canny(blurred, low_threshold, high_threshold)
        
        contours, _ = cv2.findContours(self.edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = [c for c in contours if cv2.contourArea(c) > min_contour_area]
        
        print(f"✓ Found {len(self.contours)} contours")
        return self
    
    def simplify_contours(self, epsilon_factor=0.0001):
        simplified = []
        for contour in self.contours:
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            simplified.append(approx)
        
        self.contours = simplified
        new_total = sum(len(c) for c in self.contours)
        print(f"✓ Simplified to {new_total} points")
        return self
    
    def fit_curves_parametric(self, segment_size=5):
        self.equations = []
        
        for contour in self.contours:
            if len(contour) < 2:
                continue
            
            points = contour.reshape(-1, 2)
            x = points[:, 0].astype(float)
            y = points[:, 1].astype(float)
            y = self.image.shape[0] - y
            
            n_points = len(x)
            
            if n_points <= segment_size:
                t_points = np.linspace(0, 1, n_points)
                try:
                    poly_x = lagrange(t_points, x)
                    poly_y = lagrange(t_points, y)
                    
                    self.equations.append({
                        'segments': [{
                            't_range': (0, 1),
                            'poly_x': poly_x,
                            'poly_y': poly_y
                        }]
                    })
                except:
                    pass
                continue
            
            polynomial_segments = []
            stride = max(1, segment_size - 2)
            
            for start_idx in range(0, n_points - segment_size + 1, stride):
                end_idx = min(start_idx + segment_size, n_points)
                
                seg_x = x[start_idx:end_idx]
                seg_y = y[start_idx:end_idx]
                t_points = np.linspace(0, 1, len(seg_x))
                
                try:
                    poly_x = lagrange(t_points, seg_x)
                    poly_y = lagrange(t_points, seg_y)
                    
                    polynomial_segments.append({
                        't_range': (start_idx / (n_points - 1), end_idx / (n_points - 1)),
                        'poly_x': poly_x,
                        'poly_y': poly_y
                    })
                except:
                    continue
            
            if len(polynomial_segments) > 0:
                self.equations.append({'segments': polynomial_segments})
        
        print(f"✓ Generated {len(self.equations)} parametric curves")
        return self
    
    def export_to_desmos_file(self, filename="desmos_output.txt"):
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("DESMOS OUTPUT - Parametric Polynomial Equations\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("INSTRUCTIONS:\n")
            f.write("1. Copy each pair of x(t) and y(t) equations below\n")
            f.write("2. In Desmos, paste them into expression boxes\n")
            f.write("3. Desmos will create parametric curves automatically\n\n")
            f.write("=" * 80 + "\n\n")
            
            curve_num = 1
            for eq in self.equations:
                for seg_idx, poly_seg in enumerate(eq['segments'], 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"CURVE {curve_num}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    poly_x = poly_seg['poly_x']
                    poly_y = poly_seg['poly_y']
                    
                    coeffs_x = poly_x.coefficients
                    coeffs_y = poly_y.coefficients
                    
                    f.write("x(t) = ")
                    terms_x = []
                    degree = len(coeffs_x) - 1
                    for i, coeff in enumerate(coeffs_x):
                        power = degree - i
                        if abs(coeff) > 1e-10:
                            if power == 0:
                                terms_x.append(f"{coeff:.4f}")
                            elif power == 1:
                                terms_x.append(f"{coeff:.4f}*t")
                            else:
                                terms_x.append(f"{coeff:.4f}*t^{power}")
                    
                    x_equation = " + ".join(terms_x).replace("+ -", "- ")
                    f.write(x_equation + "\n\n")
                    
                    f.write("y(t) = ")
                    terms_y = []
                    degree = len(coeffs_y) - 1
                    for i, coeff in enumerate(coeffs_y):
                        power = degree - i
                        if abs(coeff) > 1e-10:
                            if power == 0:
                                terms_y.append(f"{coeff:.4f}")
                            elif power == 1:
                                terms_y.append(f"{coeff:.4f}*t")
                            else:
                                terms_y.append(f"{coeff:.4f}*t^{power}")
                    
                    y_equation = " + ".join(terms_y).replace("+ -", "- ")
                    f.write(y_equation + "\n\n")
                    f.write("Domain: {0 ≤ t ≤ 1}\n\n")
                    
                    curve_num += 1
        
        print(f"✓ Exported {curve_num-1} polynomial segments to {filename}")
        return self

    def export_for_console(self, filename="desmos_console_input.txt"):
        """Exports all expressions into a single command for the Desmos console."""
        
        # Start with a command to clear the calculator
        all_expressions_str = "Calc.setBlank();\n"
        
        # Add each expression
        curve_id = 1
        for eq in self.equations:
            for poly_seg in eq['segments']:
                poly_x = poly_seg['poly_x']
                poly_y = poly_seg['poly_y']
                
                coeffs_x = poly_x.coefficients
                coeffs_y = poly_y.coefficients
                
                # Build x(t) equation string
                terms_x = []
                degree = len(coeffs_x) - 1
                for i, coeff in enumerate(coeffs_x):
                    power = degree - i
                    if abs(coeff) > 1e-10:
                        if power == 0:
                            terms_x.append(f"{coeff:.6f}")
                        elif power == 1:
                            terms_x.append(f"{coeff:.6f}t")
                        else:
                            terms_x.append(f"{coeff:.6f}t^{{{power}}}")
                x_latex = "+".join(terms_x).replace("+-", "-")
                
                # Build y(t) equation string
                terms_y = []
                degree = len(coeffs_y) - 1
                for i, coeff in enumerate(coeffs_y):
                    power = degree - i
                    if abs(coeff) > 1e-10:
                        if power == 0:
                            terms_y.append(f"{coeff:.6f}")
                        elif power == 1:
                            terms_y.append(f"{coeff:.6f}t")
                        else:
                            terms_y.append(f"{coeff:.6f}t^{{{power}}}")
                y_latex = "+".join(terms_y).replace("+-", "-")
                
                # Escape backslashes and quotes for the JavaScript string
                latex_str = f"\\\\left({x_latex},{y_latex}\\\\right)"
                
                # Create the Desmos API command for this expression
                expression_cmd = f"""
                Calc.setExpression({{
                  id: 'curve-{curve_id}',
                  type: 'expression',
                  latex: '{latex_str}',
                  color: '#000000',
                  lineWidth: '1',
                  lineOpacity: '1',
                  parametricDomain: {{ min: '0', max: '1' }}
                }});
                """
                all_expressions_str += expression_cmd.strip() + "\n"
                curve_id += 1
        
        with open(filename, 'w') as f:
            f.write(all_expressions_str)
            
        print(f"✓ Exported console commands to {filename}")
        return self
    
    def create_desmos_graph_state(self):
        """Create a Desmos graph state JSON that can be imported."""
        expressions = []
        
        # Add a parameter slider for t
        expressions.append({
            "type": "expression",
            "id": "t-slider",
            "latex": "t=0.5",
            "slider": {
                "hardMin": True,
                "hardMax": True,
                "min": "0",
                "max": "1",
                "step": "0.01"
            }
        })
        
        curve_id = 1
        for eq in self.equations:
            for poly_seg in eq['segments']:
                poly_x = poly_seg['poly_x']
                poly_y = poly_seg['poly_y']
                
                coeffs_x = poly_x.coefficients
                coeffs_y = poly_y.coefficients
                
                # Build x(t) equation string
                terms_x = []
                degree = len(coeffs_x) - 1
                for i, coeff in enumerate(coeffs_x):
                    power = degree - i
                    if abs(coeff) > 1e-10:
                        if power == 0:
                            terms_x.append(f"{coeff:.6f}")
                        elif power == 1:
                            terms_x.append(f"{coeff:.6f}t_{{{curve_id}}}")
                        else:
                            terms_x.append(f"{coeff:.6f}t_{{{curve_id}}}^{{{power}}}")
                
                x_latex = "+".join(terms_x).replace("+-", "-")
                
                # Build y(t) equation string
                terms_y = []
                degree = len(coeffs_y) - 1
                for i, coeff in enumerate(coeffs_y):
                    power = degree - i
                    if abs(coeff) > 1e-10:
                        if power == 0:
                            terms_y.append(f"{coeff:.6f}")
                        elif power == 1:
                            terms_y.append(f"{coeff:.6f}t_{{{curve_id}}}")
                        else:
                            terms_y.append(f"{coeff:.6f}t_{{{curve_id}}}^{{{power}}}")
                
                y_latex = "+".join(terms_y).replace("+-", "-")
                
                # Create parametric expression with unique parameter
                expression = {
                    "type": "expression",
                    "id": f"curve-{curve_id}",
                    "color": "#000000",
                    "latex": f"\\left({x_latex},{y_latex}\\right)",
                    "parametricDomain": {
                        "min": "0",
                        "max": "1"
                    },
                    "lineOpacity": "1",
                    "lineWidth": "1"
                }
                expressions.append(expression)
                curve_id += 1
        
        # Create the graph state
        graph_state = {
            "version": "9",
            "graph": {
                "viewport": {
                    "xmin": str(-50),
                    "ymin": str(-50),
                    "xmax": str(self.image.shape[1] + 50),
                    "ymax": str(self.image.shape[0] + 50)
                }
            },
            "expressions": {
                "list": expressions
            }
        }
        
        return graph_state
    
    def export_desmos_graph_state(self, filename="desmos_state.json"):
        """Export graph state to JSON file that can be imported to Desmos."""
        graph_state = self.create_desmos_graph_state()
        
        with open(filename, 'w') as f:
            json.dump(graph_state, f, indent=2)
        
        print(f"✓ Exported Desmos graph state to {filename}")
        print(f"  Total expressions: {len(graph_state['expressions']['list'])}")
        return self
    
    def export_to_svg(self, filename="output.svg"):
        """Export curves as SVG (vector graphics) file."""
        # Get image dimensions
        height, width = self.image.shape[:2]
        
        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="white"/>',
            '<g stroke="black" stroke-width="1" fill="none">'
        ]
        
        # Add each curve as a polyline
        for eq in self.equations:
            for seg in eq['segments']:
                # Sample the polynomial
                t_sample = np.linspace(0, 1, 50)
                x_sample = seg['poly_x'](t_sample)
                y_sample = seg['poly_y'](t_sample)
                
                # Create polyline points
                points = " ".join([f"{x:.2f},{y:.2f}" for x, y in zip(x_sample, y_sample)])
                svg_lines.append(f'<polyline points="{points}"/>')
        
        svg_lines.append('</g>')
        svg_lines.append('</svg>')
        
        with open(filename, 'w') as f:
            f.write('\n'.join(svg_lines))
        
        print(f"✓ Exported SVG to {filename}")
        return self
    
    def export_to_high_res_png(self, filename="output.png", dpi=300):
        """Export curves as high-resolution PNG."""
        height, width = self.image.shape[:2]
        
        # Create figure with exact dimensions
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=dpi)
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        ax.axis('off')
        
        # Plot all curves
        for eq in self.equations:
            for seg in eq['segments']:
                t_sample = np.linspace(0, 1, 50)
                x_sample = seg['poly_x'](t_sample)
                y_sample = seg['poly_y'](t_sample)
                ax.plot(x_sample, y_sample, 'k-', linewidth=0.5)
        
        plt.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0, facecolor='white')
        print(f"✓ Exported PNG to {filename}")
        plt.close()
        return self
    
    def visualize(self):
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        axes[0].imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
        axes[0].set_title("Original Image")
        axes[0].axis('off')
        
        axes[1].imshow(self.edges, cmap='gray')
        axes[1].set_title(f"Edge Detection ({len(self.contours)} contours)")
        axes[1].axis('off')
        
        axes[2].set_aspect('equal')
        axes[2].set_title("Detected Curves")
        axes[2].invert_yaxis()
        
        for eq in self.equations:
            for seg in eq['segments']:
                t_sample = np.linspace(0, 1, 50)
                x_sample = seg['poly_x'](t_sample)
                y_sample = seg['poly_y'](t_sample)
                axes[2].plot(x_sample, y_sample, 'b-', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig("processing_steps.png", dpi=150, bbox_inches='tight')
        print(f"✓ Saved visualization")
        plt.close()
        return self
    
    def process(self, output_file="desmos_output.txt", manual_rotation=0, segment_size=5, 
                export_svg=True, export_png=True, export_desmos_state=True):
        print("\n" + "=" * 50)
        print("🎨 Parametric Polynomial Converter")
        print("=" * 50)
        
        self.load_and_preprocess(manual_rotation=manual_rotation)
        self.detect_edges()
        self.simplify_contours()
        self.fit_curves_parametric(segment_size=segment_size)
        
        # Export in multiple formats
        self.export_to_desmos_file(output_file)
        self.export_for_console() # <--- Add this call
        
        if export_desmos_state:
            self.export_desmos_graph_state("desmos_state.json")
        
        if export_svg:
            self.export_to_svg("output.svg")
        
        if export_png:
            self.export_to_high_res_png("output.png", dpi=300)
        
        self.visualize()
        
        print("=" * 50)
        print(f"✅ DONE!")
        print(f"  - Desmos equations: {output_file}")
        if export_desmos_state:
            print(f"  - Desmos graph state: desmos_state.json")
            print(f"    → Go to: https://www.desmos.com/calculator")
            print(f"    → Click the menu (☰) → 'Import from...' → Upload desmos_state.json")
        print(f"  - Desmos console input: desmos_console_input.txt")
        print(f"    → Go to: https://www.desmos.com/calculator")
        print(f"    → Open developer console (F12 or Ctrl+Shift+I)")
        print(f"    → Copy content from desmos_console_input.txt and paste into console")
        if export_svg:
            print(f"  - SVG (vector): output.svg")
        if export_png:
            print(f"  - PNG (high-res): output.png")
        print("=" * 50)
        return self


if __name__ == "__main__":
    converter = ImageToDesmosConverter("image.png")
    converter.process(manual_rotation=0, segment_size=5, 
                     export_svg=True, export_png=True, export_desmos_state=True)
