# J4J_Tunnel

FROM ubuntu:18.04

EXPOSE 9004

RUN apt update && apt install -y ssh=1:7.6p1-4ubuntu0.3 && apt install -y python3=3.6.7-1~18.04 && apt install -y python3-pip=9.0.1-2.3~ubuntu1.18.04.1 && apt install -y net-tools=1.60+git20161116.90da8a0-1ubuntu1 && apt install -y inotify-tools=3.14-2 && DEBIAN_FRONTEND=noninteractive apt install -y tzdata=2019c-0ubuntu0.18.04 && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

RUN pip3 install flask-restful==0.3.7 uwsgi==2.0.17.1 psycopg2-binary==2.8.2

RUN mkdir -p /etc/j4j/J4J_Tunnel

RUN adduser --disabled-password --gecos '' tunnel

RUN chown tunnel:tunnel /etc/j4j/J4J_Tunnel

COPY --chown=tunnel:tunnel ./app /etc/j4j/J4J_Tunnel/app

COPY --chown=tunnel:tunnel ./app.py /etc/j4j/J4J_Tunnel/app.py

COPY --chown=tunnel:tunnel ./scripts /etc/j4j/J4J_Tunnel

COPY --chown=tunnel:tunnel ./uwsgi.ini /etc/j4j/J4J_Tunnel/uwsgi.ini

RUN mkdir -p /home/tunnel/.ssh_socket

RUN mkdir -p /home/tunnel/.ssh

RUN chmod 700 /home/tunnel/.ssh

RUN chown tunnel /home/tunnel/.ssh

RUN chown tunnel /home/tunnel/.ssh_socket

WORKDIR /etc/j4j/J4J_Tunnel

CMD /etc/j4j/J4J_Tunnel/start.sh
