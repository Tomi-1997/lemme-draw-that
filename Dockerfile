FROM python:alpine

WORKDIR /prod/webapp
# Libraries - flask, socketio, gunicorn, eventlet
COPY ./requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -q -r /requirements.txt

# Source code
COPY ./app .

# Gunicorn script
COPY ./docker-entrypoint.sh .
RUN chmod +x ./docker-entrypoint.sh

# Run as non-root user
RUN adduser -D myuser
RUN chown -R myuser:myuser /prod/webapp
USER myuser

ENTRYPOINT ["sh", "docker-entrypoint.sh"]