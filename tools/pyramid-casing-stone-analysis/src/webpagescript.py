import os
import xml.etree.ElementTree as ET
import json

def clean_svg(svg_content):
    # Parse the SVG content
    tree = ET.ElementTree(ET.fromstring(svg_content))
    root = tree.getroot()

    # Remove namespace prefixes
    for elem in root.iter():
        _, _, elem.tag = elem.tag.rpartition('}')

    # Correct the xmlns attribute
    root.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
    root.attrib.pop('xmlns:ns0', None)  # Remove any non-standard xmlns attributes

    # Optionally add a viewBox attribute for scaling
    if 'viewBox' not in root.attrib:
        width = root.attrib.get('width', '800')
        height = root.attrib.get('height', '800')
        root.attrib['viewBox'] = f'0 0 {width} {height}'

    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')





def generate_html(svg_filenames):

    # Load all SVG contents and clean them
    cleaned_svg_contents = []
    for svg_filename in svg_filenames:
        with open(f'input/{svg_filename}', 'r', encoding='utf-8') as file:
            svg_content = file.read()
        cleaned_svg_contents.append(clean_svg(svg_content))

    # Escape the SVG contents for embedding in a JavaScript array
    escaped_svg_contents = [content.replace("'", r"\'") for content in cleaned_svg_contents]

    # Add a dark mode toggle button to the menu
    dark_mode_toggle_button = "<button id='dark-mode-toggle' onclick='toggleDarkMode()'>Toggle Dark Mode</button>"


    # Generate HTML content

   
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>History For Granite Pyramid Viewer by Thomas Grabe</title>
   <style>
    :root {{
        --background-color: #fff;
        --text-color: #000;
        --path-stroke-color: #000;
        --path-fill-color: lightgreen;
        --menu-background-color: #f0f0f0;
        --menu-border-color: #000;
    }}
    body {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    .dark-mode {{
        --background-color: #000;
        --text-color: #fff;
        --path-stroke-color: #d3d3d3;
        --path-fill-color: #fff; /* White fill for paths in dark mode */
        --menu-background-color: #333;
        --menu-border-color: #fff;
    }}
    
   #layout-container {{
        display: flex;
    }}
    
    .svg-container {{
        flex-grow: 1;  /* Added this line to make svg-container take up remaining space */
        width: calc(100%);  /* Adjusted this line */
        height: 100vh;  /* Adjusted this line */
        overflow: auto;  /* Added this line */
    }}
    
    .svg-container svg {{
            margin-left: 200px;  /* Added this line to set margin */
        width: 100%;
        height: 100%;
    }}
    
      .svg-container svg path {{
        fill: none; /* This ensures paths are not filled with green by default */
        stroke: black; /* Default stroke color */
    }}
    /* Add dark mode styles */
    body.dark-mode {{
        background-color: black;
        color: white;
    }}
 

    body.dark-mode .svg-container svg path {{
        fill: white; /* Set base path fill color to white in dark mode */
        stroke: #E0E0E0; /* Very light grey for dark mode */
    }}
    
    body.dark-mode #menu {{
        background-color: #333; /* Dark background for the menu */
        color: white; /* Text color for dark mode */
    }}
    
    .svg-container svg path:hover {{
        stroke: blue;
        stroke-width: 3;
    }}

    .svg-container svg path.highlighted {{
        fill: red;
        stroke: red;
        stroke-width: 2;
    }}
    
    .highlighted {{
        fill: red; /* Red fill for highlighted elements */
        stroke: red; /* Red stroke for highlighted elements */
        stroke-width: 2; /* Adjust stroke width as needed */
        --path-stroke-color: red;
        --path-fill-color: red;
    }}
    
    fieldset {{
            margin-top: 5px;
            padding: 5px;
            border: 2px solid #000;
        }}
    #title {{
        position: fixed;
        top: 10px;
        right: 10px;
        font-size: 36px;
    }}
    #menu {{
        background-color: var(--menu-background-color);
        border-color: var(--menu-border-color);
        position: fixed;
        top: 10px;
        left: 10px;
        border: 2px solid
        padding: 10px;
        border-radius: 8px;
        width: 200px;
        height: 100vh;  /* Updated this line to make menu full height */
        overflow-y: auto;  /* Added this line to make menu scrollable */
    
     }}
    #menu select, 
    #menu button, 
    #menu input, 
    #menu label {{
        display: block;
        margin-bottom: 10px;
    }}
    #heatmap-box {{
        background-color: #e0e0e0;
        border: 1px solid #ccc;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
    }}
    #heatmap-box input, 
    #heatmap-box select {{
        width: 100%;
        margin-bottom: 5px;
        padding: 5px;
        border-radius: 4px;
        border: 1px solid #ccc;
    }}
</style>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MG3315YS9B"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'G-MG3315YS9B');
</script>
</head>
<body class="dark-mode"> <!-- Add 'dark-mode' class here -->
     <div id="title"></div>
<div id="layout-container">  <!-- Wrapped menu and svg-container in a layout container -->
        <div id="menu">
            <button id="dark-mode-toggle" onclick="toggleDarkMode()">Switch to Light Mode</button>
   <button onclick="clearHighlights()">Clear all highlights</button>
     <fieldset>
        <legend>Toggle side</legend>
    {''.join(f'<button id="svg-button-{i}" onclick="selectSVG({i})">{filename.replace(".svg", "")}</button>' for i, filename in enumerate(svg_filenames))}
 </fieldset>
     <fieldset>
            <legend>Special blocks</legend>
    <button onclick="highlight('iscorner', 'True', 'lightgreen')">Highlight corner blocks</button>
    <button onclick="highlight('isoffloaded', 'True', 'blue')">Highlight offloaded blocks</button>
        </fieldset>
                        <fieldset>
                <legend>Highlight Angles</legend>

        <label for="angle-threshold">Min Angle Deviation:</label>
        <input type="range" id="angle-threshold" min="0" max="90" value="20" oninput="updateAngleHighlights(); document.getElementById('angle-value').innerText = this.value + '°'">
        <span id="angle-value">1°</span>
   <button id="angle-button">Highlight angled blocks</button>
            </fieldset>
    
      <fieldset>
            <legend>Heatmap</legend>
            <label for="heatmap-attribute-toggle">Heatmap attribute:</label>
            <select id="heatmap-attribute-toggle">
            <option value="width">% width all</option>
            <option value="widthpctcrse">% dev. course</option>
        </select>
            <label for="exclude-corners">Exclude Corners:</label>
            <input type="checkbox" id="exclude-corners">
    
            <label for="lower-percentile">Lower Percentile:</label>
            <input type="number" id="lower-percentile" min="0" max="100" value="5">
            <label for="upper-percentile">Upper Percentile:</label>
            <input type="number" id="upper-percentile" min="0" max="100" value="50">
            <button onclick="heatmap()">Heatmap</button>
        </fieldset>
    </div>
</div>
</div>
  <div class="svg-container" id="svg-container">
            {''.join(f'<div style="display: {"none" if i else "block"};">{content}</div>' for i, content in enumerate(escaped_svg_contents))}
        </div>

    </div>
    <script>
        let angleHighlightingActive = false;   
        let svgContents = {json.dumps(escaped_svg_contents)};
        let svgFilenames = {json.dumps(svg_filenames)};
        let currentIndex = 0;
        let isHighlighted = {{}};
        let isAngledHighlighted = false;
        let isHeatmapApplied = false;
        let highlightingStates = svgContents.map(() => ({{}}));

        let isDarkMode = true; // Set default state to true

        function toggleDarkMode() {{
            isDarkMode = !isDarkMode;
            document.body.classList.toggle('dark-mode', isDarkMode);
            updateSVG(currentIndex); // Call this to update the SVG styles
            // Update button text based on dark mode state
            document.getElementById('dark-mode-toggle').textContent = isDarkMode ? 'Switch to Light Mode' : 'Toggle Dark Mode';
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('angle-button').addEventListener('click', toggleAngleHighlighting);
            document.getElementById('angle-threshold').addEventListener('input', function() {{
                let angleValue = this.value;
                document.getElementById('angle-value').innerText = angleValue + '°';
                updateAngleHighlights();
            }});
        }});
        

        document.addEventListener('keydown', event => {{
            if (event.key === 'ArrowRight') {{
                currentIndex = (currentIndex + 1) % svgContents.length;
                updateSVG(currentIndex);
            }} else if (event.key === 'ArrowLeft') {{
                currentIndex = (currentIndex - 1 + svgContents.length) % svgContents.length;
                updateSVG(currentIndex);
            }}
        }});

        document.getElementById('svg-select').addEventListener('change', event => {{
            currentIndex = parseInt(event.target.value);
            updateSVG(currentIndex);
        }});
        
        // Updated Angle and Width filters with real-time highlighting
        document.getElementById('angle-threshold').addEventListener('input', updateAngleHighlights);
           document.getElementById('angle-button').addEventListener('click', toggleAngleHighlighting);  // Button click listener


       function selectSVG(index) {{
            currentIndex = index;
            updateSVG(currentIndex);

        }}



         function toggleAngleHighlighting() {{
            angleHighlightingActive = !angleHighlightingActive;
            updateAngleHighlights();
        }}

        // Updated highlight function with correct syntax for embedding attribute variable

         function highlight(attribute, value, color) {{
            let paths = document.querySelectorAll(`.svg-container svg *[${{attribute}}]`);  // Updated syntax
            let toggleOn = !isHighlighted[attribute + value];
            paths.forEach((path, pathIndex) => {{
                if (path.getAttribute(attribute) === value) {{
                    path.style.fill = toggleOn ? color : '';
                    highlightingStates[currentIndex][pathIndex] = toggleOn ? color : undefined;
                }}
            }});
            isHighlighted[attribute + value] = toggleOn;
        }}

function toggleHighlight(pathElement) {{
    pathElement.classList.toggle('highlighted');
}}

function toggleHighlight(pathElement) {{
    if (pathElement.classList.contains('highlighted')) {{
        pathElement.classList.remove('highlighted');
        pathElement.setAttribute('fill', 'none'); // Reset to original fill
        pathElement.setAttribute('stroke', 'black'); // Reset to original stroke
    }} else {{
        pathElement.classList.add('highlighted');
        pathElement.setAttribute('fill', 'red'); // Apply red fill
        pathElement.setAttribute('stroke', 'red'); // Apply red stroke
    }}
}}


        
        function toggleHighlight(event) {{
            event.target.classList.toggle('highlighted');
        }}


function updateAngleHighlights() {{
    let threshold = parseInt(document.getElementById('angle-threshold').value);
    let paths = document.querySelectorAll('.svg-container svg path');

    paths.forEach(path => {{
        const angleLeft = parseFloat(path.getAttribute('angle_left') || '0');
        const angleRight = parseFloat(path.getAttribute('angle_right') || '0');
        const totalAngle = angleLeft + angleRight;

        const isAngleLeftInRange = (-angleLeft - 90 < -threshold || -angleLeft - 90 > threshold);
        const isAngleRightInRange = (-angleRight - 90 < -threshold || -angleRight - 90 > threshold);

        if ((isAngleLeftInRange || isAngleRightInRange) && angleHighlightingActive) {{
            path.classList.add('highlighted');
            path.style.fill = 'red';
            path.style.stroke = 'red';
        }} else {{
            path.classList.remove('highlighted');
            path.style.fill = '';
            path.style.stroke = 'black';
        }}
    }});
}}




        

        function clearHighlights() {{
            document.querySelectorAll('.svg-container svg path').forEach((path, pathIndex) => {{
                path.style.fill = '';
                highlightingStates[currentIndex][pathIndex] = undefined;
            }});
            isHighlighted = {{}};
            isAngledHighlighted = false;
        }}
 
       function updateSVG(index) {{
    // Unhighlight all SVG buttons
    document.querySelectorAll('#menu button[id^="svg-button-"]').forEach(button => {{
        button.style.backgroundColor = '';



    }});

    // Highlight the currently selected SVG button
    document.getElementById('svg-button-' + index).style.backgroundColor = 'lightgrey';

    // Hide all SVGs
    document.querySelectorAll('.svg-container > div').forEach(div => {{
        div.style.display = 'none';
    }});

    // Display the selected SVG
    document.querySelectorAll('.svg-container > div')[index].style.display = 'block';

    // Apply the highlighting state from the array
    document.querySelectorAll('.svg-container svg path').forEach((path, pathIndex) => {{
        let color = highlightingStates[index][pathIndex];
        if (color !== undefined) {{
            path.style.fill = color;
       }}}});
        }}


    function selectSVG(index) {{
                currentIndex = index;
                updateSVG(currentIndex);
            }}

 
    function heatmap() {{
        let excludeCorners = document.getElementById('exclude-corners').checked;
        let attribute = document.getElementById('heatmap-attribute-toggle').value;
        let lowerPercentile = parseFloat(document.getElementById('lower-percentile').value) / 100;
        let upperPercentile = parseFloat(document.getElementById('upper-percentile').value) / 100;
        let paths = Array.from(document.querySelectorAll('.svg-container svg path'));
        if (isHeatmapApplied) {{
            paths.forEach(path => path.style.fill = '');
        }} else {{
            let values = paths.map(path => excludeCorners && path.getAttribute('iscorner') === 'True' ? null : parseFloat(path.getAttribute(attribute) || '0'));
            let filteredValues = values.filter(value => value !== null);
            filteredValues.sort((a, b) => a - b);
            let lowerValue = filteredValues[Math.floor(filteredValues.length * lowerPercentile)];
            let upperValue = filteredValues[Math.floor(filteredValues.length * upperPercentile)];

            paths.forEach((path, index) => {{
                let value = values[index];
                if (value !== null) {{
                    let normalizedValue = (value - lowerValue) / (upperValue - lowerValue);
                    let color = interpolateColor(normalizedValue);
                    path.style.fill = color;
                }}
            }});
        }}
        isHeatmapApplied = !isHeatmapApplied;
    }}

        function interpolateColor(value) {{
            let r, g, b;
            if (value < 0.5) {{
                // Interpolate between blue and yellow
                r = Math.floor(255 * (value * 2));
                g = Math.floor(255 * (value * 2));
                b = 255;
            }} else {{
                // Interpolate between yellow and red
                r = 255;
                g = 255 - Math.floor(255 * ((value - 0.5) * 2));
                b = 0;
            }}
            return `rgb(${{r}}, ${{g}}, ${{b}})`;
        }}





    </script>

</body>
</html>
    """

    return html_content


def main():
    # Get all SVG file names from the 'input' directory
    svg_filenames = [f for f in os.listdir('input') if f.endswith('.svg')]
    html_content = generate_html(svg_filenames)

    # Write the HTML content to a file
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

if __name__ == "__main__":
    main()
