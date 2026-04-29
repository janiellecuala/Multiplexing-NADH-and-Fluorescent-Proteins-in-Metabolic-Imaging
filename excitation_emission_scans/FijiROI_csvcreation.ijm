 // This is gonna be a small macro to process/analyse excitation scan data from the SP8
// For now get the average intensity per image, extract values, plot, and safe to csv for further analysis in python
// The excitation stack needs to be open and selected!!!
// @faldalf 11/09/2021
// updated in 11/06/2024

// Please open image stack to analyse (z-dimension should be excitation wavelength) 
// You can either analyse using the ROI manager as with the lifetime script. 
// All excitation scan data per ROI are saved as separate csv files 
// 
// FS @faldalf updated 15/06/2024
// 
// Updated 16/06/2024: Save all ROI data to one result table and one csv file (should be cleaner). 
//
//
// Please drag and drop the image you want to analyse in FIJI and then run the script by hitting F5. Follow instructions. 

dir=getDirectory("Choose the directory to save the .csv results");
title=getTitle();

//Create ROIs by manual drawing. Click ok when all ROIs have been selected
run("ROI Manager...");
roiManager("reset");
setTool("freehand");
waitForUser("Please draw and add ROIs. \n You can use any drawing tool (polygon, rectangle ...). \n Click Add[t] and then rename ROI in ROI manager. \n Click OK here ONLY when done with all ROIs")

roiManager("show all with labels");
roicount=roiManager("count");

run("Clear Results");
for (i=0; i<roicount; i++) {
 	selectWindow(title);
 	roiManager("select", i); 
 	roi_name = Roi.getName ();
	row = 0; 
	print ("Analysing:");
	print (roi_name); // Allows to follow progess if large number of ROIs is used
 	run("Plot Z-axis Profile");
	Plot.getValues (xpoints, ypoints);
	for (j = 0; j < xpoints.length; j++) {
    	setResult ("Plane_ROI_"+roi_name, j, xpoints[j]);
    	setResult ("AverageValue_ROI_"+roi_name, j, ypoints[j]);
	}
	close ();
}
// Save results
saveAs("Results", dir+title+"_ExcScacn_all_ROIs.csv"); 
waitForUser ("Done. Click OK, then close everything or save ROI overlay.")
close ("Results");

