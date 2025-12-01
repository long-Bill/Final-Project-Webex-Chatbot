# Final-Project-Webex-Chatbot
Group #3:
Kate Barrett
Bill Luong
Tuan Sally

Random Facts Webex Bot Project

Introduction
Our project implements a Python-based Webex chatbot that responds to chat commands with real-time data from an external API. Specifically, when a user types a command in a Webex space, our bot calls an API that returns a random fact into the Webex space.
In addition to the chatbot, we integrated a security/dependency check on the GitHub repository where the bot’s code and .env file are stored, and we created a Grafana dashboard to visualize repository metrics such as number of commits. Together, these components demonstrate a small but realistic DevOps workflow that combines automation, security, and observability.

Overview of the Workflow
1.	A Python script is running and listening to a Webex room called DailyUpdates.
2.	A user types the command “/fact” or “/facts” in the DailyUpdates room.
3.	The Python script reads the message in the DailyUpdates room, parses the command, and makes an HTTP request to an external API that returns a random fact.
4.	The script formats the response and posts a message back into the Webex room with the random fact. If there is an error with the API, an error message will be posted in the Webex room.
5.	The code for this bot is version-controlled in a GitHub repository.
6.	A security/dependency checker runs against the repo to detect vulnerable Python packages.
7.	An API Health Check is run every 12 hours to ensure the API is still available.
8.	Commit activity from the repo is visualized on a Grafana dashboard, showing metrics such as commit counts over time.

Technologies Used
•	Python
  o	 Used to implement the Webex chatbot logic, handle HTTP requests to the external “random fact” API, and format responses.
•	Webex (Messaging Platform + Bot)
  o	Hosts the chat space where users interact with the bot. When users send messages, Webex sends events to our Python webhook endpoint, which triggers the bot logic.
•	External “random facts” API
  o	Returns a random fact. Our Python script calls this API whenever a specific command is received and uses the returned data in the response message.
•	GitHub
  o	Stores the Python source code and the .env file (with sensitive values excluded from version control or shown as placeholders). Commits to this repository drive both our security checks and the metrics shown in Grafana.
•	Security / Dependency Check Tool
  o	CodeQL: a vulnerability scan that reviews the repo’s contents to identify potential vulnerabilities
  o	Dependency Review: reviews any changes to repository’s requirements.txt file to identify outdated packages, helping ensure the bot is built on secure libraries.
•	Grafana
  o	Used to visualize metrics such as number of commits to the repository over time. Grafana reads data from a metrics source (e.g., GitHub statistics exported or a time series DB) and presents charts that help us monitor development activity.
•	Docker and Docker-compose
  o	A docker-compose yaml file is used to deploy a Grafana container with an exposed port of 3000, environment variable, and persistent storage. Docker-compose enables flexibility for additional container services to the Grafana stack.
These technologies are chained together in a simple pipeline: GitHub manages the code; a security checker identifies any vulnerabilities in the code; a dependency check validates dependencies; Webex events trigger our Python bot; the bot calls an external API and responds in chat; an API health check reaches out to the API regularly to make sure it is up; and Grafana presents metrics about repository activity. This combination shows automation, security, and observability in a single small project.

Setup Instructions
1.	Prerequisites
•	Accounts
  o	Webex account with permission to create a bot, plus your current personal access token to use for authentication.
  o	GitHub account with access to the repository.
•	Installed Software
  o	Python version 3.x
  o	pip (Python package manager)
  o	Git
•	Access
  o	Internet access (to reach Webex API and the “Random Facts” API).
  o	Access to your Grafana instance.
2.	Getting the Code
  a.	Clone the repository:
    i.	git clone https://github.com/long-Bill/Final-Project-Webex-Chatbot.git
  b.	Find the Python script:
    i.	random_facts_chatbot.py
3.	Environmental Variables / .env file
  a.	This file is pre-built but it includes all the variables that will be needed except your personal access token:
    i.	WEBEX_BOT_TOKEN that identifies the bot that was created for this activity
    ii.	WEBEX_BOT_EMAIL
    iii.	WEBEX_ROOM_ID that identifies the specific room that the chat bot is monitoring

How to Run the Bot
1.	Create and activate a virtual environment.
2.	Start the bot:
a.	python3 ./random_facts_chatbot.py
b.	The script starts a simple web server that listens for incoming Webex message events on the configured endpoint.
3.	In the Webex room where the bot is added, type the command “/fact” or “/facts” to call the external API and reply with a random fact.
4.	When the command is received, the bot:
a.	Validates the command.
b.	Calls the external API.
c.	Parses the JSON response to prettify the response.
d.	Posts a formatted message back into the Webex room.

Interacting with the Bot in Webex
There are only two commands available to users in the Webex room: “/facts” and “/fact”. Both commands will return with a random fact. If the API is unavailable, the program will return a message stating that it couldn’t retrieve a fact at that time.

Security / Dependency Check
This project uses CodeQL as a vulnerability check, implemented through Github Actions. CodeQL is a static analysis engine developed by GitHub that treats code like data. It works by first processing a codebase to create a database of facts, and then running queries written in the QL language against that database to find vulnerabilities, bugs, and other quality issues. 
Additionally, this project contains a Dependency Review workflow in Github to review the requirements.txt file. The review makes sure that the correct software versions are being used and identifies any potential compatibility issues.
Lastly, the project uses an API Health Check workflow in Github to make sure the API is still active. The check runs every 12 hours and returns a pass or fail response.

Grafana Metrics Overview
Grafana is an open-source, data visualization tool. Grafana offers plugins to gather data from certain applications like GitHub, AWS, Prometheus, Jenkins, and more. In this project, only the GitHub plugin was utilized to gather data from the GitHub repository. In Grafana, users can create dashboards and visualizations to view specific metrics of a GitHub repository. Several metrics include commits, pull requests, contributors, GitHub Action Workflows, and more.  
Grafana Metrics
In this project, there are 6 dashboards: Total Commits Per Day, Total Commits by Contributor, (CodeQL) Duration of Workflow Runs, (API Health Check) Duration of Workflow Runs, (CodeQL) Workflow Success and Failure, and (API Health Check) Workflow Success and Failure.
Total Commits Per Day
 
This visualization shows the total amount of commits in each day. For example, November 29th showed a total of 6 commits while November 23rd showed a total of 1 commit.
Total Commits by Contributor
 
This visualization shows the total amount of commits by each contributor. GitHub gathers all the commits made in the repository and the dashboard gets the sum of commits by each user. 
 
(CodeQL) Duration of Workflow Runs
 
This visualization shows each GitHub action run in the CodeQL workflow. The x-axis shows the workflow run number and each workflow run will show the duration of the workflow run.
(API Health Check) Duration of Workflow Runs
 
This visualization shows each GitHub action run in the API Health Check workflow. The x-axis shows the workflow run number and each workflow run will show the duration of the workflow run.
 

(CodeQL) Workflow Success and Failure
 
This visualization shows a pie chart of how many GitHub workflow runs were successful and unsuccessful in the CodeQL workflow.
(API Health Check) Workflow Success and Failure
 
This visualization shows a pie chart of how many GitHub workflow runs were successful and unsuccessful in the API Health Check workflow.
Setup Grafana
1.	Prerequisites
a.	A Linux Virtual Machine (set up steps below utilizes a RHEL-based Virtual Machine)
2.	Install Docker engine and Docker Compose.
a.	Add Docker repository to dnf. 
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
b.	Install required Docker packages. 
sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
c.	Start and enable the Docker engine. 
sudo systemctl --now enable docker
d.	Add the main user to the Docker group (ability to utilize Docker engine without sudo) 
sudo usermod -a -G docker $(whoami)
3.	Create a separate Docker network.
docker network create <name_of_new_network>
4.	Create a Docker compose file for Grafana. 
nano ~/docker-compose.yml
5.	In the docker-compose.yml file, input the following content. Then save and exit:
services:
  grafana:
    image: grafana/grafana:main
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=<desired_password>
    volumes:
      - grafana-storage:/var/lib/grafana
    networks:
      - <created_network>
    restart: unless-stopped
volumes:
  grafana-storage:
networks:
  project:
    external: true
6.	Create a Docker container with Docker Compose:
docker compose up -d
7.	To visit Grafana on the virtual machine, visit http://localhost:3000
 
8.	Log in to Grafana.
a.	Username: admin
b.	Password: <password set in docker-compose.yml>
9.	Install GitHub Plugin in Grafana.
a.	On the left panel, click on Administration > Plugins and Data > Plugins
10.	In the plugin search bar, search for GitHub and click install.
11.	After installing the plugin, select Connections > Data Sources in the left panel.
12.	Select “Add new data source” (top right) and select GitHub. 
a.	Scroll down in the Settings tab and enter your GitHub Personal Access Token.
b.	Click “Save & Test”




