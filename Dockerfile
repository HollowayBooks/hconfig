FROM python:3.6.5-alpine

RUN pip install pipenv
RUN apk add --update --no-cache alpine-sdk
COPY Pipfile Pipfile.lock /
RUN pipenv install --deploy --system

COPY hconfig.py /

WORKDIR /w
ENTRYPOINT [ "python", "/hconfig.py" ]
