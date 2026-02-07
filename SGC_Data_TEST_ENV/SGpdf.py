"""Static Gain Calibration Report Generator Script
5/20/2025
"""
import os
import numpy as np
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors

# --- HELPER: Fix Image Paths ---
def draw_bpm_image(canvas, filename, x, y, w, h):
    full_path = os.path.join("Images", filename)
    if os.path.exists(full_path):
        canvas.drawImage(full_path, x, y, w, h)
    else:
        canvas.saveState()
        canvas.setStrokeColorRGB(1, 0, 0)
        canvas.rect(x, y, w, h)
        canvas.drawString(x + 1*cm, y + h/2, f"MISSING: {filename}")
        canvas.restoreState()

# ==========================================
# PART 1: DATA PROCESSING & SORTING
# ==========================================
report_file = "Data/RmsData.txt"
bpm_data = []
stats_info = []

if os.path.exists(report_file):
    # 1. Read Data
    raw_data = []
    with open(report_file, 'r') as f:
        raw_data = [line.strip().split(',') for line in f if line.strip()]

    # 2. Parse Valid Rows (RX4=Index 3, RY4=Index 7)
    x_vals = []
    y_vals = []
    
    parsed_rows = []
    for row in raw_data:
        if len(row) < 9: continue
        try:
            val_x = float(row[3])
            val_y = float(row[7])
            name = row[8]
            
            x_vals.append(val_x)
            y_vals.append(val_y)
            parsed_rows.append({'name': name, 'x': val_x, 'y': val_y})
        except ValueError:
            continue

    if len(x_vals) > 0:
        # 3. Calculate Thresholds (Mean + 3 Sigma)
        mean_x = np.mean(x_vals)
        limit_x = mean_x + (3 * np.std(x_vals))
        
        mean_y = np.mean(y_vals)
        limit_y = mean_y + (3 * np.std(y_vals))

        stats_info = [
            f"Total BPMs: {len(parsed_rows)}",
            f"X Threshold: {limit_x:.3f} um (Mean: {mean_x:.3f})",
            f"Y Threshold: {limit_y:.3f} um (Mean: {mean_y:.3f})"
        ]

        # 4. Score and Sort
        # We calculate a 'severity' score to sort by.
        # Score > 1.0 means it failed. Higher is worse.
        for row in parsed_rows:
            score_x = row['x'] / limit_x
            score_y = row['y'] / limit_y
            row['severity'] = max(score_x, score_y) # Sort by worst axis
            row['failed'] = (row['x'] > limit_x) or (row['y'] > limit_y)

        # Sort descending (Worst at top)
        bpm_data = sorted(parsed_rows, key=lambda k: k['severity'], reverse=True)

# ==========================================
# PART 2: GENERATE TABLE PAGES
# ==========================================
c = Canvas('SRreport.pdf')
c.setPageSize((43*cm, 24*cm))

# Constants for Table Layout
y_start = 20*cm
row_height = 0.8*cm
col_name = 2*cm
col_x = 10*cm
col_y = 18*cm
col_status = 26*cm

def draw_header(c, y):
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(col_name, y, "BPM Name")
    c.drawString(col_x, y, "X RMS (um)")
    c.drawString(col_y, y, "Y RMS (um)")
    c.drawString(col_status, y, "Status")
    c.line(1*cm, y - 0.2*cm, 40*cm, y - 0.2*cm)
    return y - row_height

# --- Draw Title Page & Stats ---
c.setFont("Helvetica-Bold", 24)
c.drawString(2*cm, 22*cm, "Static Gain Calibration: Full Report")

c.setFont("Helvetica", 12)
ty = 21.5*cm
for line in stats_info:
    c.drawString(20*cm, ty, line)
    ty -= 0.5*cm

# --- Draw Table Loop ---
current_y = draw_header(c, y_start)

for row in bpm_data:
    # 1. Background Color Rect
    if row['failed']:
        c.setFillColorRGB(1, 0.8, 0.8) # Light Red
    else:
        c.setFillColorRGB(0.8, 1, 0.8) # Light Green
    
    # Draw rect for the whole row
    c.rect(1.5*cm, current_y - 0.2*cm, 38*cm, row_height, fill=1, stroke=0)

    # 2. Text Data
    c.setFillColorRGB(0, 0, 0) # Back to Black text
    c.setFont("Helvetica", 12)
    
    c.drawString(col_name + 0.5*cm, current_y + 0.2*cm, row['name'])
    
    # Bold the specific value that failed
    if row['x'] > limit_x: c.setFont("Helvetica-Bold", 12)
    else: c.setFont("Helvetica", 12)
    c.drawString(col_x, current_y + 0.2*cm, f"{row['x']:.3f}")

    if row['y'] > limit_y: c.setFont("Helvetica-Bold", 12)
    else: c.setFont("Helvetica", 12)
    c.drawString(col_y, current_y + 0.2*cm, f"{row['y']:.3f}")

    c.setFont("Helvetica-Bold", 12)
    status_text = "FAIL" if row['failed'] else "PASS"
    c.drawString(col_status, current_y + 0.2*cm, status_text)

    # 3. Move Cursor / Page Break
    current_y -= row_height
    
    if current_y < 2*cm:
        c.showPage() # Create new page
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, 22*cm, "BPM Statistics (Continued)")
        current_y = draw_header(c, 21*cm)

c.showPage() # End the table section

# Reset colors for the graphs
c.setFillColorRGB(0, 0, 0) 
c.setStrokeColorRGB(0, 0, 0)


# Note that all spacial entries such as X, Y coordinates or item height
# and width must be multiplies by the constant 'cm' which was imported
# above and converts the centimeter units into the native units used in
# Reportlab's internal code.

# Cell 1:
# Syntax: c.drawImage('Imagefile.png', X, Y, Width, Height)
# where:
#       'Imagefile.png' is the name of the BPM image PNG file created by
#        the data collection script.
#       'X, Y' are the coordinates of the lower left corner of the image
#       'Width, Height' are the dimensions of the image
c.drawImage('Images/SR:C01-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C01-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C01-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C01-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C01-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C01-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
# Syntax: c.drawString(X, Y, 'string')
# where:
#    'X, Y' are the coodinates on the page for the string
#   'string' is the string to be displayed at that location
c.drawString(1*cm, 23*cm, "Cell 1: ARC BPMs 1 through 6:")
# Syntax: c.line(X1, Y1, X2, Y2)
# where:
#   'X1, Y1' are the start coodinates on the page for the line
#   'X2, Y2' are the end coodinates on the page for the line
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 1: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

#  2:
c.drawImage('Images/SR:C02-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C02-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 2: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 2: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 3:
c.drawImage('Images/SR:C03-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C03-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 3: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 3: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 4:
c.drawImage('Images/SR:C04-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C04-BI{BPM:10}.png', 34*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 4: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 4: ID BPMs 7 through 10:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 5:
c.drawImage('Images/SR:C05-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C05-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 5: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 5: ID BPMs 7 through 9:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 6:
c.drawImage('Images/SR:C06-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C06-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C06-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C06-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C06-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C06-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 6: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 6: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 7:
c.drawImage('Images/SR:C07-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C07-BI{BPM:10}.png', 34*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 7: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 7: ID BPMs 7 through 10:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 8:
c.drawImage('Images/SR:C08-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C08-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 8: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 8: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 9:
c.drawImage('Images/SR:C09-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C09-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C09-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C09-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C09-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C09-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 9: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 9: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 10:
c.drawImage('Images/SR:C10-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C10-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 10: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 10: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 11:
c.drawImage('Images/SR:C11-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C11-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 11: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 11: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 12:
c.drawImage('Images/SR:C12-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C12-BI{BPM:10}.png', 34*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 12: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cel1 12: ID BPMs 7 through 10:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 13:
c.drawImage('Images/SR:C13-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C13-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C13-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C13-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C13-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C13-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 13: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 13: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 14:
c.drawImage('Images/SR:C14-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C14-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C14-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C14-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C14-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C14-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 14: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 14: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 15:
c.drawImage('Images/SR:C15-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C15-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C15-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C15-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C15-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C15-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 15: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 15: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 16:
c.drawImage('Images/SR:C16-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C16-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 16: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 16: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 17:
c.drawImage('Images/SR:C17-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C17-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 17: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 17: ID BPMs 7 through 9:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 18:
c.drawImage('Images/SR:C18-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C18-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 18: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 18: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 19:
c.drawImage('Images/SR:C19-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C19-BI{BPM:10}.png', 34*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 19: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 19: ID BPMs 7 through 10:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 20:
c.drawImage('Images/SR:C20-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C20-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 20: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 20: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 21:
c.drawImage('Images/SR:C21-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C21-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 21: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 21: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 22:
c.drawImage('Images/SR:C22-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C22-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C22-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C22-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C22-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C22-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 22: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 22: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 23:
c.drawImage('Images/SR:C23-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C23-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 23: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 23: ID BPMs 7 through 9:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 24:
c.drawImage('Images/SR:C24-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C24-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C24-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C24-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C24-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C24-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 24: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 24: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 25:
c.drawImage('Images/SR:C25-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C25-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C25-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C25-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C25-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C25-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 25: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 25: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 26:
c.drawImage('Images/SR:C26-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C26-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C26-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C26-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C26-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C26-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 26: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 26: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 27:
c.drawImage('Images/SR:C27-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C27-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 27: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 27: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 28:
c.drawImage('Images/SR:C28-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C28-BI{BPM:8}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 28: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 28: ID BPMs 7 through 8:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 29:
c.drawImage('Images/SR:C29-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C29-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C29-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C29-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C29-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C29-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 29: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 29: No ID BPMs")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()

# Cell 30:
c.drawImage('Images/SR:C30-BI{BPM:1}.png', 0*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:2}.png', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:3}.png', 17*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:7}.png', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:8}.png', 34*cm, 11.5*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:4}.png', 0*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:5}.png', 8.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:6}.png', 17*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:9}.png', 25.5*cm, 0*cm, 9*cm, 12*cm)
c.drawImage('Images/SR:C30-BI{BPM:10}.png', 34*cm, 0*cm, 9*cm, 12*cm)
c.drawString(1*cm, 23*cm, "Cell 30: ARC BPMs 1 through 6:")
c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
c.drawString(26.5*cm, 23*cm, "Cell 30: ID BPMs 7 through 10:")
c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)
c.showPage()
c.save()
