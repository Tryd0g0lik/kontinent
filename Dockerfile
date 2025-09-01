FROM python:latest
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir /www && \
    mkdir /www/src
WORKDIR /www/src
COPY ./requirements.txt .
RUN pip config set global.trusted-host "pypi.org files.pythonhosted.org"
RUN python -m pip install --upgrade "pip>=25.0"
# --no-cache-dir
RUN pip install -r requirements.txt
COPY . .
