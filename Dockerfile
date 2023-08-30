FROM python:3.10-bullseye

RUN apt-get update && apt-get upgrade -y

WORKDIR /usr/app
#RUN python -m venv /usr/app/venv
#ENV PATH="/usr/app/venv/bin:$PATH"

RUN mkdir -p "/usr/local/share/pw-browsers"
ENV PLAYWRIGHT_BROWSERS_PATH="/usr/local/share/pw-browsers"

COPY requirements.txt .
#--no-cache-dir
RUN pip install -r requirements.txt &&\ 
  playwright install chromium

RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

RUN apt-get install -y ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils

COPY . .
EXPOSE 6101
CMD [ "python","main.py"]