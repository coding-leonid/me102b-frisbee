FROM python:3
# docker build -t frisbee_image .
# docker run --rm -v /dev:/dev --device-cgroup-rule='c *:* rmw' -v /tmp/.X11-unix:/tmp/.X11-unix:rw --env=DISPLAY frisbee_image

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD [ "python", "main.py" ]