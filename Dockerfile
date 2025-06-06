FROM python:3.13

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  UV_REQUESTS_TIMEOUT=100

# Install uv
RUN curl -LsSf https://astral.sh/uv/0.6.10/install.sh | sh && \
  mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /code

COPY pyproject.toml uv.lock /code/
RUN uv sync --extra dev --frozen

ADD . /code
