FROM ruby:3.3-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    BUNDLE_WITHOUT=development:test \
    BUNDLE_PATH=/usr/local/bundle

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
RUN bundle install --jobs 4 --retry 3 \
    && npm install --no-audit --no-fund \
    && npm cache clean --force

COPY . .

RUN useradd --create-home --uid 10001 publisher \
    && chown -R publisher:publisher /book

USER publisher

CMD ["make", "all"]
