# GanGBot

Discord Bot written using Python

Prerequisites:
- Python 3.8.2 and above
- Package management (Preferably Miniconda)
- Java 13 and above
- PostgreSQL 12 and above

Setup instructions:
- Setup and testing was done using AWS RDS and AWS EC2 and AWS S3
- Replace the environment variables in .env_dev and rename it to .env
- Create and get a Discord developer application token from https://discord.com/developers/applications
- Run the Lavalink server via the .jar file in the Lavalink folder

Features:
- Plays audio using Wavelink/Lavalink
- Creates playsound clips from Youtube videos and saves it per Discord guild basis
