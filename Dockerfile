FROM python:3.8-buster

# Add cssms user
# RUN adduser -u 1001 -G root -D cssms

WORKDIR /home/cssms

# Copy over requirements and set up virtual environment
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

# Copy app files and make executable
COPY app app
COPY migrations migrations
COPY srdp.py config.py boot.sh ./
RUN chmod a+x boot.sh

# Set Flask App
ENV FLASK_APP srdp.py

# Launch web app
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
