SIEM API Service
This project is a lightweight API service designed to automate and manage Fail2ban activities. It provides a programmatic interface to monitor blocked IP addresses, store them in a database, and perform unban operations directly through the API
.
Features
Log Parsing: Automatically scans /var/log/fail2ban.log to extract banned IP addresses using regular expressions
.
Persistent Storage: New bans are automatically saved to a database using SQLAlchemy (via the Ban model)
.
Manual Unban: Provides a function to remove an IP from the sshd jail using the system's fail2ban-client
.
Dockerized: Built to be deployed as a containerized service
.
Tech Stack
Language: Python
Framework: FastAPI
Database: SQLAlchemy
Security Tools: Fail2ban
Deployment: Docker
Current Status & Challenges 🚧
The project is currently in active development. A significant issue being addressed is the data synchronization mismatch:
When the unban_ip function is called, the IP is successfully removed from the Fail2ban system, but the record remains in the local database
.
This results in the API reporting an IP as "banned" even after it has been cleared from the system.
TODO
[ ] Status Synchronization: Implement a mechanism to update or remove records from the database immediately after a successful unban_ip operation to ensure data consistency
.
Requirements
Fail2ban installed on the host system.
Read access to /var/log/fail2ban.log for the application user
.
Permissions to execute fail2ban-client commands
.
