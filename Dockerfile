FROM alpine:3.4
MAINTAINER "Adam Dodman <adam.dodman@gmx.com>"

RUN apk add --no-cache python3 git\
 && pip3 install --upgrade pip \
 && pip3 install ts3\
 && git clone https://github.com/Adam-Ant/ts3selfserve \
 && rm /ts3selfserve/README.md /ts3selfserve/Dockerfile \
 && apk del --no-cache git

VOLUME ["/config"]
WORKDIR /ts3selfserve
CMD ["python3","/ts3selfserve/main.py","-c","/config"]
