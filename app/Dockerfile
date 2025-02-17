FROM python:3.12-alpine

#COPY ./routes.py /app/
#COPY ./requirements.txt /app/
#COPY database/ /app/database
COPY . /app/

#WORKDIR /app/

RUN pip install -r /app/requirements.txt

CMD ["uvicorn", "app.routes:app", "--host", "0.0.0.0"]