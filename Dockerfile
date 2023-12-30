FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
WORKDIR /app

RUN apt update 

ARG MONGODB_HOST
ENV MONGODB_PORT=27017
ENV MONGODB_DATABASE="mydatabase"
ENV MONGODB_COLLECTION="mycollection"


COPY ./app/ /app/
COPY ./requirements.txt /app/
RUN pip install -r /app/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]



