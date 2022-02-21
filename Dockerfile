FROM python:3.6-alpine

# Add cssms user
RUN adduser -u 1001 -G root -D cssms

WORKDIR /home/cssms

# Copy over requirements and set up virtual environment
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

# Copy app files and make executable
COPY app app
COPY migrations migrations
COPY search search
COPY cssms.py config.py boot.sh ./
RUN chmod a+x boot.sh

# Update userale data-autostart parameter
ARG USERALE_AUTOSTART
RUN sed -i 's+data-autostart=false+data-autostart='$USERALE_AUTOSTART'+g' app/templates/base.html

# Set Flask App
ENV FLASK_APP cssms.py

# Change user ownership to cssms and change user
RUN chown -R 1001:1001 ./
USER cssms

# Launch web app
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
