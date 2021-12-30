FROM python:3.7-slim
WORKDIR /source
COPY . /source/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV INSIDE_DOCKER True
EXPOSE 5001
CMD ["python", "app.py"] 