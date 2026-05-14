import cv2
import numpy as np
import open3d as o3d
# import matplotlib.subplots
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.spatial import cKDTree
from scipy.spatial.distance import directed_hausdorff
from shapely.geometry import Polygon
from PIL import Image

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================

def extract_outer_contour(image_path, is_scan=False):
    """Reads an image, optionally erases scanner borders, and extracts the outermost contour."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not load image at {image_path}.")
    
    # NEW LOGIC: Erase the scanner bed shadow
    if is_scan:
        h, w = img.shape
        # Erase the outer 150 pixels (~6mm at 600 DPI) by painting them white (255).
        # This obliterates the black strip without changing the image's overall dimensions.
        border_thickness = 150
        cv2.rectangle(img, (0, 0), (w-1, h-1), (255), thickness=border_thickness)
    
    # Use Otsu's thresholding to separate part from background
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Extract only the external boundary
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    # Filter out dust and massive artifacts, just in case
    image_area = img.shape[0] * img.shape[1]
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 100 < area < (image_area * 0.90):
            valid_contours.append(cnt)
            
    if not valid_contours:
        raise ValueError("No valid parts found. The image might be completely blank or the part is too small.")

    # Grab the largest valid contour
    largest_contour = max(valid_contours, key=cv2.contourArea)
    return largest_contour.squeeze()

def get_tiff_scale(tiff_path, default_dpi=600):
    try:
        with Image.open(tiff_path) as img:
            dpi = img.info.get('dpi')
            if dpi is not None:
                return 25.4 / dpi[0] 
    except Exception as e:
        print(f"Could not read TIFF metadata: {e}")
    print(f"Warning: DPI metadata not found. Defaulting to {default_dpi} DPI.")
    return 25.4 / default_dpi

def align_contours_icp(source_coords, target_coords):
    source_3d = np.hstack((source_coords, np.zeros((len(source_coords), 1))))
    target_3d = np.hstack((target_coords, np.zeros((len(target_coords), 1))))
    
    source_pcd = o3d.geometry.PointCloud()
    source_pcd.points = o3d.utility.Vector3dVector(source_3d)
    target_pcd = o3d.geometry.PointCloud()
    target_pcd.points = o3d.utility.Vector3dVector(target_3d)
    
    threshold = 50.0 
    trans_init = np.eye(4) 
    reg_p2p = o3d.pipelines.registration.registration_icp(
        source_pcd, target_pcd, threshold, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000)
    )
    
    source_pcd.transform(reg_p2p.transformation)
    aligned_coords_3d = np.asarray(source_pcd.points)
    return aligned_coords_3d[:, :2]

# ==========================================
# 2. VISUALIZATION FUNCTION
# ==========================================

def visualize_results(model_coords, scan_coords, tree, max_pt_scan, max_pt_model, max_dev):
    print("Generating visualization plot...")
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    
    ax.plot(model_coords[:, 0], model_coords[:, 1], 'g-', linewidth=2, label='Model (Ideal)')
    ax.plot(scan_coords[:, 0], scan_coords[:, 1], 'b-', linewidth=1.5, alpha=0.7, label='Scanned Print')
    
    distances, indices = tree.query(scan_coords)
    error_lines = []
    for i in range(0, len(scan_coords), 15):
        p1 = scan_coords[i]
        p2 = model_coords[indices[i]]
        error_lines.append([p1, p2])
        
    lc = LineCollection(error_lines, colors='gray', linewidths=0.5, alpha=0.6, label='Deviation Vectors')
    ax.add_collection(lc)
    
    ax.plot([max_pt_scan[0], max_pt_model[0]], 
            [max_pt_scan[1], max_pt_model[1]], 
            'r-', linewidth=3, label=f'Max Error ({max_dev:.2f} mm)')
    
    ax.plot(max_pt_scan[0], max_pt_scan[1], 'ro', markersize=5) 
    
    plt.title("Print Deviation Analysis")
    plt.xlabel("Millimeters (X)")
    plt.ylabel("Millimeters (Y)")
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.5)
    ax.invert_yaxis()
    plt.show()

# ==========================================
# 3. MAIN EXECUTION PIPELINE
# ==========================================

def run_inspection(scan_path, model_path, known_cad_width_mm):
    print("Starting automated TIFF inspection...\n")

    # FIX: Pass 'is_scan=True' so the script erases the scanner borders
    raw_scan_coords = extract_outer_contour(scan_path, is_scan=True)
    raw_model_coords = extract_outer_contour(model_path, is_scan=False)

    scan_scale_factor = get_tiff_scale(scan_path)
    scan_coords_mm = raw_scan_coords * scan_scale_factor
    
    model_min_x = np.min(raw_model_coords[:, 0])
    model_max_x = np.max(raw_model_coords[:, 0])
    model_scale_factor = known_cad_width_mm / (model_max_x - model_min_x)
    model_coords_mm = raw_model_coords * model_scale_factor

    # FIX: Center both parts at the origin (0,0) before alignment
    scan_coords_mm = scan_coords_mm - np.mean(scan_coords_mm, axis=0)
    model_coords_mm = model_coords_mm - np.mean(model_coords_mm, axis=0)

    print("Aligning scanned print to model via ICP...")
    aligned_scan_mm = align_contours_icp(scan_coords_mm, model_coords_mm)

    print("Calculating metrics...")
    tree = cKDTree(model_coords_mm)
    distances, _ = tree.query(aligned_scan_mm)
    mean_deviation = np.mean(distances)
    
    forward_h = directed_hausdorff(aligned_scan_mm, model_coords_mm)
    backward_h = directed_hausdorff(model_coords_mm, aligned_scan_mm)
    
    if forward_h[0] >= backward_h[0]:
        max_deviation = forward_h[0]
        max_pt_scan = aligned_scan_mm[forward_h[1]]
        max_pt_model = model_coords_mm[forward_h[2]]
    else:
        max_deviation = backward_h[0]
        max_pt_model = model_coords_mm[backward_h[1]]
        max_pt_scan = aligned_scan_mm[backward_h[2]]

    scan_poly = Polygon(aligned_scan_mm).buffer(0)
    model_poly = Polygon(model_coords_mm).buffer(0)
    shape_match_percentage = (scan_poly.intersection(model_poly).area / scan_poly.union(model_poly).area) * 100

    print("\n" + "="*40)
    print("INSPECTION RESULTS:")
    print("="*40)
    print(f"Mean Deviation (Average Error): {mean_deviation:.3f} mm")
    print(f"Max Deviation (Worst Error):    {max_deviation:.3f} mm")
    print(f"Overall Shape Match (IoU):      {shape_match_percentage:.2f} %")
    print("="*40 + "\n")

    visualize_results(model_coords_mm, aligned_scan_mm, tree, max_pt_scan, max_pt_model, max_deviation)

# ==========================================
# RUN THE SCRIPT
# ==========================================
if __name__ == "__main__":
    SCANNED_IMAGE_FILE = "C:\\Users\\pjvth\\High-tech Engineering\\Thesis\\Resultaten\\Side view pictures\\L-shape\\Ori 45\\L-shape_45_ori_2.tif"
    MODEL_IMAGE_FILE = "C:\\Users\\pjvth\\High-tech Engineering\\Thesis\\Resultaten\\Side view pictures\\L-shape\\L-shape_model_100_b.png"

    # Bounding-box widths

    # T-shape = 73.11744
    # L-shape = 49.0
    # Arc	= 98.0 / 74.896559
    # Bracket = 58.233737 for new 75% , 56.25 for 90 printhead 75%
    # Lug	= 98.5

    CAD_MODEL_WIDTH_MM = 49.0
    
    run_inspection(SCANNED_IMAGE_FILE, MODEL_IMAGE_FILE, CAD_MODEL_WIDTH_MM)