FROM python:3

COPY . /

RUN mkdir /data
VOLUME /data

RUN pip install -r requirements.txt

EXPOSE 5123

ENTRYPOINT [ "python", "/app.py" ]
