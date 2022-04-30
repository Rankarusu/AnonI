FROM python:3.9.7

COPY app/ /app/

WORKDIR /app

RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]