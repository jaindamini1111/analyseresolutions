AnalyseResolutions README.txt
=============================

I Foreword
-----------

	The code in this snapshot is in a poor shape: a thicket in need of tending, midway in much needed restructuring, and hopelessly un-optimised. (Apologies.)
	The code was nevertheless released _as it is_ in order to make it available for those interested.
	
	Please see https://ttoljamo.github.io/analyseresolutions/ for further information.
	
	Note: AnalyseResolutions has only been tested on several computers with Windows 7/64bit.
	
	
II Release Outline
------------------

	\README.txt											// This text file.
	\To_Do_List.txt	

	\src\												// The thicket of code:							
		\AnalyseResolutions.ipynb						// AnalyseResolutions Jupyter Notebook file; the main-loop of sorts.
		\ColumnLevel.py									// Several python files used by the ipynb.
		\DocumentImageAnalysis.py
		\DocumentImageUnderstanding.py
		\HelperFunctions.py
		\Levers.py
		\SpreadLevel.py
		\TextProcessing.py
		\XMLFactory.py	

		\bodyConfig.txt									// Tesseract 3.05 configuration files (included in OCR spells through command line parameters).
		\datelineConfig.txt
		\headConfig.txt

		\style.css										// A CSS stylesheet for the HTML testing pages that are generated during processing.
		
		\images\										// Three document images as examples; the images are from the National Archives of the Netherlands.
			   \NL-HaNA_1.01.02_3795_0058.jpg			
			   \NL-HaNA_1.01.02_3795_0059.jpg
			   \NL-HaNA_1.01.02_3795_0060.jpg
			   \image_licenses.txt
		 
		 \results\										// An empty folder where the results of processing will be stored.
		
	\rsc\		
		\tessdata\										// Tesseract 3.05 training files.
			     \custom_dateline_v1.traineddata		
				 \custom_head_v2_1740_2.traineddata
				 \custom_body_v2_1740_2.traineddata
				 \emop_body_v2_1740_2.traineddata
			
	\licenses\
			 \LICENSE_Ocropy.txt						// Ocropy license; the tool uses Sauvola binarisation borrowed from Breuel's Ocropy.
	\docs\
		   ...
		
		
III Getting Started
-------------------
	
	Please consider the steps below:
				
		(1) Acquire the AnalyseResolutions code release from GitHub (https://github.com/ttoljamo/analyseresolutions). 
	
		(2) Install Anaconda3 to get the needed Python essentials: e.g. JupyterNotebook and various libraries.
	
		(3) Install Tesseract v3.05 (e.g. UB Mannheim offers an installer at: https://github.com/UB-Mannheim/tesseract/wiki, tesseract-ocr-setup-3.05.00dev.exe).
		
		(4) Copy the training files from the release's tessdata folder to Tesseract v3.05's tessdata folder.
		
		(5) Edit Levers.py and change the path for style.css to reflect your system (the CSS is used with HTML testing pages for the generated output).
		
		(6) Open JupyterNotebook and execute the code in AnalyseResolutions.ipynb.
		
		If all goes well, the code begins to execute and you can see the processing results -- slowly -- appear in the results folder.
		(Note: Because the debug flag in Levers.py is set on by default, quite a few image splices are generated along the way to visualise the processing.)
		
		Although the code is a mess, the program is a processing pipeline and because of that it's not difficult to tweak bits here and there and 
		see what happens to that processing stage.
		
		
--
(8th December 2017)
