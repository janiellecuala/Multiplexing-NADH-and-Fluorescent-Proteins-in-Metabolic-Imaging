// Assemble_ExScan_ch0_Stack.ijm
// Assembles ch0 (intensity) images across all excitation wavelengths
// for a single sample into one stack, ready for ROI-based analysis.
//
// Naming convention expected:
//   {sampleName}_LA00_ch0.tif  -> 680nm
//   {sampleName}_LA01_ch0.tif  -> 690nm
//   {sampleName}_LA02_ch0.tif  -> 700nm
//   ... etc.
//
// Output: single stack with slices labeled by wavelength (nm)
//         left open and ready for FijiROI_csvcreation.ijm
//
// @faldalf — pipeline step 1 of 2 (run before FijiROI_csvcreation.ijm)

// ── User inputs ──────────────────────────────────────────────────────────────
folderPath = getDirectory("Select folder containing raw .tif files");
sampleName = getString("Enter sample name exactly as in filename (e.g. avGFP-1)", "avGFP-1");

// ── Find all matching ch0 files for this sample ───────────────────────────────
fileList = getFileList(folderPath);

// Collect matching filenames into a string array (IJ macro workaround)
matchCount = 0;
for (i = 0; i < fileList.length; i++) {
    f = fileList[i];
    if (startsWith(f, sampleName + "_LA") && endsWith(f, "_ch0.tif")) {
        matchCount++;
    }
}

if (matchCount == 0) {
    exit("No ch0 files found for sample: " + sampleName + "\nCheck sample name and folder.");
}

print("=== Assemble ExScan ch0 Stack ===");
print("Sample: " + sampleName);
print("Folder: " + folderPath);
print("Found " + matchCount + " wavelength steps");

// ── Open and assemble stack ───────────────────────────────────────────────────
// Open files in sorted LA order
laIndex = 0;
openedCount = 0;

while (true) {
    // Format LA index as zero-padded two digits
    if (laIndex < 10) {
        laStr = "0" + laIndex;
    } else {
        laStr = "" + laIndex;
    }

    filename = sampleName + "_LA" + laStr + "_ch0.tif";
    fullPath = folderPath + filename;

    if (!File.exists(fullPath)) {
        // No more files for this sample
        break;
    }

    open(fullPath);
    openedCount++;

    // Rename the opened image to wavelength for clarity
    wavelength_nm = 680 + (laIndex * 10);
    rename("" + wavelength_nm + "nm");

    print("  Opened: " + filename + "  ->  " + wavelength_nm + "nm");
    laIndex++;
}

if (openedCount == 0) {
    exit("No files could be opened. Check folder path and sample name.");
}

print("Assembling " + openedCount + " images into stack...");

// ── Concatenate all open wavelength images into one stack ─────────────────────
run("Images to Stack", "name=" + sampleName + "_ch0_ExScan use");

// Verify stack
getDimensions(width, height, channels, slices, frames);
print("Stack created: " + slices + " slices (" + (680) + "–" + (680 + (slices-1)*10) + " nm)");
print("Dimensions: " + width + " x " + height + " pixels");

// ── Label slices with wavelength ──────────────────────────────────────────────
for (s = 1; s <= slices; s++) {
    setSlice(s);
    wl = 680 + ((s - 1) * 10);
    setMetadata("Label", "" + wl + "nm");
}

// ── Enhance display for easier ROI drawing ────────────────────────────────────
resetMinAndMax();
run("Enhance Contrast", "saturated=0.35");

print("");
print("=== DONE ===");
print("Stack '" + sampleName + "_ch0_ExScan' is ready.");
print("Next step: run FijiROI_csvcreation.ijm to draw ROIs and extract intensities.");
print("");
print("ROI naming guide:");
print("  Transfected nuclei    ->  trans_nuc1, trans_nuc2, ...");
print("  Untransfected nuclei  ->  untrans_nuc1, untrans_nuc2, ...");
print("  Cytoplasm             ->  cyto1, cyto2, ...");

// Leave stack open for ROI drawing
selectWindow(sampleName + "_ch0_ExScan");
