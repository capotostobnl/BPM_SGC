"""
SGC Final Comparison Report Generator
Automatically generates the full PDF report with Statistics Table and Layouts.
"""
import os
import numpy as np
import glob
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors

# ================= CONFIGURATION =================
output_pdf = "SGC_Comparison_Report_Final.pdf"
img_dir = "Comparison_Images"

# BPM Counts per Cell (From your configuration)
# Cell 1-30
Nbpm = [6, 8, 8, 10, 9, 6, 10, 8, 6, 8, 8, 10, 6, 6, 6, 8, 9, 8, 10, 8, 8, 6, 9, 6, 6, 6, 8, 8, 6, 10]

# Data Directories for Stats Calculation
dirs = {
    "0dB": "0to31data",
    "10dB": "10to31data",
    "20dB": "20to31data"
}
# =================================================

def draw_bpm_image(c, bpm_name, x, y, w, h):
    """Draws the comparison image from the correct directory."""
    filename = f"{bpm_name}_Compare.png"
    full_path = os.path.join(img_dir, filename)
    
    if os.path.exists(full_path):
        c.drawImage(full_path, x, y, w, h)
    else:
        # Draw placeholder if missing
        c.saveState()
        c.setStrokeColorRGB(1, 0, 0)
        c.rect(x, y, w, h)
        c.setFillColorRGB(1, 0, 0)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + w/2, y + h/2, "MISSING")
        c.drawCentredString(x + w/2, y + h/2 - 10, filename)
        c.restoreState()

def get_stats_for_bpm(bpm_name):
    """Calculates spread stats."""
    filename = f"{bpm_name}_Data.txt"
    stats = {}
    for label, folder in dirs.items():
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            stats[label] = None
            continue
        try:
            data = np.loadtxt(path, delimiter=',')
            if data.ndim == 1: data = data.reshape(1, -1)
            stats[label] = {
                'x_spread': np.ptp(data[:, 2]), # PTP of X3
                'y_spread': np.ptp(data[:, 6])  # PTP of Y3
            }
        except:
            stats[label] = None
    return stats

def draw_stats_table(c):
    """Draws the summary statistics table."""
    c.setFont("Helvetica-Bold", 24)
    c.drawString(2*cm, 22*cm, "SGC Comparison: Spread Statistics")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, 21.2*cm, "Values = Peak-to-Peak spread (microns) of the Corrected Orbit.")
    
    y = 20*cm
    row_h = 0.6*cm
    col_name = 1.5*cm
    col_0 = 5.0*cm
    col_10 = 8.5*cm
    col_20 = 12.0*cm
    col_diff = 16.0*cm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col_name, y, "BPM Name")
    c.drawString(col_0, y, "0dB Spread")
    c.drawString(col_10, y, "10dB Spread")
    c.drawString(col_20, y, "20dB Spread")
    c.drawString(col_diff, y, "Imp. (0->10)")
    y -= 0.8*cm
    c.line(1*cm, y+0.5*cm, 20*cm, y+0.5*cm)

    # Get file list from 0dB folder
    files = sorted(glob.glob(os.path.join(dirs["0dB"], "*_Data.txt")))
    
    for fpath in files:
        bpm_name = os.path.basename(fpath).replace("_Data.txt", "")
        stats = get_stats_for_bpm(bpm_name)
        
        s0  = stats["0dB"]['x_spread'] if stats["0dB"] else 0
        s10 = stats["10dB"]['x_spread'] if stats["10dB"] else 0
        s20 = stats["20dB"]['x_spread'] if stats["20dB"] else 0
        
        if s10 > 10.0: c.setFillColorRGB(1, 0.8, 0.8)
        else: c.setFillColorRGB(1, 1, 1)
        c.rect(1*cm, y-0.15*cm, 19*cm, row_h, fill=1, stroke=0)
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        c.drawString(col_name, y, bpm_name)
        
        if stats["0dB"]: c.drawString(col_0, y, f"{s0:.2f}")
        if stats["10dB"]: c.drawString(col_10, y, f"{s10:.2f}")
        if stats["20dB"]: c.drawString(col_20, y, f"{s20:.2f}")
        
        if stats["0dB"] and stats["10dB"]:
            diff = s0 - s10
            c.setFillColor(colors.green if diff > 0 else colors.red)
            c.drawString(col_diff, y, f"{diff:+.2f}")
            c.setFillColor(colors.black)

        y -= row_h
        if y < 2*cm:
            c.showPage()
            y = 22*cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(col_name, y+0.5*cm, "BPM Name (Cont.)")
            y -= 0.8*cm

    c.showPage()

# ================= MAIN EXECUTION =================
c = Canvas(output_pdf)
c.setPageSize((43*cm, 24*cm))

# 1. Draw Stats
draw_stats_table(c)

# 2. Draw Layouts
for cell_idx in range(30):
    cell_num = cell_idx + 1
    num_bpms = Nbpm[cell_idx]
    
    # -- Page Setup --
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(1*cm, 23*cm, f"Cell {cell_num}: ARC BPMs 1 through 6:")
    
    # Draw Grid Lines
    c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)    # Left Vert
    c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)    # Bottom Horiz
    c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)  # Top Horiz
    c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)  # Mid Vert (Splitter)
    
    # ARC BPMs (Always present)
    # Row 1 (Top)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:1}}', 0*cm, 11.5*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:2}}', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:3}}', 17*cm, 11.5*cm, 9*cm, 12*cm)
    # Row 2 (Bottom)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:4}}', 0*cm, 0*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:5}}', 8.5*cm, 0*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:6}}', 17*cm, 0*cm, 9*cm, 12*cm)

    # ID BPMs (Right Side)
    if num_bpms > 6:
        # Draw ID Box
        c.drawString(26.5*cm, 23*cm, f"Cell {cell_num}: ID BPMs:")
        c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)   # Bottom
        c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)  # Left
        c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)  # Right
        c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm) # Top

        # Logic for ID BPM placement
        # BPM 7 is always Top-Left of ID box
        draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:7}}', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
        
        if num_bpms == 8:
            # BPM 8 is Bottom-Left
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:8}}', 25.5*cm, 0*cm, 9*cm, 12*cm)
        elif num_bpms >= 9:
            # BPM 8 is Top-Right
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:8}}', 34*cm, 11.5*cm, 9*cm, 12*cm)
            # BPM 9 is Bottom-Left
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:9}}', 25.5*cm, 0*cm, 9*cm, 12*cm)
            
            if num_bpms == 10:
                # BPM 10 is Bottom-Right
                draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:10}}', 34*cm, 0*cm, 9*cm, 12*cm)
    else:
        # Label "No ID BPMs" if none exist
        c.drawString(26.5*cm, 23*cm, f"Cell {cell_num}: No ID BPMs")
        # Draw empty box
        c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
        c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
        c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
        c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)

    c.showPage()
    print(f"Generated Page for Cell {cell_num}")

c.save()
print(f"Done! Report saved as: {output_pdf}")
