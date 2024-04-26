I've discovered a collection of Finnish forest survey data, including LiDAR and aerial photos, available in the public domain. 
https://asiointi.maanmittauslaitos.fi/karttapaikka/tiedostopalvelu
However, these files aren't directly accessible; instead, I receive an email with a unique link that leads to the files. 
To streamline this process, I decided to automate the downloads. This task was educational, teaching me how to set up work from emails 
in the Gmail box and delving into OAuth2 authentication.
The access setup is done through the Google Cloud Console, and while there's plenty of guidance online, I've also prepared a quick guide 
for those who prefer a speedrun. Remember, the first time you run the code, you'll need to confirm the application's access to your Gmail box.

One challenge was that the download links weren't embedded in the HTML of the page; they were dynamically generated. 
This led me to consider using browser automation tools like Selenium or Playwright. However, I found a more efficient solution:
a hiddent API endpoint that allows me to extract the download link directly, bypassing the need for browser automation.

After analyzing the data structure, I added functionality to scrap and download metadata. Since the files are from a specific site, 
the structure was hardcoded into the Python script. Essentially, the script connects to Gmail, searches for unread emails from the recipient, 
clicks on the links, and downloads the files. 

What I have learnt:
Working with APIs: This project provides hands-on experience with interacting with real-world APIs, including authentication, 
data retrieval, and parsing responses.
Handling Diverse Data Formats: By dealing with HTML emails and JSON responses, I gain experience in extracting information from various 
data formats commonly encountered in data engineering tasks.
Automating Data Pipelines: Building this automation script strengthens my ability to design and implement data pipelines that efficiently 
extract, transform, and load data.
Error Handling and Resilience: Implementing error handling mechanisms ensures the script's robustness and prepares me for building 
reliable data pipelines in real-world scenarios.

It's not perfect, but I have other things to do =) So, potential enhancements:
Logging: Incorporating a logging mechanism would allow me to track the script's execution, record errors, and facilitate debugging.
Configuration: Moving sensitive information like API keys and email addresses to a configuration file would improve security and make
the script more adaptable.
Scheduling: Integrating with a scheduling tool like cron would enable automatic execution of the script at regular intervals. Or we can 
wrap it into DAG and use Apache Airflow.
Data Validation: Adding data validation steps would ensure the quality and integrity of the downloaded data.

This project is a practical example of automating data collection or exploring automation. 
Remember, every challenge is an opportunity to learn and grow.
