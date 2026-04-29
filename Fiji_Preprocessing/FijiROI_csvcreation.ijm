// FijiROI_csvcreation.ijm
// Extracts mean intensity per ROI across excitation wavelengths from an SP8 stack.
// Outputs one clean CSV with a Wavelength column (680nm steps) and one column
// per ROI — ready to input directly into exScan_fluor.py.
//
// Run AFTER Assemble_ExScan_ch0_Stack.ijm
// Stack must be open and selected before running.
//
// ROI naming guide:
//   Transfected nuclei    ->  trans_nuc1, trans_nuc2, ...
//   Untransfected nuclei  ->  untrans_nuc1, untrans_nuc2, ...
//   Cytoplasm             ->  cyto1, cyto2, ...
//
// @faldalf 11/09/2021
// updated 11/06/2024, 16/06/2024
// updated 2024: clean CSV output, correct wavelength axis, fixed filename typo

dir = getDirectory("Choose the directory to save the .csv results");
title = getTitle();

// Get number of slices to build wavelength array
getDimensions(width, height, channels, slices, frames);
print("=== ExScan ROI CSV Creation ===");
print("Stack: " + title);
print("Slices: " + slices + "  (" + 680 + "–" + (680 + (slices-1)*10) + " nm)");

// Create ROIs by manual drawing
run("ROI Manager...");
roiManager("reset");
setTool("freehand");
waitForUser("Please draw and add ROIs.\n \nYou can use any drawing tool (polygon, rectangle, freehand).\nClick Add[t] after each ROI and rename it in the ROI Manager.\n \nROI naming:\n  trans_nuc1, trans_nuc2 ...\n  untrans_nuc1, untrans_nuc2 ...\n  cyto1, cyto2 ...\n \nClick OK here ONLY when all ROIs are done.");

roiManager("show all with labels");
roicount = roiManager("count");

if (roicount == 0) {
    exit("No ROIs found! Please draw and add ROIs before clicking OK.");
}

print("ROIs found: " + roicount);

// ── Build results table ───────────────────────────────────────────────────────
// First column: Wavelength (nm)
// One column per ROI: mean intensity values

run("Clear Results");

// Set wavelength column
for (j = 0; j < slices; j++) {
    wavelength = 680 + (j * 10);
    setResult("Wavelength_nm", j, wavelength);
}

// Extract mean intensity per ROI per slice
for (i = 0; i < roicount; i++) {
    selectWindow(title);
    roiManager("select", i);
    roi_name = Roi.getName();

    print("Analysing: " + roi_name);

    run("Plot Z-axis Profile");
    Plot.getValues(xpoints, ypoints);
    close(); // close the plot window

    // Write intensity values — column named after ROI directly
    for (j = 0; j < ypoints.length; j++) {
        setResult("Mean(" + roi_name + ")", j, ypoints[j]);
    }
}

// ── Save CSV ──────────────────────────────────────────────────────────────────
// Clean filename: strip extension from stack title, fix typo
cleanTitle = replace(title, ".tif", "");
cleanTitle = replace(title, ".tiff", "");
outputPath = dir + cleanTitle + "_ExcScan_all_ROIs.csv";

saveAs("Results", outputPath);
print("CSV saved: " + outputPath);

waitForUser("Done!\n \nCSV saved to:\n" + outputPath + "\n \nClick OK, then close everything or save the ROI overlay.");
close("Results");
