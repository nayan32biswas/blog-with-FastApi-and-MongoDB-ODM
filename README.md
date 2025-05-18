# Blog project in FastAPI and MongoDB-ODM

This is a **Blog** API project using <a href="https://mongodb-odm.readthedocs.io" class="external-link" target="_blank">MongoDB-ODM</a> in <a href="https://fastapi.tiangolo.com" class="external-link" target="_blank">FastAPI</a>

## Start project

### First

Clone the repository and navigate to the project.

```bash
git clone https://github.com/nayan32biswas/blog-with-FastApi-and-MongoDB-ODM.git
cd blog-with-FastApi-and-MongoDB-ODM
```

### [Install UV](https://docs.astral.sh/uv/getting-started/installation/){.internal-link target=\_blank}

We are using uv to manage our python package.

So we need to install uv to start project.

### Install Dependency

Install all dependency.

```bash
uv sync
```

### Activate venv

```bash
source .venv/bin/activate
```

### Start Mongodb Server

#### [Install MongoDB](https://www.mongodb.com/docs/manual/installation/){.internal-link target=\_blank}

Install mongodb by following there official doc.

Start mongodb server.

### Export env key

```bash
export SECRET_KEY=your-secret-key
export MONGO_URL=<mongodb-connection-url>
export DEBUG=True
```

### Create Indexes

Before start backend server create indexes with:

```bash
uv run -m app.main create-indexes
```

### Run Server

Run backend server with `unicorn`.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Populate Database

## Run with Docker

Make sure you have docker installed and active.

- `docker compose build api` Build docker image.
- `docker compose run --rm api uv run -m app.main create-indexes` Create Indexes
- `docker compose up api` Run the server.

### Populate Database with Docker

- `docker compose run --rm api uv run --extra dev -m app.main populate-data --total-user 100 --total-post 100` Populate database with 100 user and 100 post with others necessary information
- `docker compose run --rm api uv run --extra dev -m app.main delete-data` Clean database if necessary.

## Visit API Documentation

Open your browser and visit [http://localhost:8000/docs](http://localhost:8000/docs)

You will find all the necessary API documentation there.

## Test

- Start Mongodb server
- Export env key
- `scripts/test.sh`

## Test with Docker

Run project unittest with single command:

```bash
docker compose run --rm api ./scripts/test.sh
```

## Contribute

Developers are welcome to improve this project by contributing.

If you found some bug or if you can improve code we welcome you to make change.

It's better to create an issue first. Or create a discussions.

### Before create PR

Before creating PR make sure you follow those steps:

- Write test on your change.
- `scripts/test.sh` Run unittest and make sure everything pass.
- `scripts/lint.sh` Run linting script.
- `scripts/format.sh` Run format test if any formatting required.

## Build and Run production server

### Database

#### Run The Database

For the first time run the database with container name **blog-database-container**

```sh
docker run -d --name blog-database-container -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=password mongo
```

#### Start Database If Existing

```sh
docker start blog-database-container
```

#### Get container IP

```bash
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' blog-database-container
```

### Run Server

#### Build and run server

```bash
docker build -t fastapi-blog-image -f Dockerfile.prod .

docker run -d --name fastapi-blog-container \
    -p 8000:8000 --env-file .env \
    fastapi-blog-image
```

#### Restart server

```bash
docker start fastapi-blog-container
```

## Populate Data

```bash
docker run --rm --env-file .env fastapi-blog-image uv run --extra dev -m app.main delete-data
docker run --rm --env-file .env fastapi-blog-image uv run --extra dev -m app.main populate-data --total-user 10000 --total-post 10000
```

## Load Test

### Configure Common Database

```bash
docker network create blog-database
```

#### Run Mongodb service

`mkdir ~/mongo_blog_data` Create volume directory

```bash
docker run -d --name blog_db --hostname db \
    --network blog-database -p 27017:27017 --expose 27017 \
    -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=password \
    -v ~/mongo_blog_data:/data/db \
    mongo:7
```

Additional command for the database container

The connection URL will be

- `mongodb://root:password@localhost:27017/blog_db?authSource=admin` for mongodb compass.
- `mongodb://root:password@db:27017/blog_db?authSource=admin` for application instance.

#### Populate database

```bash
docker build -t fastapi_blog:latest -f Dockerfile .

docker run --rm --network blog-database --env-file .env fastapi_blog:latest \
 uv run --extra dev -m app.main populate-data --total-user=100000 --total-post=100000
```

### Configure and Run Instance

Build the image:
`docker build -t fastapi_blog_prod:latest -f Dockerfile.prod .`

Run the newly create image with proper tagging

```bash
docker run -d --name fastapi_blog_api \
    --network blog-database -p 8000:8000 --env-file .env \
    fastapi_blog_prod:latest
```

#### Run application script

### Container related command

- `docker start <name>` stop the service if it's stopped.
- `docker stop <name>` Stop the service.
- `docker rm <name>` Remove the service.
