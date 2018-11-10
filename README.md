# CheckNarc
Download patient prescription data from the [arkansas pmp database](https://arkansas.pmpaware.net) for all your patients

## Prerequisites
* PyQt5
* requests
* bs4

You can install them all via

`pip install -r requirements.txt`

## Download

Download the latest release [here](https://github.com/katzrkool/checkNarc/releases)

## Usage

Once you've installed the application, open it up and enter your Arkansas PMP login credentials into the boxes like in the image below

![Login Page](screenshots/login.png)

Hit the Submit Button and the application will prompt you to pick a CSV file to read patient information from.

![CSV Picker](screenshots/pickCSV.png)

Then it'll ask you for a folder to save your patient data in. Whatever folder you choose will be filled with numerous files, so it may be a good idea to create a new folder

![Folder Picker](screenshots/pickFolder.png)

If the account authenticated with at the beginning is a subaccount, a dialog will popup asking which supervisor you would like to query under. 

![Supervisor Picker](screenshots/pickSuper.png)

The data will begin to download and its progress can be tracked via the progress bar at the bottom of the screen. There is also a status update at the bottom of the screen which presents the current status of the application.

![Progress Bar](screenshots/progress.png)

Finally, once the application finishes downloading, you can navigate to the folder you chose to save in from earlier and find a CSV with information about each patient. Every patient in the system with history in the last year will have its own PDF file, with more details.