from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from base import ImageToDesmosConverter
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for matplotlib

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 5MB max file size (reduced for free tier)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or GIF'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get parameters from request
        manual_rotation = float(request.form.get('rotation', 0))
        segment_size = int(request.form.get('segment_size', 5))
        low_threshold = int(request.form.get('low_threshold', 30))
        high_threshold = int(request.form.get('high_threshold', 100))
        epsilon_factor = float(request.form.get('epsilon_factor', 0.0001))
        min_contour_area = int(request.form.get('min_contour_area', 20))
        blur_size = int(request.form.get('blur_size', 3))
        contours_only = request.form.get('contours_only', 'false').lower() == 'true'
        
        # Bilateral filter parameters
        use_bilateral = request.form.get('use_bilateral', 'false').lower() == 'true'
        bilateral_d = int(request.form.get('bilateral_d', 9))
        bilateral_sigma_color = int(request.form.get('bilateral_sigma_color', 75))
        bilateral_sigma_space = int(request.form.get('bilateral_sigma_space', 75))
        
        # NEW: Posterization parameters
        use_posterize = request.form.get('use_posterize', 'false').lower() == 'true'
        posterize_levels = int(request.form.get('posterize_levels', 4))
        
        # NEW: Morphology parameters
        use_morphology = request.form.get('use_morphology', 'false').lower() == 'true'
        morph_close = int(request.form.get('morph_close', 3))
        morph_open = int(request.form.get('morph_open', 2))
        
        # DEBUG: Print what we received
        print(f"\n{'='*60}")
        print(f"PARAMETERS RECEIVED:")
        print(f"  use_bilateral: {use_bilateral} (raw: '{request.form.get('use_bilateral', 'NOT SENT')}')")
        print(f"  use_posterize: {use_posterize} (raw: '{request.form.get('use_posterize', 'NOT SENT')}')")
        print(f"  posterize_levels: {posterize_levels}")
        print(f"  use_morphology: {use_morphology} (raw: '{request.form.get('use_morphology', 'NOT SENT')}')")
        print(f"  morph_close: {morph_close}, morph_open: {morph_open}")
        print(f"{'='*60}\n")
        
        # Process image
        converter = ImageToDesmosConverter(filepath)
        converter.load_and_preprocess(manual_rotation=manual_rotation)
        
        # Apply posterization if requested
        if use_posterize:
            converter.posterize(levels=posterize_levels)
        
        converter.detect_edges(
            low_threshold=low_threshold, 
            high_threshold=high_threshold,
            blur_size=blur_size, 
            min_contour_area=min_contour_area,
            use_bilateral=use_bilateral,
            bilateral_d=bilateral_d,
            bilateral_sigma_color=bilateral_sigma_color,
            bilateral_sigma_space=bilateral_sigma_space
        )
        
        # Apply morphological cleanup if requested
        if use_morphology:
            converter.clean_edges(close_kernel=morph_close, open_kernel=morph_open)
        
        converter.simplify_contours(epsilon_factor=epsilon_factor)
        
        # Generate output files - just pass filenames, base.py handles the output_dir
        base_filename = os.path.splitext(filename)[0]
        
        if contours_only:
            # Only export contours visualization
            contours_file = f"{base_filename}_contours_only.png"
            converter.export_contours_only(contours_file, show_original=True)
            
            # Get stats
            total_contours = len(converter.contours)
            total_points = sum(len(c) for c in converter.contours)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'contours_only': True,
                'output_image': f'/download/{contours_file}',
                'total_contours': total_contours,
                'total_points': total_points,
                'message': f'Preview complete: {total_contours} contours detected with {total_points} points'
            })
        else:
            # Full Desmos processing
            converter.fit_curves_parametric(segment_size=segment_size)
            
            desmos_file = f"{base_filename}_desmos.txt"
            console_file = f"{base_filename}_console.txt"
            output_png = f"{base_filename}_output.png"
            
            converter.export_to_desmos_file(desmos_file)
            converter.export_for_console(console_file)
            converter.export_to_high_res_png(output_png, dpi=150)
            
            # Read console input for display - now read from outputs folder
            console_path = os.path.join(app.config['OUTPUT_FOLDER'], console_file)
            with open(console_path, 'r') as f:
                console_input = f.read()
            
            # Get stats
            total_curves = sum(len(eq['segments']) for eq in converter.equations)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'contours_only': False,
                'console_input': console_input,
                'output_image': f'/download/{output_png}',
                'desmos_file': f'/download/{desmos_file}',
                'console_file': f'/download/{console_file}',
                'total_curves': total_curves,
                'message': f'Successfully converted image with {total_curves} polynomial curves!'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Use PORT environment variable for production deployment
    # Changed default port to 8080 to avoid macOS AirPlay conflict on port 5000
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
