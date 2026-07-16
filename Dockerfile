FROM ruby:3.3-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       chromium \
       curl \
       fonts-dejavu-core \
       fonts-liberation \
       git \
       make \
       python3 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /book

COPY Gemfile package.json ./
RUN bundle install \
    && npm install

COPY . .

CMD ["make", "all"]
