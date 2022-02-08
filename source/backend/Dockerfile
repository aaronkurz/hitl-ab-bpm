FROM python:3.7-slim as app
WORKDIR /source
COPY . /source/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV INSIDE_DOCKER True
EXPOSE 5001
CMD ["python", "app.py"] 

FROM python:3.7-slim as celery
WORKDIR /source
COPY . /source/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV INSIDE_DOCKER True

CMD celery -A task_scheduler.celery_app.celery worker -B -l info 