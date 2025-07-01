<p align="center">
  <img src="Image/UR_icon16.PNG" alt="Logo" width="200" />
  <h2>Utility Review <span style="font-size: 0.75em; font-weight: normal;">(preview 3)</span></h2>
</p>

<header>edited on July 1, 2025</header>


```plaintext
Project Structure (July 1, 2025)

UR_Preview_3/
├── UR_data/
│   └── ShapeFiles/              # Stores input shapefiles (not tracked by Git, from Teams)
├── github_code/
│   ├── code/
│   │   ├── .venv/               # Virtual environment (ignored by Git)
│   │   ├── main.py              # Main entry point for the script
│   │   ├── parsers/             # Parsing utilities for GML and TXT
│   │   │   ├── gml_parser.py
│   │   │   ├── txt_parser.py
│   │   │   └── __init__.py
│   │   ├── processing/          # Processing logic (clipping, mapping, email)
│   │   │   ├── clipping.py
│   │   │   ├── mapping.py
│   │   │   ├── emailer.py
│   │   │   ├── screenshot.py
│   │   │   └── __init__.py
│   │   ├── setup/               # Config, launchers, and setup tools
│   │   │   ├── changeme.txt           # Active config file (created from template)
│   │   │   ├── changeme-template.txt # Template config (reference)
│   │   │   ├── requirements.txt      # Python dependencies
│   │   │   ├── run_missdig.bat       # Batch script to run project
│   │   │   ├── run_missdig.lnk       # Windows shortcut (ignored by Git)
│   │   │   └── setup_env.bat         # Batch script to set up the environment
│   │   ├── utils/               # Utility functions
│   │   │   ├── changeme.py      # Logic for loading and parsing changeme.txt
│   │   │   └── __init__.py
├── GIS_Tools/ChromeExtension/   # (Extension for Salesforce Scraping)
├── Results/                     # Output results (ignored by Git, created by Scripts if not exist)
├── Image/                       # Images folder
├── .gitignore                   # Git ignore rules
└── README.md                    # Project overview and instructions
```


Initial Setup - Script

1. Run setup_env.bat (UR_Preview_3\github_code\code\setup\setup_env.bat), this will set up the venv for the script
2. Create a shortcut (.lnk) for run_missdig.bat (in the same folder as step 1)

    a. Right click on the blank space inside the folder  
    b. New --> Shortcut  
    c. Enter: cmd /c 
    d. Right Click on run_missdig.bat  
    e. Copy as Path, and paste it after cmd /c  
    d. Give it a name  
    f. Open the properties of the new shortcut  
    g. Copy the address from the folder address bar  
    h. Paste it into Start in  
    i. (optionally) Change the icon in Change Icon, remove the address, hit Enter, select an icon you like   
    j. Click "Apply"  
    k. Drag the shortcut into the task bar  
3. Open changeme_template.txt, and update the contact section of the file  
4. Save it (rename) as changeme.txt  
5. Go to Teams OneDrive --> GIS Specialist --> Document --> General --> Mike Stuff
6. Download UR_data folder, and drag it into UR_preview_3 folder

Initial Setup - Salesforce Scraping

1. Open Google Chrome
2. Open Setting
3. Open Extension from the left side bar
4. Toggle on Developer mode
5. Click Load Unpacked, find this folder github_code\GIS_Tools
6. Click Select Folder, and the UR Extractor is loaded now
7. Click Details
8. Toggle on Pin to toolbar


Congrats, the script is all set up now!