import os
import cv2
import math 
import numpy as np
from psd_tools import PSDImage
from PIL import Image
import svgwrite
from math import atan2, degrees
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import parse
from xml.dom.minidom import parseString
from scipy.spatial import distance
from bs4 import BeautifulSoup
import re

# Initialize dictionaries at the beginning of your code or function
previous_course_bottom_row = {}
current_course_bottom_row = {}

# New global variables
course_width_sum = {}
course_block_count = {}

def sanitize_id(text):
    return ''.join(e if e.isalnum() else '_' for e in text)


def vectorize_blob_with_svgwrite(image, dwg, offset_x, offset_y, svg_filename, course, block_count):
    _, thresh = cv2.threshold(image, 254, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for idx, contour in enumerate(sorted(contours, key=lambda c: cv2.boundingRect(c)[0])):
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx_contour = cv2.approxPolyDP(contour, epsilon, True)
        points = approx_contour.squeeze()

        if np.ndim(points) > 1:
            # Update the block count for the current course
            block_count[course] = block_count.get(course, 0) + 1  # Update block count

            path_id = f"path_{svg_filename[0]}_{course}_{block_count[course]}"

            # Unique group ID
            group_id = f"{svg_filename[0]}_{course}_{block_count[course]}"

            # Initialize group with the unique ID
            group = dwg.g(id=group_id)

            d = f'M{points[0][0] + offset_x},{points[0][1] + offset_y}'
            for point in points[1:]:
                d += f' L{point[0] + offset_x},{point[1] + offset_y}'
            d += ' Z'

            path = dwg.path(d=d, id=path_id, stroke='black', fill='none')
            group.add(path)

            dwg.add(group)

    print(f"{svg_filename[0]}_{course}_{block_count.get(course, 0)}")


def calculate_angle(point, reference_corner):
    delta_x = point[0] - reference_corner[0]  # Calculate the change in x-coordinates
    delta_y = point[1] - reference_corner[1]  # Calculate the change in y-coordinates

    # Calculate the angle in radians using the arctangent function (atan2)
    angle_in_radians = math.atan2(delta_y, delta_x)

    # Convert the angle from radians to degrees
    angle_in_degrees = math.degrees(angle_in_radians)

    return angle_in_degrees

def estimate_corner_points(points):
    if all(isinstance(p, tuple) for p in points) and all(len(p) > 1 for p in points):
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
    
        raw_corners = [(min_x, min_y), (max_x, min_y), (min_x, max_y), (max_x, max_y)]
        derived_corners = []

        for raw_corner in raw_corners:
            closest_point = min(points, key=lambda x: distance.euclidean(x, raw_corner))
            derived_corners.append(closest_point)
        
        top_left, top_right, bottom_left, bottom_right = derived_corners

        return top_left, top_right, bottom_left, bottom_right
    else:
        print(f"Warning: Points contain an invalid tuple. Points: {points}")
        return None, None, None, None  # Return None for all corners if validation fails


def get_course_data(points, course_data, course, is_offloaded=False):
    top_left, top_right, bottom_left, bottom_right = estimate_corner_points(points)
    course_data.setdefault(course, []).append({
        'top_left': top_left,
        'top_right': top_right,
        'bottom_left': bottom_left,
        'bottom_right': bottom_right,
        'IsOffloaded': is_offloaded
    })


# Initialize these variables at the beginning of your script
global_min_x = float('inf')
global_max_x = float('-inf')

# Initialize these dictionaries at the beginning of your script
course_min_x = {}
course_max_x = {}

def update_path_attributes(path_element, points, course, block_number, course_data, total_paths):
    global current_course_bottom_row, global_min_x, global_max_x, course_min_x, course_max_x  # Existing global declarations
    global course_width_sum, course_block_count  # New global declarations
    top_left, top_right, bottom_left, bottom_right = estimate_corner_points(points)
    angle_top = round(calculate_angle(top_left, top_right))
    angle_bottom = round(calculate_angle(bottom_left, bottom_right))
    angle_left = round(calculate_angle(top_left, bottom_left))
    angle_right = round(calculate_angle(top_right, bottom_right))

    min_x = bottom_left[0]
    max_x = bottom_right[0]
    width = max_x - min_x 

    # Update course-specific min and max x-coordinates
    course_min_x[course] = min(course_min_x.get(course, float('inf')), min_x)
    course_max_x[course] = max(course_max_x.get(course, float('-inf')), max_x)
    course_width_sum[course] = course_width_sum.get(course, 0) + width
    course_block_count[course] = course_block_count.get(course, 0) + 1
    

    current_course_bottom_row[block_number] = (bottom_left[0], bottom_right[0])
    print(f"Updated current_course_bottom_row: {current_course_bottom_row}")
    print(f"previous_course_bottom_row: {previous_course_bottom_row}")
    print(f"top values current block: {min_x} {max_x}")
    # New average width and width percentage calculations
    
    if course_block_count[course] > 0:  # Avoid division by zero
        average_width = course_width_sum[course] / course_block_count[course]
    else:
        average_width = 0

    if average_width > 0:  # Avoid division by zero
        width_pct_crse = (width / average_width) * 100
    else:
        width_pct_crse = 0


    is_offloaded = True  # Assume True initially

    for bottom_left_x, bottom_right_x in previous_course_bottom_row.values():
        if (min_x <= bottom_left_x <= max_x) or (min_x <= bottom_right_x <= max_x):
            is_offloaded = False  # Set to False and exit loop if any value is within range
            break
        
    # New condition: Check if there is a block at all on the previous course within the interval
    if not any(bottom_left_x <= max_x and bottom_right_x >= min_x for bottom_left_x, bottom_right_x in previous_course_bottom_row.values()):
        is_offloaded = False  # Set to True if no block is found within the range




    # Update global min and max x-coordinates
    global_min_x = min(global_min_x, min_x)
    global_max_x = max(global_max_x, max_x)

    # Check for corner block
    is_corner = (
        (min_x <= global_min_x or max_x >= global_max_x) and
        (min_x <= course_min_x[course] or max_x >= course_max_x[course])
    )      

    path_element.attrib.update({
        
        'top_left_x': str(top_left[0]),
        'top_right_x': str(top_right[0]),
        'bottom_left_x': str(bottom_left[0]),
        'bottom_right_x': str(bottom_right[0]),
        'Width': str(width),
        'WidthPctCrse': f'{width_pct_crse:.2f}',  # Format as a string with 2 decimal places
        'angle_top': str(angle_top),
        'angle_bottom': str(angle_bottom),
        'angle_left': str(angle_left),
        'angle_right': str(angle_right),
        'Course': str(course),
        'IsCorner': str(is_corner),
        'IsOffloaded': str(is_offloaded)
    })
    
        
    get_course_data(points, course_data, course, is_offloaded)
    
def add_custom_attributes_with_elementtree(svg_path, svg_filename, course, course_data, block_count):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    for i in range(1, block_count[course] + 1):
        group_id = f"{svg_filename[0]}_{course}_{i}"
        group = root.find(f".//{{http://www.w3.org/2000/svg}}g[@id='{group_id}']")
        
        if group is not None:
            print(f"ID Matching: Match found for Group ID: {group_id}")

            total_paths = len(group.findall(".//{http://www.w3.org/2000/svg}path"))
      
            for idx, path_element in enumerate(group.findall(".//{http://www.w3.org/2000/svg}path")):
                print("Attribute Update: Updating attributes for path elements.")
                d_value = path_element.attrib['d']
                parsed_d_values = d_value.replace('M', '').replace('Z', '').split('L')
                points = [tuple(map(int, value.split(','))) for value in parsed_d_values]

                # Pass the block_number i as an argument here
                update_path_attributes(path_element, points, course, i, course_data, total_paths)

            print("File Write-back: Writing back to SVG.")
            tree.write(svg_path)
            print("File Write-back: Successfully wrote back to SVG.")
        else:
            print(f"ID Matching: Group with ID {group_id} not found.")



     
# Ensure each <path> element is individually selectable
def post_process_svg(svg_path):
    with open(svg_path, 'r') as file:
        svg_str = file.read()

    dom = parseString(svg_str)
    paths = dom.getElementsByTagNameNS('http://www.w3.org/2000/svg', 'path')
    groups = dom.getElementsByTagNameNS('http://www.w3.org/2000/svg', 'g')

    for path in paths:
        path.setAttribute('pointer-events', 'all')

    for group in groups:
        group.setAttribute('pointer-events', 'all')

    with open(svg_path, 'w') as file:
        file.write(dom.toprettyxml())
# Note: Keep the remaining parts of the code unchanged.

previous_course_bottom_row, current_course_bottom_row = None, None  # Initial global assignment

def reset_course_bottom_rows():
    global previous_course_bottom_row, current_course_bottom_row
    # The global declaration is done before any assignments.
    previous_course_bottom_row, current_course_bottom_row = {}, {}


def reset_global_max():
    global global_max_x, global_min_x, course_min_x, course_max_x
    global_max_x, global_min_x = float('-inf'), float('inf')
    course_min_x, course_max_x = {}, {}  # Resetting course-specific min and max x-coordinates



def process_psd(psd_path, svg_path):
    global previous_course_bottom_row, current_course_bottom_row, global_max_x, global_min_x
    reset_course_bottom_rows()  # Resets the course bottom rows.
    reset_global_max()          # Resets the global and course-specific max variables.
    print("Inside process_psd: Starting.")
    psd = PSDImage.open(psd_path)
    dwg = svgwrite.Drawing(svg_path, size=(psd.width, psd.height), profile='tiny')
    svg_filename = os.path.basename(svg_path).split('.')[0]
    course_data = {}
    course = 0
    block_count = {}  # Initialize block_count as an empty dictionary
    walk_layers(psd, dwg, svg_filename, course, course_data, block_count)  # Include block_count in function call
    
    dwg.save()
    print(f"Inside process_psd: Saved SVG. Course data: {course_data}")
    
    for course in range(1, len(block_count) + 1):  # Loop through each course
        print(f"Inside process_psd: Trying to call add_custom_attributes_with_elementtree for course {course}.")
        print("Type of count before calling add_custom_attributes_with_elementtree:", type(block_count[course]))
        print("Value of count:", block_count[course])
        add_custom_attributes_with_elementtree(svg_path, svg_filename, course, course_data, block_count)  # Passing specific block_count for the course
    
        # Moved this block of code here, after all layers have been processed
        global previous_course_bottom_row, current_course_bottom_row
        print(f"previous_course_bottom_row before flush: {previous_course_bottom_row}")
        print(f"current_course_bottom_row before flush: {current_course_bottom_row}")
        # Move current to previous and clear current
        previous_course_bottom_row = current_course_bottom_row
        current_course_bottom_row = {}
        print(f"previous_course_bottom_row after flush: {previous_course_bottom_row}")
        print(f"current_course_bottom_row after flush: {current_course_bottom_row}")
        
        print("Inside process_psd: Exiting.")


def numeric_sort(groups):
    """Sort the given list of groups based on the numerical value in the name."""
    numeric_part = lambda group: int(re.sub("[^0-9]", "", group.name) or 0)
    return sorted(groups, key=numeric_part)

def walk_layers(psd, dwg, svg_filename, course, course_data, block_count):
    global previous_course_bottom_row, current_course_bottom_row
    
    groups = [layer for layer in psd if layer.is_group()]
    sorted_groups = numeric_sort(groups)
    
    for layer in sorted_groups + [layer for layer in psd if not layer.is_group()]:
        if layer.is_group():
            course += 1
            block_count[course] = 0
            walk_layers(layer, dwg, svg_filename, course, course_data, block_count)
        else:
            process_layer(layer, dwg, svg_filename, course, course_data, block_count)


def process_layer(layer, dwg, svg_filename, course, course_data, block_count):
    print(f"Inside process_layer: Layer {layer.name}, Course {course}, Block Count: {block_count}")
   
    pil_image = layer.topil()
    rgba_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
    alpha_channel = rgba_image[:, :, 3]
    white_channel = cv2.cvtColor(rgba_image, cv2.COLOR_BGRA2GRAY)
    white_blob = cv2.bitwise_and(white_channel, white_channel, mask=alpha_channel)
    x, y = layer.left, layer.top
    vectorize_blob_with_svgwrite(white_blob, dwg, x, y, svg_filename, course, block_count)  # Corrected number of arguments
    # Assuming course_data is updated here. Add debug info.
    print(f"Before updating course_data: {course_data}")
    # Code that updates course_data
    print(f"After updating course_data: {course_data}")


def main():
    print("Starting main function.")
    block_count = [0]
    input_folder = './input'
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith('.psd'):
                print(f"Processing PSD file: {filename}")
                psd_path = os.path.join(root, filename)
                svg_filename = f"{filename.split('.')[0]}.svg"
                svg_path = os.path.join(root, svg_filename)
                process_psd(psd_path, svg_path)
    print("Main function execution complete.")


if __name__ == "__main__":
    main()
