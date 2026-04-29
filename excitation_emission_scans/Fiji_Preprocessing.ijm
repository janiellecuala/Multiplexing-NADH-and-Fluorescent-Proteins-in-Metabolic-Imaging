// Simple Direct Z-axis Data Extraction Macro
// This bypasses Plot Z-axis Profile and directly extracts slice data

// Get output directory for CSV files
outputDir = getDirectory("Choose output directory for CSV files");

// Get list of all open images
imageList = getList("image.titles");

if (imageList.length == 0) {
    showMessage("No images are currently open!");
    exit();
}

print("=== Direct Z-axis Data Extraction ===");
print("Found " + imageList.length + " open images");

// Process each open image
processedCount = 0;
for (i = 0; i < imageList.length; i++) {
    selectWindow(imageList[i]);
    
    // Check if it's a stack
    getDimensions(width, height, channels, slices, frames);
    
    if (slices > 1) {
        print("\n--- Processing: " + imageList[i] + " ---");
        print("Dimensions: " + width + "x" + height + ", " + slices + " slices");
        
        success = extractDataDirectly(imageList[i], outputDir);
        if (success) {
            processedCount++;
        }
    } else {
        print("Skipping " + imageList[i] + " (only " + slices + " slice)");
    }
}

print("\n=== COMPLETE ===");
print("Successfully processed " + processedCount + " stacks");
print("CSV files saved to: " + outputDir);

function extractDataDirectly(stackTitle, outputDir) {
    // Select the stack
    selectWindow(stackTitle);
    
    // Get stack info
    getDimensions(width, height, channels, slices, frames);
    
    // Use entire image as ROI
    run("Select All");
    
    // Initialize data arrays
    wavelengths = newArray(slices);
    intensities = newArray(slices);
    
    print("Extracting data from " + slices + " slices...");
    
    // Go through each slice and get mean intensity
    for (slice = 1; slice <= slices; slice++) {
        setSlice(slice);
        
        // Get statistics for this slice
        getStatistics(area, mean, min, max, std, histogram);
        
        // Calculate wavelength (400nm start, 10nm increment)
        wavelength = 400 + ((slice - 1) * 10);
        
        // Store data
        wavelengths[slice-1] = wavelength;
        intensities[slice-1] = mean;
        
        // Show progress every 5 slices
        if (slice % 5 == 0 || slice == slices) {
            print("  Slice " + slice + ": " + wavelength + "nm, intensity = " + mean);
        }
    }
    
    // Verify we have data
    if (intensities.length == 0) {
        print("ERROR: No data extracted!");
        return false;
    }
    
    print("Data extraction complete. Creating CSV...");
    
    // Find min and max intensity manually
    minIntensity = intensities[0];
    maxIntensity = intensities[0];
    for (k = 0; k < intensities.length; k++) {
        if (intensities[k] < minIntensity) minIntensity = intensities[k];
        if (intensities[k] > maxIntensity) maxIntensity = intensities[k];
    }
    
    // Create CSV content line by line to avoid concatenation issues
    csvLines = newArray(slices + 1);
    csvLines[0] = "Slice,Wavelength_nm,Intensity";
    
    for (j = 0; j < slices; j++) {
        sliceNumber = j + 1;
        wavelength = wavelengths[j];
        intensity = intensities[j];
        
        // Build line manually to avoid NaN issues
        line = "" + sliceNumber + "," + wavelength + "," + intensity;
        csvLines[j + 1] = line;
    }
    
    // Join all lines
    csvContent = "";
    for (j = 0; j < csvLines.length; j++) {
        csvContent += csvLines[j];
        if (j < csvLines.length - 1) csvContent += "\n";
    }
    
    // Create filename
    filename = replace(stackTitle, ".tif", "");
    filename = replace(filename, ".tiff", "");
    filename = replace(filename, " ", "_");
    filename = filename + "_zprofile.csv";
    
    csvPath = outputDir + File.separator + filename;
    
    // Save CSV
    File.saveString(csvContent, csvPath);
    
    // Verify file was created and has content
    if (File.exists(csvPath)) {
        fileSize = File.length(csvPath);
        print("SUCCESS: Created " + filename);
        print("  File size: " + fileSize + " bytes");
        print("  Data points: " + slices);
        print("  Wavelength range: " + wavelengths[0] + "-" + wavelengths[slices-1] + " nm");
        print("  Intensity range: " + minIntensity + "-" + maxIntensity);
        
        // Read back first few lines to verify
        savedContent = File.openAsString(csvPath);
        lines = split(savedContent, "\n");
        if (lines.length > 1) {
            print("  Sample data line 1: " + lines[1]);
        }
        if (lines.length > 2) {
            print("  Sample data line 2: " + lines[2]);
        }
        
        return true;
    } else {
        print("ERROR: Failed to create file " + filename);
        return false;
    }
}
