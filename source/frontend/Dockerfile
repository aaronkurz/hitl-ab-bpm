FROM python:3.7-slim
WORKDIR /source
COPY . /source/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV INSIDE_DOCKER True
CMD streamlit run sl-ui.py