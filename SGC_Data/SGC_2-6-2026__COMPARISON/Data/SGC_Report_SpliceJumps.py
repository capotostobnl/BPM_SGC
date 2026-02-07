"""
SGC Final Report: Splice Jump Analysis
Calculates the position discontinuity (jump) at 10dB and 20dB splice points.
"""
import os
import numpy as np
import glob
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors

# ================= CONFIGURATION =================
output_pdf = "SGC_Report_Splice_Analysis.pdf"
img_dir = "Comparison_Images"

# BPM Counts (Cell 1-30)
Nbpm = [6, 8, 8, 10, 9, 6, 10, 8, 6, 8, 8, 10, 6, 6, 6, 8, 9, 8, 10, 8, 8, 6, 9, 6, 6, 6, 8, 8, 6, 10]

# Data Directories
dirs = {
    "0dB": "0to31data",
    "10dB": "10to31data",
    "20dB": "20to31data"
}
# =================================================

def get_splice_jumps(bpm_name):
    """
    Calculates the 'Jump' in X and Y at 10dB and 20dB.
    Returns dictionary with jump values or None if data missing.
    """
    filename = f"{bpm_name}_Data.txt"
    paths = {k: os.path.join(v, filename) for k, v in dirs.items()}
    
    # We need all three files to exist to do a full splice analysis
    if not all(os.path.exists(p) for p in paths.values()):
        return None

    try:
        # --- LOAD DATA ---
        # Data Format: Cols 2=X3 (Corrected), 6=Y3 (Corrected)
        
        # Load 0dB Run (Starts at 0dB)
        d0 = np.loadtxt(paths["0dB"], delimiter=',')
        if d0.ndim == 1: d0 = d0.reshape(1, -1)
        # 10dB is at Index 10
        val_0_at_10dB_X = d0[10, 2]
        val_0_at_10dB_Y = d0[10, 6]

        # Load 10dB Run (Starts at 10dB)
        d10 = np.loadtxt(paths["10dB"], delimiter=',')
        if d10.ndim == 1: d10 = d10.reshape(1, -1)
        # 10dB is at Index 0
        val_10_at_10dB_X = d10[0, 2]
        val_10_at_10dB_Y = d10[0, 6]
        # 20dB is at Index 10
        val_10_at_20dB_X = d10[10, 2]
        val_10_at_20dB_Y = d10[10, 6]

        # Load 20dB Run (Starts at 20dB)
        d20 = np.loadtxt(paths["20dB"], delimiter=',')
        if d20.ndim == 1: d20 = d20.reshape(1, -1)
        # 20dB is at Index 0
        val_20_at_20dB_X = d20[0, 2]
        val_20_at_20dB_Y = d20[0, 6]

        # --- CALCULATE JUMPS ---
        return {
            'jump_10_X': abs(val_10_at_10dB_X - val_0_at_10dB_X),
            'jump_10_Y': abs(val_10_at_10dB_Y - val_0_at_10dB_Y),
            'jump_20_X': abs(val_20_at_20dB_X - val_10_at_20dB_X),
            'jump_20_Y': abs(val_20_at_20dB_Y - val_10_at_20dB_Y)
        }

    except Exception as e:
        # If any index error occurs (e.g. incomplete file), return None
        return None

def draw_stats_table(c):
    """Draws the Splice Jump Summary Table."""
    c.setFont("Helvetica-Bold", 24)
    c.drawString(2*cm, 22*cm, "Splice Analysis: Position Jumps")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, 21.2*cm, "Values represent the position discontinuity (jump) if tables are spliced together.")
    c.drawString(2*cm, 20.8*cm, "Jump @ 10dB = |Run2(10dB) - Run1(10dB)|. Jump @ 20dB = |Run3(20dB) - Run2(20dB)|")
    
    y = 20*cm
    row_h = 0.6*cm
    
    # Columns
    col_name = 1.5*cm
    col_10x = 6.0*cm
    col_10y = 9.0*cm
    col_20x = 13.0*cm
    col_20y = 16.0*cm
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col_name, y, "BPM Name")
    c.drawString(col_10x, y, "X Jump (10dB)")
    c.drawString(col_10y, y, "Y Jump (10dB)")
    c.drawString(col_20x, y, "X Jump (20dB)")
    c.drawString(col_20y, y, "Y Jump (20dB)")
    
    y -= 0.8*cm
    c.line(1*cm, y+0.5*cm, 20*cm, y+0.5*cm)

    # Get file list from 0dB folder
    files = sorted(glob.glob(os.path.join(dirs["0dB"], "*_Data.txt")))
    
    for fpath in files:
        bpm_name = os.path.basename(fpath).replace("_Data.txt", "")
        jumps = get_splice_jumps(bpm_name)
        
        if jumps:
            # Highlight Logic: If jump > 10um, mark red
            is_bad = max(jumps.values()) > 10.0
            if is_bad: c.setFillColorRGB(1, 0.8, 0.8)
            else: c.setFillColorRGB(1, 1, 1)
            
            c.rect(1*cm, y-0.15*cm, 19*cm, row_h, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            
            c.setFont("Helvetica", 9)
            c.drawString(col_name, y, bpm_name)
            
            # 10dB Jumps
            if jumps['jump_10_X'] > 10: c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.red)
            else: c.setFont("Helvetica", 9); c.setFillColor(colors.black)
            c.drawString(col_10x, y, f"{jumps['jump_10_X']:.2f} um")
            
            if jumps['jump_10_Y'] > 10: c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.red)
            else: c.setFont("Helvetica", 9); c.setFillColor(colors.black)
            c.drawString(col_10y, y, f"{jumps['jump_10_Y']:.2f} um")

            # 20dB Jumps
            if jumps['jump_20_X'] > 10: c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.red)
            else: c.setFont("Helvetica", 9); c.setFillColor(colors.black)
            c.drawString(col_20x, y, f"{jumps['jump_20_X']:.2f} um")
            
            if jumps['jump_20_Y'] > 10: c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.red)
            else: c.setFont("Helvetica", 9); c.setFillColor(colors.black)
            c.drawString(col_20y, y, f"{jumps['jump_20_Y']:.2f} um")

        else:
            # Missing Data Case
            c.setFillColorRGB(0.9, 0.9, 0.9)
            c.rect(1*cm, y-0.15*cm, 19*cm, row_h, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(col_name, y, bpm_name)
            c.drawString(col_10x, y, "DATA MISSING")

        y -= row_h
        if y < 2*cm:
            c.showPage()
            y = 22*cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(col_name, y+0.5*cm, "BPM Name (Cont.)")
            y -= 0.8*cm

    c.showPage()

def draw_bpm_image(c, bpm_name, x, y, w, h):
    """Draws comparison image."""
    filename = f"{bpm_name}_Compare.png"
    full_path = os.path.join(img_dir, filename)
    if os.path.exists(full_path):
        c.drawImage(full_path, x, y, w, h)
    else:
        c.saveState()
        c.setStrokeColorRGB(1, 0, 0)
        c.rect(x, y, w, h)
        c.setFillColorRGB(1, 0, 0)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x+w/2, y+h/2, "MISSING")
        c.drawCentredString(x+w/2, y+h/2-10, filename)
        c.restoreState()

# ================= MAIN EXECUTION =================
c = Canvas(output_pdf)
c.setPageSize((43*cm, 24*cm))

# 1. Draw Stats Table
draw_stats_table(c)

# 2. Draw Layouts
for cell_idx in range(30):
    cell_num = cell_idx + 1
    num_bpms = Nbpm[cell_idx]
    
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(1*cm, 23*cm, f"Cell {cell_num}: ARC BPMs 1 through 6:")
    
    # Grid
    c.line(0.2*cm, 0.2*cm, 0.2*cm, 23.5*cm)
    c.line(0.2*cm, 0.2*cm, 25.4*cm, 0.2*cm)
    c.line(0.2*cm, 23.5*cm, 25.4*cm, 23.5*cm)
    c.line(25.4*cm, 0.2*cm, 25.4*cm, 23.5*cm)
    
    # ARC BPMs
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:1}}', 0*cm, 11.5*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:2}}', 8.5*cm, 11.5*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:3}}', 17*cm, 11.5*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:4}}', 0*cm, 0*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:5}}', 8.5*cm, 0*cm, 9*cm, 12*cm)
    draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:6}}', 17*cm, 0*cm, 9*cm, 12*cm)

    # ID BPMs
    if num_bpms > 6:
        c.drawString(26.5*cm, 23*cm, f"Cell {cell_num}: ID BPMs:")
        c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
        c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
        c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
        c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)

        draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:7}}', 25.5*cm, 11.5*cm, 9*cm, 12*cm)
        
        if num_bpms == 8:
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:8}}', 25.5*cm, 0*cm, 9*cm, 12*cm)
        elif num_bpms >= 9:
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:8}}', 34*cm, 11.5*cm, 9*cm, 12*cm)
            draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:9}}', 25.5*cm, 0*cm, 9*cm, 12*cm)
            if num_bpms == 10:
                draw_bpm_image(c, f'SR:C{cell_num:02d}-BI{{BPM:10}}', 34*cm, 0*cm, 9*cm, 12*cm)
    else:
        c.drawString(26.5*cm, 23*cm, f"Cell {cell_num}: No ID BPMs")
        c.line(25.7*cm, 0.2*cm, 42.7*cm, 0.2*cm)
        c.line(25.7*cm, 0.2*cm, 25.7*cm, 23.5*cm)
        c.line(42.7*cm, 0.2*cm, 42.7*cm, 23.5*cm)
        c.line(25.7*cm, 23.5*cm, 42.7*cm, 23.5*cm)

    c.showPage()
    print(f"Page generated for Cell {cell_num}")

c.save()
print(f"Report complete: {output_pdf}")
